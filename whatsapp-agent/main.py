from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
import uvicorn
import asyncio
import os
import requests
from twilio.rest import Client
import json
from fastapi import Request, Form
from claude import get_response

'''

The main server to bridge messages/prompts from whatsapp and Agent responses.

'''

load_dotenv()

app = FastAPI()

twilio_client = Client(account_sid=os.getenv("TWILIO_ACCOUNT_SID"), password=os.getenv("TWILIO_AUTH_TOKEN"))

PHONE_NUMBER = os.getenv("PHONE_NUMBER")
BACKEND_URL = "https://testing-dev.up.railway.app"

import tempfile
IMAGES_DIR = Path(tempfile.gettempdir()) / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "WhatsApp Agent Server"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/images/{image_id}.{image_format}")
async def serve_image(image_id: str, image_format: str):
    image_path = IMAGES_DIR / f"{image_id}.{image_format}"
    if not image_path.exists():
        return {"error": "Image not found"}
    
    return FileResponse(image_path, media_type=f"image/{image_format}")

@app.post("/webhook")
async def webhook_handler(request: Request):
    form_data = await request.form()
    Body = form_data.get("Body", "")
    From = form_data.get("From", "")
    Media = form_data.get("NumMedia", "")
    Media_items = []
    
    # Download and serve media items through our own endpoint
    if Media:
        for i in range(int(Media)):
            media_url = form_data.get(f"MediaUrl{i}")
            content_type = form_data.get(f"MediaContentType{i}", "image/jpeg")
            image_format = content_type.split("/")[1]  # e.g. "jpeg" from "image/jpeg"
            image_id = media_url.split("Media/")[1]

            resp = await asyncio.to_thread(
                requests.get, media_url,
                auth=(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            )
            if resp.status_code == 200:
                (IMAGES_DIR / f"{image_id}.{image_format}").write_bytes(resp.content)
                local_url = f"{BACKEND_URL}/images/{image_id}.{image_format}"
            else:
                local_url = media_url  # fallback to Twilio URL if download fails

            Media_items.append({
                "id": image_id,
                "media_type": content_type,
                "url": local_url,
            })

    agent_response_text, tool_result = await asyncio.to_thread(get_response, From, Body, Media_items)
    
    if isinstance(tool_result, dict) and tool_result.get("type") == "image":
        public_url = tool_result.get("url", None)
    else:
        public_url = None
    
    if public_url: # Checks if it's an image
        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=From,
            media_url=[public_url],
            body=agent_response_text if agent_response_text else ""
        )
        
        return Response(content="", media_type="text/plain")
    else:
        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=From,
            content_sid="HX448d22e244c513bbe65a0645536b9e5c",
            content_variables=json.dumps({"message": agent_response_text}),
        )

        return Response(content="", media_type="text/plain")
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)