import json, urllib.request, urllib.error, os

with open('data/headlines.json') as f:
    headlines_data = json.load(f)

articles = headlines_data.get('articles', [])[:15]
titles = [a.get('title', '') for a in articles if a.get('title')]
headline_text = "\n".join(titles)

prompt = """You are a macro analyst. Based on these recent financial headlines, write a JSON object with this exact structure, no markdown formatting, no extra text before or after, just the raw JSON:
{
  "usd_bias": "Bullish or Bearish or Neutral",
  "usd_reason": "one sentence why",
  "gold_bias": "Bullish or Bearish or Neutral",
  "gold_reason": "one sentence why",
  "indices_bias": "Bullish or Bearish or Neutral",
  "indices_reason": "one sentence why",
  "lead_story": "2-3 sentence summary of the single biggest driver right now",
  "updated": "current UTC date and time"
}

Headlines:
""" + headline_text

key = os.environ.get('GEMINI_KEY', '')
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + key
body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

analysis = {}
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        analysis = json.loads(text.strip())
except urllib.error.HTTPError as e:
    analysis = {"error": "HTTP " + str(e.code) + ": " + e.read().decode()[:400]}
except Exception as e:
    analysis = {"error": str(e)}

with open('data/analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("Done. Result:")
print(json.dumps(analysis, indent=2))
