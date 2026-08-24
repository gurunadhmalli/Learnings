# INSTANT GRATIFICATION - Part 2 (Cohere Edition)

## Adding AI to Your Production App (with Cohere instead of OpenAI)

This is the Cohere version of the "Instant Gratification" tutorial, for anyone who doesn't have OpenAI credits. Cohere offers a free trial API key with no credit card required.

## Step 1: Get Your Cohere API Key

1. Visit [dashboard.cohere.com](https://dashboard.cohere.com) and sign up for a free account.
2. No payment or credit card is required for the trial key.
3. Go to the **API Keys** section of the dashboard.
4. Copy your trial key (it does not start with `sk-`, it's just a plain string).
5. **Save it somewhere safe** (use a plain text editor, not a word processor like Word that might format the characters).

Note: the free trial key has rate limits (roughly 20 calls/minute, 1000 calls/month) — fine for testing and small projects, but worth knowing if traffic grows.

## Step 2: Add Your API Key to Vercel

In your terminal, type:

```bash
vercel env add COHERE_API_KEY
```

- When prompted for the value, paste your API key.
- Select all environments (development, preview, production) when asked.

## Step 3: Update Dependencies

Open your `requirements.txt` file and add the Cohere library instead of openai:

```
fastapi
uvicorn
cohere
```

Save the file.

## Step 4: Update Your Application Code

Replace the entire content of `instant.py` with:

```python
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import cohere

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def instant():
    client = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
    message = """
You are on a website that has just been deployed to production for the first time!
Please reply with an enthusiastic announcement to welcome visitors to the site, explaining that it is live on production for the first time!
"""
    messages = [{"role": "user", "content": message}]
    response = client.chat(model="command-a-03-2025", messages=messages)
    reply = response.message.content[0].text.replace("\n", "<br/>")
    html = f"<html><head><title>Live in an Instant!</title></head><body><p>{reply}</p></body></html>"
    return html
```

Save the file.

## Step 5: Deploy Your AI-Enhanced App

Deploy to development first to test:

```bash
vercel .
```

Once it's deployed:

1. Visit the URL provided.
2. You should see a dynamic, AI-generated welcome message!
3. Refresh the page to see different variations.

Deploy to production when ready:

```bash
vercel --prod
```

## What's Happening?

Your app now:

- Connects to Cohere's API using your secure API key
- Generates unique, enthusiastic welcome messages for each visitor
- Returns properly formatted HTML with the AI's response
- Runs entirely serverless on Vercel's infrastructure

## Congratulations!

You've successfully:

- Integrated AI into a production application
- Secured API credentials using environment variables
- Created dynamic, personalized content
- Built your first AI-powered web application (without needing to pay for OpenAI credits)

## What You've Learned

- How to securely manage API keys in production
- How to integrate Cohere's API with FastAPI
- How to use environment variables in Vercel
- How to create dynamic HTML responses with AI-generated content

## Next Steps

- Try modifying the prompt to create different types of content
- Add query parameters to customize the AI's response
- Experiment with different Cohere models (e.g. `command-r-plus`, `command-r`)
- Add error handling for API failures and rate limits

## Troubleshooting

### "Cohere API key not found"

- Make sure you added the environment variable with `vercel env add COHERE_API_KEY`
- Check that the key name is exactly `COHERE_API_KEY`
- Redeploy after adding the environment variable

### "Rate limit exceeded"

- The free trial key is capped at roughly 20 calls/minute and 1000 calls/month
- Wait a bit and try again, or upgrade to a production key if you need more headroom

### Page loads slowly

- The first request may be slower as the serverless function cold starts
- Subsequent requests should be faster
- This is normal behavior for serverless functions

## Security Note

Your API key is:

- Never exposed in your code
- Securely stored in Vercel's environment variables
- Only accessible to your deployed application
- Protected from being visible in browser developer tools
