from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
import uvicorn
import os
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
    
    # Save media items
    if Media:
        for i in range(int(Media)):
            Media_items.append({
                "url": form_data.get(f"MediaUrl{i}"),
                "format": form_data.get(f"MediaContentType{i}")
            })
        
    agent_response_text, tool_result = get_response(From, Body, Media_items)
    
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