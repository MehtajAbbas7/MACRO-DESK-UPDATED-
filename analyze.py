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

key = os.environ.get('GROQ_KEY', '').strip()
print("Key length check:", len(key))

url = "https://api.groq.com/openai/v1/chat/completions"
body = json.dumps({
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3
}).encode()
req = urllib.request.Request(
    url,
    data=body,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key
    }
)

analysis = {}
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
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
