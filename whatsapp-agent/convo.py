'''

Contains conversation history management

'''

conversation_store = {}

# HISTORY FUNCTIONS

def get_history(phone):
    '''
    Gets the conversation history for the associated phone number.
    
    :param phone: Phone number
    '''
    if phone not in conversation_store:
        conversation_store[phone] = []
    return conversation_store.get(phone, [])

def add_message(phone, role, content):
    '''
    Append a message to the conversation history.
    
    :param phone: Phone number
    :param role: Role for Claude API, "user" or "assistant"
    :param content: Message content
    '''
    message = {
        "role": role,
        "content": content
    }
    conversation_store[phone].append(message)
    
    return message
    

if __name__ == "__main__":
    pass