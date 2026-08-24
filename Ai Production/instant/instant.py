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
