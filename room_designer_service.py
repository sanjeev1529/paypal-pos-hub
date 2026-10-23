"""OpenAI image editing for the Room Designer."""
import base64

import httpx

from config import OPENAI_API_KEY, OPENAI_IMAGE_MODEL


def design_room(room_image: bytes, filename: str, product: dict, style_notes: str = "") -> bytes:
    """Place a catalog item into a room photo and return the generated PNG bytes."""
    if not OPENAI_API_KEY:
        raise RuntimeError("Add OPENAI_API_KEY to your .env file to generate room designs.")

    details = product.get("description") or product["name"]
    prompt = (
        "Edit this real room photo into a realistic interior-design preview. Keep the room's "
        "architecture, windows, doors, camera angle, and lighting consistent. Add the selected "
        f"catalog furniture item as the clear focal point: {product['name']}. Product details: {details}. "
        "Choose believable scale, perspective, contact shadows, and natural placement. Do not add "
        "unrequested furniture, text, labels, or watermarks."
    )
    if style_notes.strip():
        prompt += f" Customer design preferences: {style_notes.strip()}"

    content_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    files = {"image[]": (filename, room_image, content_type)}
    data = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "size": "1536x1024",
        "quality": "medium",
        "output_format": "png",
    }
    try:
        response = httpx.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            data=data,
            files=files,
            timeout=180,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Could not reach the image service: {exc}") from exc

    if response.is_error:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        raise RuntimeError(f"Image generation failed: {message}")
    try:
        encoded = response.json()["data"][0]["b64_json"]
        return base64.b64decode(encoded)
    except (ValueError, KeyError, IndexError) as exc:
        raise RuntimeError("The image service returned an unexpected response.") from exc
