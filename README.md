# LangSmith Webhook Judge Service

Automated evaluation system that receives LangSmith webhook notifications, evaluates runs with an LLM judge, and posts feedback back to LangSmith.

## Overview

This project sets up:
1. **LangSmith Tracing Project** - Initializes a project for tracing
2. **Render Webhook Service** - Deploys a FastAPI service that receives webhooks
3. **LangSmith Webhooks** - Configures webhook rules to trigger on runs
4. **Sample Traces** - Sends test traces to trigger evaluators

## Architecture

- **`main.py`** - Main orchestration script that sets up everything
- **`config.py`** - Configuration and environment variable management
- **`services/server.py`** - FastAPI webhook receiver with LLM judge evaluation
- **`services/langsmith.py`** - LangSmith webhook configuration
- **`services/render.py`** - Render.com deployment (untested, requires paid plan)
- **`services/traces.py`** - Sample traces for testing

## Prerequisites

1. **Python 3.9+** with virtual environment
2. **LangSmith Account** with API key
3. **OpenAI API Key** for the judge LLM
4. **Render.com Account** (for deployment)
5. **Git Repository** (for Render auto-deploy)

## Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd spotify

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root following the `.env.example` file

### 3. Get Your Render Owner ID

Your Render Owner ID can be found **via Render Dashboard**: Look at your dashboard URL - it contains your owner ID

### 4. Run the Setup Script

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Run the main setup script
python main.py
```

This will:
1. ✅ Validate all environment variables
2. ✅ Set up LangSmith tracing project and send initial trace
3. ⚠️ Attempt to deploy service to Render (see note below)
4. ✅ Configure webhooks in LangSmith
5. ✅ Send sample traces to trigger evaluators

## Important Notes

### Render Deployment (`services/render.py`)

⚠️ **WARNING**: The Render deployment script (`services/render.py`) is has the following limitations:

1. **Requires Paid Plan**: Free tier services **cannot be created via the Render API**. You must:
   - Create the service manually in the Render dashboard first, OR
   - Use a paid plan (Starter or higher)

2. **Untested**: The script has not been fully tested end-to-end. If you encounter issues:
   - Create the service manually in Render dashboard
   - The script will detect existing services and update their environment variables

3. **Manual Alternative**: To set up manually:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Create a new Web Service
   - Connect your Git repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn services.server:app --host 0.0.0.0 --port $PORT`
   - Configure environment variables (see below)
   - Get your service URL and use it in `services/langsmith.py`

### Environment Variables for Render Service

When deploying (manually or via script), set these environment variables in Render:

- `LANGSMITH_API_KEY` - Your LangSmith API key
- `OPENAI_API_KEY` - Your OpenAI API key
- `JUDGE_MODEL` - Optional, defaults to `openai:gpt-4o-mini`
- `LANGSMITH_PROJECT` - Optional, your LangSmith project name
