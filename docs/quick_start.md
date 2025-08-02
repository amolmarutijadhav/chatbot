# Quick Start Guide

Get your Intelligent MCP Chatbot running with real LLM functionality in minutes!

## Prerequisites

- Python 3.8+
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Step 1: Setup Environment

1. **Activate virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

2. **Set up API key:**
   ```bash
   python scripts/setup_env.py
   ```
   
   This will create a `.env` file with your API key.

## Step 2: Test Configuration

Run the LLM test to verify everything is working:

```bash
python scripts/test_llm_config.py
```

You should see success messages and a test response from the LLM.

## Step 3: Run the Chatbot

### Option A: Demo Mode (Recommended for first run)
```bash
python src/main.py demo
```

This runs a pre-defined conversation to test all functionality.

### Option B: Interactive Mode
```bash
python src/main.py interactive
```

This lets you chat with the bot directly in the terminal.

### Option C: API Server
```bash
python src/api_main.py
```

This starts the web API server on http://localhost:8000

## Step 4: Test the Web Interface

1. Start the API server: `python src/api_main.py`
2. In another terminal, start the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```
3. Open http://localhost:3000 in your browser

## What's Working Now

✅ **Real LLM Integration**: Your chatbot now uses OpenAI's GPT models  
✅ **Web Interface**: Modern React frontend with real-time chat  
✅ **API Server**: RESTful API with WebSocket support  
✅ **Configuration Management**: Easy setup and customization  
✅ **Logging & Monitoring**: Debug information and metrics  

## Next Steps

1. **Configure MCP Servers**: Add real MCP servers for file system access, databases, etc.
2. **Custom Plugins**: Create plugins for specific functionality
3. **Production Deployment**: Set up for production use
4. **Advanced Features**: Add authentication, rate limiting, etc.

## Troubleshooting

### "API Key not found"
- Run `python scripts/setup_env.py` to set up your API key
- Make sure the `.env` file exists in the project root

### "Failed to connect to OpenAI API"
- Verify your API key is correct
- Check your internet connection
- Ensure you have API credits

### "Module not found"
- Make sure you're in the virtual environment
- Run `pip install -r requirements.txt`

## Support

- Check logs in `logs/chatbot.log`
- Run tests: `python scripts/test_llm_config.py`
- See full documentation in `docs/`

## Cost Optimization

For testing, the configuration uses `gpt-3.5-turbo` which is cost-effective:
- ~$0.002 per 1K tokens
- Monitor usage at https://platform.openai.com/usage

To use more powerful models, edit `config/chatbot_config.yaml`:
```yaml
llm:
  providers:
    openai:
      model: "gpt-4"  # More powerful but more expensive
``` 