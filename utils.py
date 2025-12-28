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
                # Step 1: Deep analysis of the character
                analysis_prompt = """
                Analyze this character image for a LINE sticker project. 
                Identify and describe in detail:
                1. Art Style & Line Quality: (e.g., thick/thin lines, clean/sketchy, vector/hand-drawn)
                2. Color Palette: (exact colors, shading style, gradients)
                3. Key Features: (proportions, eye shape, accessories, hair style)
                4. Unique Identifiers: (patterns, marks, specific costume details)
                
                Provide the analysis in a way that helps another AI model reproduce this EXACT character consistently.
                """
                
                response = _client.models.generate_content(
                    model='gemini-1.5-pro',
                    contents=[analysis_prompt, base_image]
                )
                if response.text:
                    character_description = response.text
            except Exception as e:
                print(f"Error describing image: {e}")
                pass

        # Step 2: Generate Image with Imagen 4 using SubjectReferenceImage
        ref_id = "input_character"
        
        # Prepare the reference images list
        reference_images = []
        if base_image:
            # Convert PIL image to bytes for the SDK
            img_byte_arr = io.BytesIO()
            base_image.save(img_byte_arr, format='PNG')
            
            reference_images.append(
                types.ReferenceImage(
                    reference_id=ref_id,
                    reference_type="SUBJECT",
                    image=types.Part.from_bytes(
                        data=img_byte_arr.getvalue(),
                        mime_type="image/png"
                    )
                )
            )

        full_prompt = f"""
        A professional LINE sticker illustration.
        Subject: The character [{ref_id}]
        Action/Emotion: {text}
        
        Style Reconstruction Guide:
        {character_description}
        
        CRITICAL: Maintain absolute consistency with [{ref_id}]. Use the exact same line style, color treatment, and character proportions as the reference image.
        Background: Pure white background.
        Composition: Vector art, clean lines, high quality, 2D illustration.
        """
        
        try:
            # Note: Imagen 4 configuration
            response = _client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    include_rai_reason=True,
                    reference_images=reference_images if reference_images else None,
                    # strength=1.0 # If SDK supports this for reference images influence
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
                    return None, f"Model 'imagen-4.0-generate-001' not found. Available models on your key: {model_names}. ERROR details: {error_str}"
                except Exception as list_err:
                     return None, f"Model not found and failed to list models: {list_err}. Original error: {error_str}"
            else:
                raise e
        
        if response.generated_images:
            generated_image_obj = response.generated_images[0]
            
            # The SDK returns a GeneratedImage object. 
            # To ensure we have a PIL Image with .thumbnail(), we load it from the binary data.
            try:
                image_bytes = None
                
                # Try various ways the SDK might provide the bytes
                if hasattr(generated_image_obj, 'image'):
                    img_attr = generated_image_obj.image
                    if isinstance(img_attr, bytes):
                        image_bytes = img_attr
                    elif hasattr(img_attr, 'image_bytes'): # Public attribute in new SDK
                        image_bytes = img_attr.image_bytes
                    elif hasattr(img_attr, '_image_bytes'): # Internal attribute
                        image_bytes = img_attr._image_bytes
                
                if image_bytes is None and hasattr(generated_image_obj, 'binary'):
                    image_bytes = generated_image_obj.binary
                
                if image_bytes is None:
                    # Final attempt: direct cast to bytes if it's some bytes-compatible object
                    try:
                        image_bytes = bytes(generated_image_obj.image)
                    except:
                        return None, f"Could not extract image bytes from {type(generated_image_obj.image)}"
                
                # Load as PIL Image
                generated_image = Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                print(f"Error converting response to PIL Image: {e}")
                return None, f"Failed to process generated image: {e}"

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
