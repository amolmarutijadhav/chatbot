# LLM Setup Guide

This guide will help you configure real LLM functionality for your Intelligent MCP Chatbot.

## Prerequisites

1. **OpenAI API Key**: You'll need an OpenAI API key to use GPT models
2. **Python Environment**: Make sure you have the virtual environment activated

## Step 1: Get an OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (it starts with `sk-`)

## Step 2: Set Environment Variable

### Windows (PowerShell)
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

### Windows (Command Prompt)
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

### Linux/Mac
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### Permanent Setup (Recommended)

Create a `.env` file in your project root:
```bash
# .env file
OPENAI_API_KEY=sk-your-api-key-here
CHATBOT_ENVIRONMENT=development
CHATBOT_DEBUG=true
```

Then install python-dotenv and load it in your application:
```bash
pip install python-dotenv
```

## Step 3: Test Configuration

Run the LLM configuration test:

```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Run the test
python scripts/test_llm_config.py
```

You should see output like:
```
🔧 Testing LLM Configuration...
==================================================
✅ API Key found: sk-1234...abcd
✅ LLM Configuration loaded
   Default provider: openai
✅ OpenAI configuration found
   Model: gpt-3.5-turbo
   Base URL: https://api.openai.com/v1

🔌 Testing OpenAI connection...
✅ Successfully connected to OpenAI API
✅ Available models: 50
   - gpt-4
   - gpt-4-turbo
   - gpt-3.5-turbo
   - gpt-3.5-turbo-16k
   - text-embedding-ada-002
   ... and 45 more

🧪 Testing response generation...
✅ Response received: Hello from OpenAI!

🔧 Testing LLM Manager...
✅ LLM Manager started successfully
✅ Available providers: ['openai']
✅ Manager response: Hello from LLM Manager!
✅ LLM Manager stopped successfully

==================================================
🎉 All LLM tests passed successfully!
Your chatbot is ready to use with real LLM functionality.
```

## Step 4: Run the Chatbot

### Demo Mode
```bash
python src/main.py demo
```

### Interactive Mode
```bash
python src/main.py interactive
```

### API Server
```bash
python src/api_main.py
```

## Configuration Options

### Model Selection

You can change the model in `config/chatbot_config.yaml`:

```yaml
llm:
  providers:
    openai:
      model: "gpt-4"  # or "gpt-3.5-turbo", "gpt-4-turbo", etc.
```

### Cost Optimization

For testing, use `gpt-3.5-turbo` which is more cost-effective:
- `gpt-3.5-turbo`: ~$0.002 per 1K tokens
- `gpt-4`: ~$0.03 per 1K tokens
- `gpt-4-turbo`: ~$0.01 per 1K tokens

### Alternative Providers

You can also configure Anthropic Claude:

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Uncomment the anthropic section in `config/chatbot_config.yaml`
3. Set the `ANTHROPIC_API_KEY` environment variable

```yaml
llm:
  default_provider: "anthropic"  # Change default
  providers:
    anthropic:
      type: "anthropic"
      base_url: "https://api.anthropic.com"
      chat_completion_url: "/v1/messages"
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-3-haiku-20240307"  # Cost-effective model
```

## Troubleshooting

### Common Issues

1. **"API Key not found"**
   - Make sure you've set the environment variable correctly
   - Check that the variable name is exactly `OPENAI_API_KEY`

2. **"Failed to connect to OpenAI API"**
   - Verify your API key is valid
   - Check your internet connection
   - Ensure you have sufficient API credits

3. **"Rate limit exceeded"**
   - Reduce the rate limit in configuration
   - Wait a few minutes before trying again

4. **"Model not found"**
   - Check that the model name is correct
   - Ensure you have access to the specified model

### Debug Mode

Enable debug logging in `config/chatbot_config.yaml`:

```yaml
logging:
  level: "DEBUG"
  console_output: true
```

### API Usage Monitoring

Monitor your API usage at:
- [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- [Anthropic Usage Dashboard](https://console.anthropic.com/usage)

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables for secrets**
3. **Rotate API keys regularly**
4. **Monitor API usage for unexpected charges**
5. **Set up usage alerts in your provider dashboard**

## Next Steps

Once LLM is working:

1. **Test MCP Integration**: Configure real MCP servers
2. **Add Plugins**: Implement custom functionality
3. **Deploy**: Set up production environment
4. **Monitor**: Add logging and metrics

## Support

If you encounter issues:

1. Check the logs in `logs/chatbot.log`
2. Run the test script: `python scripts/test_llm_config.py`
3. Verify your API key and configuration
4. Check the provider's status page for service issues 