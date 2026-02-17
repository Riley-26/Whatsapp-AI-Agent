'''

Contains all logic for Claude API requests

'''
import os
from convo import get_history, add_message
import anthropic
from dotenv import load_dotenv

load_dotenv("C:/Users/riley/Desktop/robotics/Agency/AI Agents/Testing/whatsapp-agent/.env")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"

client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

def get_response(phone, user_message):
    '''
    Gets conversation history, adds the new message, calls Claude API 
    with full history then saves Claude's response to the history while returning it.
    
    :param phone: Phone number
    :param user_message: Message to be formatted for Claude API
    '''
    add_message(phone, "user", user_message)
    messages = get_history(phone)
    print(messages)
    
    if len(messages) > 0:
        claude_message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=messages
        )
    else:
        claude_message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024
        )

    add_message(phone, "assistant", claude_message.content[0].text)
    print(claude_message)
    return claude_message.content[0].text
    
if __name__ == "__main__":
    # print(get_response("whatsapp:+14155238886", "Hello! How are you?"))
    pass