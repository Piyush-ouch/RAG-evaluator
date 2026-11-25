import asyncio
import sys
import httpx

async def test_gemini_key(api_key: str):
    print(f"Testing Gemini API Key: {api_key[:6]}...{api_key[-4:] if len(api_key)>10 else ''}\n")
    models_to_try = [
        "gemma-4-26b-a4b-it",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
    ]

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": "Hello! Please reply with a short confirmation message saying 'Google Gemini API key is active and working successfully!'."}]
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=30.0)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", []))
                        print("=" * 60)
                        print(f"SUCCESS! Connection verified using model: {model}")
                        print("=" * 60)
                        print(f"Gemini AI Response:\n{text.strip()}")
                        print("=" * 60)
                        return True
                else:
                    err_msg = resp.json().get("error", {}).get("message", resp.text[:120])
                    print(f"Model {model} returned status {resp.status_code}: {err_msg}")
        except Exception as e:
            print(f"Error testing model {model}: {e}")

    print("\nCould not verify generation with fallback models.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_gemini.py <YOUR_API_KEY>")
        sys.exit(1)
    
    key = sys.argv[1]
    asyncio.run(test_gemini_key(key))
