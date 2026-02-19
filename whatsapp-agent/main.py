from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
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
IMAGES_DIR = Path("/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_URL = "https://testing-production-2f9c.up.railway.app/"

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
        return image_path
        return {"error": "Image not found"}
    
    return FileResponse(image_path, media_type=f"image/{image_format}")

@app.post("/webhook")
async def webhook_handler(
    Body: str = Form(...),
    From: str = Form(...)
):
    print(f"Message from {From}: {Body}")
    agent_response_text = get_response(From, Body)
    
    if "IMAGE_ID: " in agent_response_text:
        image_id = agent_response_text.split("IMAGE_ID: ")[1].split()[0]
        image_format = agent_response_text.split("IMAGE_FORMAT: ")[1].split()[0]
        public_url = f"{BACKEND_URL}/images/{image_id}-{image_format}"
        
        message = twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=PHONE_NUMBER,
            media_url=[public_url]
        )
        message = twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=PHONE_NUMBER,
            content_sid="HX448d22e244c513bbe65a0645536b9e5c",
            content_variables=json.dumps({"message": agent_response_text}),
        )
    else:
        message = twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=PHONE_NUMBER,
            content_sid="HX448d22e244c513bbe65a0645536b9e5c",
            content_variables=json.dumps({"message": agent_response_text}),
        )
        
    print(message.body)
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)