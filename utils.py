import os
import io
import zipfile
import textwrap
from google import genai
from google.genai import types
from PIL import Image

# Global client instance
_client = None

def init_gemini(api_key):
    """Initializes the Gemini API Client with the provided key."""
    global _client
    if not api_key:
        return False, "API Key is missing."
    try:
        # Initialize the client
        _client = genai.Client(api_key=api_key)
        # Verify by making a cheap call? Or just assume it's good if valid format.
        # Actually initializing the client doesn't validate the key until a call is made.
        return True, "API Key configured successfully."
    except Exception as e:
        return False, str(e)

def generate_stamp(base_image, text, style_prompt=""):
    """
    Generates a stamp image using Gemini (Imagen 3) based on a base image and text.
    Uses a two-step process:
    1. Describe the base image (if present) using Gemini 1.5 Pro.
    2. Generate the stamp using Imagen 3 with the description + text.
    
    Args:
        base_image (PIL.Image): The reference character image.
        text (str): The text/dialogue for the stamp.
        style_prompt (str): Additional style description.
    
    Returns:
        tuple: (PIL.Image or None, str or None) - The generated image and an error message if any.
    """
    global _client
    if not _client:
        return None, "API not initialized. Please configure API Key."

    try:
        # Step 1: Describe the base image if provided
        character_description = "A cute mascot character."
        
        if base_image:
            try:
                # Resize base image if too large (optional, but good practice for API)
                img_byte_arr = io.BytesIO()
                base_image.save(img_byte_arr, format='PNG')
                # Base64 encoding is handled by the SDK if we pass the PIL image directly usually, 
                # or we can pass bytes. The new SDK supports PIL images in contents.
                
                response = _client.models.generate_content(
                    model='gemini-1.5-pro',
                    contents=[
                        "Describe this character in detail, focusing on physical appearance (hair, eyes, clothes, colors), art style, and key features so that an artist can draw it exactly the same. Keep it concise but descriptive.",
                        base_image
                    ]
                )
                if response.text:
                    character_description = response.text
            except Exception as e:
                print(f"Error describing image: {e}")
                # Fallback to default description if vision fails, but log it
                pass

        # Step 2: Generate Image with Imagen 3
        full_prompt = f"""
        Create a LINE sticker/stamp illustration of a character.
        
        Character Description:
        {character_description}
        
        Action/Pose/Emotion based on this text: "{text}"
        
        Style:
        {style_prompt}
        Vector art, clean lines, white background, suitable for a sticker.
        """
        
        # Imagen 3 generation
        # model: imagen-3.0-generate-001
        
        try:
            response = _client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    include_rai_reason=True
                )
            )
        except Exception as e:
            # Check for 404 or other API errors
            error_str = str(e)
            if "404" in error_str or "NOT_FOUND" in error_str:
                # Attempt to list models to help debugging
                try:
                    all_models = _client.models.list()
                    # Filter for image generation models if possible, or just list a few
                    model_names = [m.name for m in all_models]
                    return None, f"Model 'imagen-3.0-generate-001' not found. Available models on your key: {model_names}. ERROR details: {error_str}"
                except Exception as list_err:
                     return None, f"Model not found and failed to list models: {list_err}. Original error: {error_str}"
            else:
                raise e
        
        if response.generated_images:
            generated_image_obj = response.generated_images[0]
            # New SDK returns an object with .image (PIL Image) usually
            if hasattr(generated_image_obj, 'image'):
                 generated_image = generated_image_obj.image
            else:
                 # It might be raw bytes in some versions/configs?
                 # SDK v1 usually returns PIL image in .image property
                 return None, "Generated image object format not recognized."

            # RESIZE to LINE specs (max 370x320)
            if generated_image:
                generated_image.thumbnail((370, 320), Image.Resampling.LANCZOS)
                return generated_image, None
        
        return None, "No image returned from API."

    except Exception as e:
        print(f"Error generating image: {e}")
        return None, str(e)

def create_zip(images_map):
    """
    Creates a ZIP file from a dictionary of {filename: PIL.Image}.
    
    Args:
        images_map (dict): Keys are filenames (e.g., "stamp_01.png"), values are PIL Images.
        
    Returns:
        bytes: The ZIP file content.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, img in images_map.items():
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            zf.writestr(filename, img_byte_arr.getvalue())
    return zip_buffer.getvalue()
