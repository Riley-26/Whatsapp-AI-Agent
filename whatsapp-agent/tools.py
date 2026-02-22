'''

Tool suite

'''
from datetime import datetime
from pathlib import Path
import uuid
import requests
import base64
from openai import OpenAI
from io import BytesIO
import os
from dotenv import load_dotenv
from convo import get_system_context, save_system_context

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

import tempfile
IMAGES_DIR = Path(tempfile.gettempdir()) / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# BACKEND_URL = "https://testing-dev.up.railway.app"
BACKEND_URL = "https://testing-production-2f9c.up.railway.app"

tools = [
    {
        "name": "update_system_context",
        "description": """Update the long-term system context with important information.

Use this when you learn something significant about the user that should persist:
- User preferences (image styles, communication preferences)
- Important facts (their job, interests, location)
- Patterns you've noticed (common requests, schedules)
- Rules or principles for this specific user

When updating a section, append the new information. You should only replace existing information if it becomes redundant or outdated, or if the user requests for you to. 
For example, if the user changes what the current project they're working on is.

DO NOT update for:
- Casual conversation
- Temporary information
- Single-use facts

DO NOT update the sub-sections under the "Agent Profile" section (marked as [LOCKED] to help you).

DO preserve formatting when editing the markdown, i.e. keep the newlines between sections.

IMPORTANT: The tool replaces the entire section with the "content" parameter, therefore you MUST return the existing content along with the new information (usually only when adding information, but sometimes you may replace information)

The context is limited, so only store what's genuinely valuable long-term.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["user_info", "patterns", "domain_knowledge", "rules", "key_facts"],
                    "description": "Which section to update"
                },
                "content": {
                    "type": "string",
                    "description": "What to add/update in that section"
                }
            },
            "required": ["section", "content"]
        }
    },
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
    },
    {
        "name": "edit_image",
        "description": """Edit a previously generated image from this conversation.

To use this tool:
1. Look through the conversation history for images
2. Identify which image the user wants to edit (most recent, specific description, etc.)
3. Call this tool with the image reference and edit instructions

Examples:
- "Edit the last image to make it darker" -> Find most recent image
- "Change the moon image to have stars" -> Find image with 'moon' in prompt
- "Make my cat image black and white" -> Find image with 'cat' in prompt""",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_reference": {
                    "type": "string",
                    "description": "How to identify the image: 'last', 'most_recent', or search term from original prompt"
                },
                "edit_instructions": {
                    "type": "string",
                    "description": "What changes to make to the image"
                },
                "mask": {
                    "type": "string",
                    "description": "Optional: Area to edit (not implemented yet)",
                    "default": None
                }
            },
            "required": ["image_reference", "edit_instructions"]
        }
    }
]

def execute_tool(tool_name, tool_input, phone=None):
    '''
    Main execution of the desired tool
    
    :param name: Name of tool
    :param input: Input by Claude, i.e. query for web search
    '''
    match tool_name:
        case "update_system_context":
            return _update_system_context(phone, tool_input["section"], tool_input["content"], tool_input["action"])
        case "generate_image":
            return _generate_image(
                prompt=tool_input["prompt"],
                size=tool_input.get("size", "1024x1024"),
                quality=tool_input.get("quality", "medium"),
                output_format=tool_input.get("format", "png"),
                background=tool_input.get("background"),
                style=tool_input.get("style")
            )
        case "edit_image":
            return _edit_image()
        case _:
            return "No tool found"
            
def _generate_image(prompt, size="1024x1024", quality="medium", output_format="png", background=None, style=None):
    '''
    Generate image using GPT
    Returns: URL to the generated image
    '''
    
    if style:
        prompt = f"{prompt}, {style} style"
    
    try:
        openai_response = openai_client.images.generate(
            model=os.getenv("OPENAI_MODEL", "gpt-image-1-mini"),
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
            
        return [{
            "type": "image",
            "source": {
                "type": "url",
                "url": f"{BACKEND_URL}/images/{image_id}.{output_format}"
            }
        }]
    except Exception as e:
        print(e)
        return f"Failed to generate image: {e}"
    
def _edit_image():
    pass

def _update_system_context(phone, section, content, action):
    """
    Update the markdown system context
    """
    current_context = get_system_context(phone)
    section_headers = {
        "user_info": "## User Information",
        "patterns": "## Learned Patterns",
        "domain_knowledge": "## Domain Knowledge",
        "rules": "## Important Rules",
        "key_facts": "## Key Facts to Remember"
    }
    
    header = section_headers[section]
    
    updated_context = current_context.replace(
        header,
        f"{header}\n- {content}"
    )
    
    save_system_context(updated_context, phone)
    
    return "System context updated"