'''

Tool suite

'''

tools = [
    {
        "name": "web_search",
        "type": "web_search_20250305"
    }
]

def execute_tool(tool_name, tool_input):
    '''
    Main execution of the desired tool
    
    :param name: Name of tool
    :param input: Input by Claude, i.e. query for web search
    '''
    match tool_name:
        case "web_search":
            return _web_search(tool_input["query"])
        case _:
            return "No tool found"
            
def _web_search(query):
    pass