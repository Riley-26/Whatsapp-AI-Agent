from fastapi import FastAPI
import uvicorn
import os
from twilio.rest import Client
import json

'''

The main server to bridge messages/prompts from whatsapp and Agent responses.

'''

app = FastAPI()

twilio_client = Client(account_sid=os.getenv("TWILIO_ACCOUNT_SID"), password=os.getenv("TWILIO_AUTH_TOKEN"))

@app.get("/")
async def root():
    return {"message": "WhatsApp Agent Server"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook_handler():
    message = twilio_client.messages.create(
        from_="whatsapp:+14155238886",
        to="whatsapp:+447585330551",
        content_sid="HXb5b62575e6e4ff6129ad7c8efe1f983e",
        content_variables=json.dumps({"1": "22 July 2026", "2": "3:15pm"}),
    )
    
    print(message.body)
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)