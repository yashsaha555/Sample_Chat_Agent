import os
import io
import base64
import json
from typing import Optional

from PIL import Image


async def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        import pytesseract
        if os.getenv("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception:
        return ""


async def extract_math_from_image(image_bytes: bytes) -> Optional[str]:
    # Prefer Mathpix if available
    app_id = os.getenv("MATHPIX_APP_ID")
    app_key = os.getenv("MATHPIX_APP_KEY")
    if app_id and app_key:
        try:
            import requests
            b64 = base64.b64encode(image_bytes).decode()
            headers = {"app_id": app_id, "app_key": app_key, "Content-type": "application/json"}
            data = {"src": f"data:image/png;base64,{b64}", "formats": ["text", "latex_styled"]}
            r = requests.post("https://api.mathpix.com/v3/text", headers=headers, data=json.dumps(data), timeout=20)
            r.raise_for_status()
            js = r.json()
            latex = js.get("latex_styled") or js.get("latex")
            text = js.get("text")
            if latex:
                return f"LaTeX:\n{latex}\nPlain:\n{text or ''}"
            return text
        except Exception:
            pass

    # Fallback to OpenAI Vision if configured
    vision_model = os.getenv("VISION_MODEL")
    openai_key = os.getenv("OPENAI_API_KEY")
    if vision_model and openai_key:
        try:
            from openai import OpenAI
            from openai import AsyncOpenAI
            b64 = base64.b64encode(image_bytes).decode()
            client = AsyncOpenAI(api_key=openai_key, base_url=os.getenv("OPENAI_BASE_URL"))
            prompt = "Extract and transcribe any mathematical expressions. Return LaTeX when possible."
            resp = await client.chat.completions.create(
                model=vision_model,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"}
                        }
                    ]}
                ]
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    # No math extraction available
    return None
