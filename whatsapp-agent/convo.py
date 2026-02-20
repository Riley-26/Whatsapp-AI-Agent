'''

Contains conversation history management

'''
from datetime import datetime
import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()

conversation_store = {}

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT", 5432),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

# HISTORY FUNCTIONS

def get_history(phone):
    '''
    Gets the conversation history for the associated phone number.
    
    :param phone: Phone number
    '''
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.role, m.content
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE c.phone_number = %s
            ORDER BY m.created_at ASC
        """, (phone,))
        
        rows = cur.fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]
    
def get_recent_history(phone, limit=50):
    '''
    Get last N messages to stay under context window
    
    :param phone: Phone number
    :param limit: How many rows to get
    '''
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.role, m.content 
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE c.phone_number = %s
            ORDER BY m.created_at DESC
            LIMIT %s
        """, (phone, limit))
        
        rows = cur.fetchall()
        rows.reverse()  # Oldest first for Claude
        return [{"role": row[0], "content": row[1]} for row in rows]

def add_message(phone, role, content):
    '''
    Append a message to the conversation history.
    
    :param phone: Phone number
    :param role: Role for Claude API, "user" or "assistant"
    :param content: Message content
    '''
    if isinstance(content, dict):
        media = content.get("media", None)
        # If adding a user-sent media message
        if media:
            message = content.get("user_message", None)
            content_json = []
            for i in media:
                if i.get("base64"):
                    content_json.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": i.get("media_type", "image/jpeg"),
                            "data": i.get("base64"),
                        }
                    })
                else:
                    content_json.append({
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": i.get("url"),
                        }
                    })
            if message:
                content_json.append({"type": "text", "text": message})
        elif content.get("url", None):
            content_json = [{
                "type": "image",
                "source": {
                    "type": "url",
                    "url": content.get("url")
                }
            }]
    elif isinstance(content, str):
        content_json = [{"type": "text", "text": content}]
    else:
        content_json = content
        
    with conn.cursor() as cur:
        # Get or create conversation
        cur.execute("""
            INSERT INTO conversations (phone_number)
            VALUES (%s)
            ON CONFLICT (phone_number) DO UPDATE SET updated_at = NOW()
            RETURNING id
        """, (phone,))
        conv_id = cur.fetchone()[0]
        
        # Add message
        cur.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (%s, %s, %s)
        """, (conv_id, role, json.dumps(content_json)))
        
        conn.commit()
    
def clear_conversation(phone):
    '''
    Deletes conversation history on request.
    
    :param phone: Phone number
    '''
    with conn.cursor() as cur:
        # Deletes conversation
        cur.execute("""
            DELETE FROM conversations WHERE phone_number = %s
        """, (phone,))
        
        conn.commit()
    

if __name__ == "__main__":
    add_message(os.getenv("PHONE_NUMBER"), "user", "Hello there")