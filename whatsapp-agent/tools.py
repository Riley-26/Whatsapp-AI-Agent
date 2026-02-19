'''

Tool suite

'''
import requests
import base64
from openai import OpenAI
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

tools = [
    {
        "name": "web_search",
        "type": "web_search_20250305"
    },
    {
        "name": "generate_image",
        "description": "Generate an image from a text description. Use this when the user asks to create, draw, generate or make an image",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "A detailed description of the image to generate."
                },
                "style": {
                    "type": "string",
                    "enum": ["photorealistic", "artistic", "illustration", "3d-render"],
                    "description": "The visual style of the image."
                }
            },
            "required": ["prompt"]
        }
    }
]

def execute_tool(tool_name, tool_input):
    '''
    Main execution of the desired tool
    
    :param name: Name of tool
    :param input: Input by Claude, i.e. query for web search
    '''
    match tool_name:
        case "generate_image":
            return generate_image(tool_input["prompt"], tool_input.get("style"))
        case _:
            return "No tool found"
            
def generate_image(prompt, style=None):
    '''
    Generate image using DALL-E 3
    Returns: URL to the generated image
    '''
    
    if style:
        prompt = f"{prompt}, {style} style"
    
    try:
        openai_response = openai_client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            response_format="url",
            size="256x256"
        )
        
        image_url = openai_response.data[0].url

        return {
            "type": "image",
            "source": {
                "type": "url",
                "url": image_url
            }
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }