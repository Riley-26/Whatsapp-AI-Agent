from dotenv import load_dotenv
from fastapi import FastAPI
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

@app.get("/")
async def root():
    return {"message": "WhatsApp Agent Server"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook_handler(
    Body: str = Form(...),
    From: str = Form(...)
):
    print(f"Message from {From}: {Body}")
    agent_response_text = get_response(From, Body)
    
    message = twilio_client.messages.create(
        from_="whatsapp:+14155238886",
        to=PHONE_NUMBER,
        content_sid="HX448d22e244c513bbe65a0645536b9e5c",
        content_variables=json.dumps({"message": agent_response_text}),
    )
    
    print(message.body)
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)