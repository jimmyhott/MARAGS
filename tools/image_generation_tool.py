import logging
from typing import List, Dict, Any

from langchain_core.tools import Tool
from openai import AzureOpenAI

from llm.azure_secrets import AZURE_DALL_E_3_ENDPOINT, AZURE_DALL_E_3_API_KEY

logger = logging.getLogger(__name__)

# You can use OpenAI's DALL-E, Stability AI, or any other image generation API

def generate_article_image(prompt: str, style: str = "photorealistic") -> Dict[str, Any]:
    """
    Generate an image based on the prompt for the article using Azure OpenAI DALL-E 3.

    Args:
        prompt: Description of the image to generate
        style: Style of the image (photorealistic, illustration, cartoon, etc.)

    Returns:
        Dict containing image URL or base64 data
    """
    try:
        # Initialize Azure OpenAI client for dall-e-3
        client = AzureOpenAI(
            api_key=AZURE_DALL_E_3_API_KEY,
            azure_endpoint=AZURE_DALL_E_3_ENDPOINT,
            azure_deployment='dall-e-3'
        )

        # Enhance prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        logger.info(f"Generating image with prompt: {enhanced_prompt[:100]}...")

        # Generate image using DALL-E 3
        response = client.images.generate(
            model="dall-e-3",  # or your deployment name from Azure
            prompt=enhanced_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        # Get the image URL from response
        image_url = response.data[0].url

        logger.info(f"Successfully generated image for prompt: {prompt[:50]}...")

        logger.info(image_url)

        return {
            "url": image_url,
            "prompt": prompt,
            "style": style
        }

    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")

        # Return placeholder image on error
        return {
            "url": f"https://via.placeholder.com/1024x1024.png?text=Image+Generation+Failed",
            "prompt": prompt,
            "style": style,
            "error": str(e)
        }


def get_image_generation_tools() -> List[Tool]:
    """Get image generation tools for the editor."""
    return [
        Tool(
            name="generate_article_image",
            description="Generate an image to accompany the article. Use this to create visual content that enhances the article.",
            func=generate_article_image
        )
    ]