#!/usr/bin/env python3
"""
Generate and edit images using OpenRouter API with various image generation models.

Supports OpenRouter image models served on the chat-completions endpoint with the
`modalities` parameter, e.g.:
- google/gemini-3.1-flash-image ("Nano Banana 2", generation + editing)
- black-forest-labs/flux.2-pro (generation + editing)
- black-forest-labs/flux.2-flex (generation + editing)

For image editing, provide an input image along with an editing prompt.
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from typing import Optional

# Image-model default follows the ALTERLAB_*_MODEL convention (skills/core/shared/model_env.md):
# reviewed 2026-09-23. google/gemini-3.1-flash-image is the GA "Nano Banana 2"; the former
# -preview ID was shut down by Google on 2026-06-25. Override via ALTERLAB_IMAGE_MODEL or --model.
DEFAULT_IMAGE_MODEL = "google/gemini-3.1-flash-image"


def default_image_model() -> str:
    """Return $ALTERLAB_IMAGE_MODEL if set/non-empty, else the dated default."""
    return os.environ.get("ALTERLAB_IMAGE_MODEL") or DEFAULT_IMAGE_MODEL


def check_env_file() -> Optional[str]:
    """Check if .env file exists and contains OPENROUTER_API_KEY."""
    # Look for .env in current directory and parent directories
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        env_file = parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENROUTER_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if api_key:
                            return api_key
    return None


def load_image_as_base64(image_path: str) -> str:
    """Load an image file and return it as a base64 data URL."""
    path = Path(image_path)
    if not path.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    # Determine MIME type from extension
    ext = path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    mime_type = mime_types.get(ext, 'image/png')
    
    with open(path, 'rb') as f:
        image_data = f.read()
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def save_base64_image(base64_data: str, output_path: str) -> None:
    """Save base64 encoded image to file."""
    # Remove data URL prefix if present
    if ',' in base64_data:
        base64_data = base64_data.split(',', 1)[1]

    # Decode and save
    image_data = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)


def generate_image(
    prompt: str,
    model: Optional[str] = None,
    output_path: str = "generated_image.png",
    api_key: Optional[str] = None,
    input_image: Optional[str] = None
) -> dict:
    """
    Generate or edit an image using OpenRouter API.

    Args:
        prompt: Text description of the image to generate, or editing instructions
        model: OpenRouter model ID (default: $ALTERLAB_IMAGE_MODEL or DEFAULT_IMAGE_MODEL)
        output_path: Path to save the generated image
        api_key: OpenRouter API key (falls back to $OPENROUTER_API_KEY, then a .env file)
        input_image: Path to an input image for editing (optional)

    Returns:
        dict: Response from OpenRouter API
    """
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found. Install with: pip install requests")
        sys.exit(1)

    model = model or default_image_model()

    # API key: explicit argument, then the environment, then a .env file
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY") or check_env_file()

    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found!")
        print("\nPlease create a .env file in your project directory with:")
        print("OPENROUTER_API_KEY=your-api-key-here")
        print("\nOr set the environment variable:")
        print("export OPENROUTER_API_KEY=your-api-key-here")
        print("\nGet your API key from: https://openrouter.ai/keys")
        sys.exit(1)

    # Determine if this is generation or editing
    is_editing = input_image is not None
    
    if is_editing:
        print(f"✏️ Editing image with model: {model}")
        print(f"📷 Input image: {input_image}")
        print(f"📝 Edit prompt: {prompt}")
        
        # Load input image as base64
        image_data_url = load_image_as_base64(input_image)
        
        # Build multimodal message content for image editing
        message_content = [
            {
                "type": "text",
                "text": prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url
                }
            }
        ]
    else:
        print(f"🎨 Generating image with model: {model}")
        print(f"📝 Prompt: {prompt}")
        message_content = prompt

    # Make API request. Gemini/GPT image models return image + text; image-only models
    # (e.g. FLUX.2) may reject a request that also asks for text, so retry once with
    # modalities=["image"] on a client error.
    response = None
    for modalities in (["image", "text"], ["image"]):
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ],
                    "modalities": modalities
                },
                timeout=300,
            )
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            sys.exit(1)
        if response.status_code in (400, 422) and len(modalities) > 1:
            continue
        break

    # Check for errors
    if response.status_code != 200:
        print(f"❌ API Error ({response.status_code}): {response.text}")
        sys.exit(1)

    result = response.json()

    # Extract and save image
    if result.get("choices"):
        message = result["choices"][0]["message"]

        # Handle both 'images' and 'content' response formats
        images = []

        if message.get("images"):
            images = message["images"]
        elif message.get("content"):
            # Some models return content as array with image parts
            content = message["content"]
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image":
                        images.append(part)

        if images:
            # Save the first image
            image = images[0]
            if "image_url" in image:
                image_url = image["image_url"]["url"]
                save_base64_image(image_url, output_path)
                print(f"✅ Image saved to: {output_path}")
            elif "url" in image:
                save_base64_image(image["url"], output_path)
                print(f"✅ Image saved to: {output_path}")
            else:
                print(f"❌ Unexpected image format: {image}")
                sys.exit(1)
        else:
            print("❌ No image found in response")
            if message.get("content"):
                print(f"Response content: {message['content']}")
            sys.exit(1)
    else:
        print("❌ No choices in response")
        print(f"Response: {json.dumps(result, indent=2)}")
        sys.exit(1)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate or edit images using OpenRouter API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with default model (Gemini 3.1 Flash Image, or $ALTERLAB_IMAGE_MODEL)
  python generate_image.py "A beautiful sunset over mountains"

  # Use a specific model
  python generate_image.py "A cat in space" --model "black-forest-labs/flux.2-pro"

  # Specify output path
  python generate_image.py "Abstract art" --output my_image.png

  # Edit an existing image
  python generate_image.py "Make the sky purple" --input photo.jpg --output edited.png

  # Edit with a specific model
  python generate_image.py "Add a hat to the person" --input portrait.png -m "black-forest-labs/flux.2-pro"

Popular image models (all support generation + editing):
  - google/gemini-3.1-flash-image (default, "Nano Banana 2", high quality)
  - black-forest-labs/flux.2-pro (frontier quality)
  - black-forest-labs/flux.2-flex (cheaper, strong text/typography)
        """
    )

    parser.add_argument(
        "prompt",
        type=str,
        help="Text description of the image to generate, or editing instructions"
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help=f"OpenRouter model ID (default: $ALTERLAB_IMAGE_MODEL or {DEFAULT_IMAGE_MODEL})"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="generated_image.png",
        help="Output file path (default: generated_image.png)"
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Input image path for editing (enables edit mode)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (default: $OPENROUTER_API_KEY, then a .env file)"
    )

    args = parser.parse_args()

    generate_image(
        prompt=args.prompt,
        model=args.model,
        output_path=args.output,
        api_key=args.api_key,
        input_image=args.input
    )


if __name__ == "__main__":
    main()
