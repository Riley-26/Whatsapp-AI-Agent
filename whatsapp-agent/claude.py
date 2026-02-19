'''

Contains all logic for Claude API requests

'''
import os
from convo import get_history, add_message
import anthropic
from dotenv import load_dotenv
from tools import execute_tool, tools

load_dotenv()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL")

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
    
    try:
        claude_response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=messages,
            tools=tools
        )
        
        result = ""
        
        # Check if Claude wants to use a tool
        while claude_response.stop_reason == "tool_use":
            print(claude_response.content)
            
            # Save Claude's response
            agent_content = []
            for block in claude_response.content:
                if block.type == "text":
                    agent_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    agent_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    
            add_message(phone, "assistant", agent_content)

            # Execute tools
            tool_results = []
            for block in claude_response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
                
            # Add tool results to conversation
            add_message(phone, "user", tool_results)
            messages = get_history(phone)
        
            # Call Claude again with tool results
            claude_response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=messages,
                tools=tools
            )

        # Extract text from results
        text_parts = []
        for block in claude_response.content:
            if block.type == "text":
                text_parts.append(block.text)
        final_text = "".join(text_parts) if text_parts else ""
        
        add_message(phone, "assistant", final_text)

        return final_text, result
    except Exception as e:
        print(f"Claude API error: {e}")
        return "Sorry, I'm having trouble right now. Please try again."
    
if __name__ == "__main__":
    print(get_response("whatsapp:+14155238886", "Hello! Can you generate me an image of the moon?"))