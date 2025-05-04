import re
from datetime import datetime
from uuid import uuid4
import sys
import subprocess

from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

subprocess.run([sys.executable, "-m", "pip", "install", "youtube_transcript_api"])
subprocess.run([sys.executable, "-m", "pip", "install", "google-api-python-client"])

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from openai import OpenAI

# ASI-1 client initialization
asi_client = OpenAI(
    base_url="https://api.asi1.ai/v1",
    api_key="sk_47dbfae6905943759c8f952266ca2d78120fddfd56d34eb893582d87c4836df1",
)

# Message models
class YouTubeRequest(Model):
    query: str

class YouTubeResponse(Model):
    response: str

# Constants
AGENT_SEED = "youtube_agent_seed"

# Agent
youtube_agent = Agent(name="YouTubeAgent", port=8000, seed=AGENT_SEED, endpoint=["http://127.0.0.1:8000/submit"])

# Chat protocol
chat_proto = Protocol(name="chat", spec=chat_protocol_spec)

@youtube_agent.on_event("startup")
async def start(ctx: Context):
    ctx.storage.set("authenticated", False)

@chat_proto.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    user_input = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            user_input += item.text.strip()

    authenticated = ctx.storage.get("authenticated") or False

    if not authenticated:
        if "fetch" in user_input.lower():
            ctx.storage.set("authenticated", True)
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="Password accepted. How can I help you?")]
            ))
        else:
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="Please provide the password to proceed.")]
            ))
        return

    # Check for insights request
    if any(word in user_input.lower() for word in ["insight", "analyze", "summarize"]):
        # Get the last stored video data
        keys = ctx.storage._store.keys()
        recent_key = next((k for k in reversed(list(keys)) if k != "authenticated"), None)
        if not recent_key:
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="No video data available to analyze.")]
            ))
            return

        video_data = ctx.storage.get(recent_key)
        
        try:
            response = asi_client.chat.completions.create(
                model="ASI-MINI",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant who gives YouTube video insights."},
                    {"role": "user", "content": f"Please provide insights and summary for this YouTube video data:\n\n{video_data}"}
                ],
                temperature=0.7,
            )

            insight_text = response.choices[0].message.content.strip()

            await ctx.send(sender, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"Insights:\n{insight_text}")]
            ))

        except Exception as e:
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"Error while analyzing video: {str(e)}")]
            ))
        return

    # Extract API key and video ID from user_input using regex
    try:
        api_key_match = re.search(r'API_KEY\s*=\s*([A-Za-z0-9_\-]+)', user_input)
        video_url_match = re.search(r'(?:v=|youtu\.be/)([\w\-]{11})', user_input)

        if not api_key_match or not video_url_match:
            raise ValueError("Could not find both a valid API key and video ID in your message.")

        api_key = api_key_match.group(1)
        video_id = video_url_match.group(1)

        # Check if already in storage
        cached_data = ctx.storage.get(video_id)
        if cached_data:
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=cached_data)]
            ))
            return

        # Initialize YouTube Data API client
        youtube = build("youtube", "v3", developerKey=api_key)

        # Get Video Details
        video_response = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()

        items = video_response.get("items", [])
        if not items:
            response_text = "Video not found or is private."
        else:
            video = items[0]
            snippet = video["snippet"]
            stats = video["statistics"]

            title = snippet["title"]
            channel_title = snippet["channelTitle"]
            upload_date = snippet["publishedAt"]
            views = stats.get("viewCount", "N/A")
            likes = stats.get("likeCount", "N/A")
            comments_count = stats.get("commentCount", "N/A")

            response_text = f"Video Info:\nTitle: {title}\nChannel: {channel_title}\nUpload Date: {upload_date}\nTotal Views: {views}\nLikes: {likes}\nComments: {comments_count}\n"

            # Fetch comments
            try:
                comment_response = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=5,
                    textFormat="plainText"
                ).execute()

                comments = comment_response.get("items", [])
                if comments:
                    response_text += "\nTop Comments:\n"
                    for item in comments:
                        comment = item["snippet"]["topLevelComment"]["snippet"]
                        author = comment["authorDisplayName"]
                        text = comment["textDisplay"]
                        likes = comment["likeCount"]
                        response_text += f"@{author} ({likes} likes): {text}\n"
                else:
                    response_text += "\nNo comments found.\n"

            except Exception as e:
                response_text += f"\nCould not retrieve comments: {e}\n"

            # Get Transcript
            response_text += "\nTranscript:\n"
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                for entry in transcript[:10]:  # Limit to first 10 lines
                    response_text += f"{entry['start']:.1f}s: {entry['text']}\n"
            except TranscriptsDisabled:
                response_text += "Transcripts are disabled for this video.\n"
            except NoTranscriptFound:
                response_text += "No transcript found (video may be private or not have captions).\n"
            except Exception as e:
                response_text += f"Could not retrieve transcript: {e}\n"

        ctx.storage.set(video_id, response_text)

        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)]
        ))

    except Exception as e:
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"Could not extract info: {e}")]
        ))
        return

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.storage.set("authenticated", False)

youtube_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    youtube_agent.run()
