'''

Tool suite

'''
from pathlib import Path
import uuid
import requests
import base64
from openai import OpenAI
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

import tempfile
IMAGES_DIR = Path(tempfile.gettempdir()) / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

tools = [
    {
        "name": "web_search",
        "type": "web_search_20250305"
    },
    {
        "name": "generate_image",
        "description": """Generate an image from a text description.
        
        Parse the user's message for preferences:
        - Size keywords: "portrait", "landscape", "square"
        - Quality keywords: "low-quality", "medium-quality", "high-quality"
        - Format keywords: "png", "jpeg", "webp"
        - Background keywords: "transparent" (NOTE: Transparent is only available if the format is "png" or "webp", omit otherwise)
        - Style keywords: "vivid", "natural", "realistic"
        
        If no preferences mentioned, use and SPECIFY defaults: 1024x1024, standard quality, natural style.
        
        Examples:
        - "Generate a portrait image of the moon in high quality" -> size=1024x1536, quality=high
        - "Create a vivid landscape of mountains" -> size=1536x1024, style=vivid
        - "Create a vivid landscape of mountains in a square size" -> size=1024x1024, style=vivid
        - "Make a realistic square image of a cat" -> size=1024x1024, style=realistic""",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "A detailed description of the image to generate"
                },
                "size": {
                    "type": "string",
                    "enum": ["1024x1024", "1024x1536", "1536x1024"],
                    "description": "Image dimensions",
                    "default": "1024x1024"
                },
                "quality": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Image quality level",
                    "default": "medium"
                },
                "format": {
                    "type": "string",
                    "enum": ["png", "jpeg", "webp"],
                    "description": "Image output format",
                    "default": "png"
                },
                "background": {
                    "type": "string",
                    "enum": ["transparent"],
                    "description": "Sets the image's background to transparent or not",
                    "default": ""
                },
                "style": {
                    "type": "string",
                    "enum": ["vivid", "natural", "realistic"],
                    "description": "Visual style - vivid for hyper-real and dramatic, natural for more subtle, realistic for just standard realism",
                    "default": "vivid"
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
            return generate_image(
                prompt=tool_input["prompt"],
                size=tool_input.get("size", "1024x1024"),
                quality=tool_input.get("quality", "medium"),
                output_format=tool_input.get("format", "png"),
                background=tool_input.get("background"),
                style=tool_input.get("style")
            )
        case _:
            return "No tool found"
            
def generate_image(prompt, size="1024x1024", quality="medium", output_format="png", background=None, style=None):
    '''
    Generate image using GPT
    Returns: URL to the generated image
    '''
    
    if style:
        prompt = f"{prompt}, {style} style"
    
    try:
        openai_response = openai_client.images.generate(
            model="gpt-image-1-mini",
            prompt=prompt,
            size=size,
            quality=quality,
            output_format=output_format
        )
        
        image_base64 = openai_response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)
        
        image_id = str(uuid.uuid4())
        image_path = IMAGES_DIR / f"{image_id}.{output_format}"
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
            
        return f"Image generated successfully. IMAGE_ID: {image_id} IMAGE_FORMAT: {output_format}"
            
    except Exception as e:
        print(e)
        return f"Failed to generate image: {e}"