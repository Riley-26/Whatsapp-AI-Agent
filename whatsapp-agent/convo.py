'''

Contains conversation history management

'''

conversation_store = {
    "whatsapp:+14155238886": []
}

# HISTORY FUNCTIONS

def get_history(phone):
    '''
    Gets the conversation history for the associated phone number.
    
    :param phone: Phone number
    '''
    messages = []
    if not phone:
        return "No phone number provided"
    
    for i in conversation_store[phone]:
        messages.append(i)
    return messages

def add_message(phone, role, content):
    '''
    Append a message to the conversation history.
    
    :param phone: Phone number
    :param role: Role for Claude API, "user" or "assistant"
    :param content: Message content
    '''
    if not phone:
        return "No phone number provided"
    if not role:
        return "No role provided"
    if not content:
        return "No content provided"
    
    message = {
        "role": role,
        "content": content
    }
    conversation_store[phone].append(message)
    
    return "Message added"
    

if __name__ == "__main__":
    pass