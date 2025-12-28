import os
import io
import zipfile
import textwrap
import google.generativeai as genai
from PIL import Image

def init_gemini(api_key):
    """Initializes the Gemini API with the provided key."""
    if not api_key:
        return False, "API Key is missing."
    try:
        genai.configure(api_key=api_key)
        return True, "API Key configured successfully."
    except Exception as e:
        return False, str(e)

def generate_stamp(base_image, text, style_prompt=""):
    """
    Generates a stamp image using Gemini (Imagen 3) based on a base image and text.
    
    Args:
        base_image (PIL.Image): The reference character image.
        text (str): The text/dialogue for the stamp.
        style_prompt (str): Additional style description.
    
    Returns:
        PIL.Image: The generated image resized to target dimensions.
    """
    try:
        # Note: As of late 2024/early 2025, the Python SDK for Imagen 3 might vary.
        # This implementation assumes the 'imagen-3.0-generate-001' or similar model is accessible 
        # via the standard generation methods, or we use a text-to-image prompting strategy 
        # if direct image-to-image is not strictly supported in the same way.
        # However, for 'keeping character features', we ideally need Model fine-tuning or 
        # a strong multi-modal prompt with the image as input.
        # Standard Imagen 3 API often takes text prompts. 
        # If we can't pass the image directly for style transfer content preservation in standard API without fine-tuning,
        # we will describe the character or assume the user prompt allows for it.
        # BUT, since the user asked for "Gemini 3 Pro", we might be using the Multi-modal capabilities of Gemini 1.5 Pro/Flash
        # or the newer Gemini models to GENERATE images (if supported) or just describe it.
        # 
        # The prompt specifically asked for "Image Generation Engine: Gemini 3 Pro (Imagen 3 API)".
        # We will use the 'imagen-3.0-generate-001' model for generation.
        
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        
        # Construct a detailed prompt
        # Since we can't easily pass the 'base_image' ref to Imagen 3 standard API (it's text-to-image usually),
        # WE WILL ASSUME THIS IS A LIMITATION unless we use Gemini 1.5 Pro to 'describe' the image first, 
        # then pass the description to Imagen.
        # Let's try that hybrid approach if possible, OR just rely on the text prompt if the user didn't implement image upload logic for the prompt.
        # Wait, the requirements said "Upload base image... Exec logic: preserve base image features".
        # This implies we might need to describe the image first.
        
        # Step 1: Describe the base image if provided
        # We need a vision model for this.
        vision_model = genai.GenerativeModel('gemini-1.5-pro') # Or pro-002, 1.5-flash which is faster
        
        if base_image:
             desc_response = vision_model.generate_content([
                 "Describe this character in detail, focusing on physical appearance (hair, eyes, clothes, colors), art style, and key features so that an artist can draw it exactly the same. Keep it concise but descriptive.",
                 base_image
             ])
             character_description = desc_response.text
        else:
             character_description = "A cute mascot character."

        full_prompt = f"""
        Create a LINE sticker/stamp illustration of a character.
        
        Character Description:
        {character_description}
        
        Action/Pose/Emotion based on this text: "{text}"
        
        Style:
        {style_prompt}
        Vector art, clean lines, white background, suitable for a sticker.
        """
        
        result = model.generate_images(
            prompt=full_prompt,
            number_of_images=1,
            aspect_ratio="1:1", # approximate, we resize later
            safety_filter_level="block_only_high",
            person_generation="allow_adult"
        )
        
        if result and result.images:
            # Access PIL image safely
            if hasattr(result.images[0], 'image'):
                generated_image = result.images[0].image
            elif hasattr(result.images[0], '_pil_image'):
                generated_image = result.images[0]._pil_image
            else:
                # Fallback or error if neither exists (though one should)
                # In some versions, result.images[0] IS the PIL image
                if isinstance(result.images[0], Image.Image):
                     generated_image = result.images[0]
                else:
                     raise ValueError("Could not retrieve PIL image from response.")

            # RESIZE to LINE specs (max 370x320)
            # We will resize to fit within 370x320 maintaining aspect ratio
            generated_image.thumbnail((370, 320), Image.Resampling.LANCZOS)
            return generated_image
        
        return None

    except Exception as e:
        print(f"Error generating image: {e}")
        return None

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
