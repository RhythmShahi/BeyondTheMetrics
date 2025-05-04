# BeyondTheMetrics

A Fetch.ai AgentVerse application using a uAgent to automate the extraction of insights from YouTube video data and provide intelligent responses based on user queries.

## Overview

This system is built around an autonomous agent:

- **YouTubeInsightsAgent**: Acts as the AI agent that processes YouTube video data, extracting useful insights such as transcript, comments, likes, etc. Which can then be used insights.

The agent communicate via uAgents and leverage **ASI-1 MINI (ASI-MINI)**, a powerful AI model, to intelligently analyze the video data and handle natural language queries.

## Core Functionality

### 1. Video Data Extraction (`YouTubeInsightsAgent.py`)
- Takes a YouTube URL and API key as input.
- Fetches metadata, transcript, comments, and other relevant data from the video.
- Processes the extracted data for easy querying.

### 2. Authentication & Security
- The user agent requires authentication (e.g., an API key) to start the session before processing queries.

## How to Use

### Prerequisites

- Python 3.9+
- uAgents
- `openai` Python client (used for ASI-1)
- YouTube API Key

### ASI-1 API Key

Replace the placeholder in `YouTubeInsightsAgent.py` with your actual ASI-1 API key:

```python
client = OpenAI(
    base_url='https://api.asi1.ai/v1',
    api_key='your_asi1_api_key_here'
)
```

## Chatting with the AI Agent

Once running, you can initiate a session and send queries using the chat protocol:

- Then send natural language queries like:
  - "Summarize the transcript"
  - "What are the most liked comments on this video?"

The system responds with insights based on the video data and can continue the conversation to dig deeper.

## File Structure

```bash
.
├── README.md              # Project documentation
└── agents/
    ├── YouTubeInsightsAgent.py    # AI agent handling video data extraction
```

##Creator Economy Track: User Journey and Engagement Metrics

In the creator economy, understanding audience engagement and content insights is key for creators and brands to maximize their reach and impact. This system enhances user engagement by allowing them to interact with video data in a meaningful way, asking targeted questions and receiving actionable insights.

### Key Features:

- Video data extraction: Automatically collects and processes key video insights.
- Real-time engagement: Allows users to query video data in natural language.
- Enhanced audience interaction: Provides content creators with valuable metrics based on user interaction with video data.

### Target Users:

- Content creators
- Social media managers
- Digital marketing professionals

### Benefits:

- Deeper insights into viewer engagement
- Streamlined data collection for content optimization
- Intelligent, real-time interaction with video content

## Powered By

- Fetch.ai AgentVerse
- uAgents framework
- ASI-1 MINI LLM

## License

This project is licensed under the MIT License.
