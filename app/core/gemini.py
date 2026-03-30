import json
import re
import requests
from app.core.config import settings


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in response.")

    json_str = cleaned[start : end + 1]
    return json.loads(json_str)


def generate_product_estimate(*, product_name: str, brand: str, category: str, price: float) -> dict:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3-flash-preview:generateContent?key={settings.GEMINI_API_KEY}"
    )

    prompt = f"""
    You are a helpful assistant for an Amazon/AliExpress dropshipper that provides informed decisions about products.
    Given the following product information:
    - Product Name: {product_name}
    - Brand: {brand}
    - Category: {category}
    - Price: {price}

    Research the following for similar products in the same scope:
    - Estimate for bulk buying cost (per unit)
    - Suggested selling price
    - Margin Estimate
    - Uncertainty (How confident are you in the above estimates?)

    Return your findings in the following json format, only return the json without any additional text:
    {{
        "bulk_cost": $ value,
        "selling_price": $ value,
        "margin_percent": % value,
        "margin_value": $ value,
        "uncertainty": "High/Medium/Low"
    }}
    """

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "tools": [
            {
                "google_search": {}
            }
        ]
    }

    last_error = None
    for attempt in range(3):
        try:
            timeout = 60 + (attempt * 30)  # 60s, 90s, 120s
            response = requests.post(url, json=body, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return _extract_json(text)
        except requests.exceptions.Timeout as e:
            last_error = e
            continue
        except requests.exceptions.ConnectionError as e:
            last_error = e
            continue

    raise last_error or RuntimeError("Gemini API failed after 3 attempts")
