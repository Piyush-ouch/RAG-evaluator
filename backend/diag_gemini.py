import asyncio
import httpx
import sys

async def check_all_models(key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            print("API Key invalid or forbidden:", resp.text)
            return

        models = resp.json().get("models", [])
        gen_models = [m["name"].replace("models/", "") for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
        print(f"Found {len(gen_models)} models supporting generateContent.\n")

        for m in gen_models:
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
            payload = {"contents": [{"role": "user", "parts": [{"text": "Hi"}]}]}
            try:
                r = await client.post(gen_url, json=payload, timeout=10.0)
                if r.status_code == 200:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"SUCCESS on model '{m}'!")
                    print(f"Response: {text.strip()}")
                    return
                else:
                    err_msg = r.json().get("error", {}).get("message", r.text[:80])
                    print(f"Model '{m}' -> Code {r.status_code}: {err_msg}")
            except Exception as e:
                print(f"Model '{m}' -> Error: {e}")

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    asyncio.run(check_all_models(key))
