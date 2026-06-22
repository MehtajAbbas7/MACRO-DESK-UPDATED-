import json, urllib.request, urllib.error, os

with open('data/headlines.json') as f:
    headlines_data = json.load(f)

articles = headlines_data.get('articles', [])[:15]
titles = [a.get('title', '') for a in articles if a.get('title')]
headline_text = "\n".join(titles)

prompt = """You are a macro analyst writing for someone who wants simple, clear explanations, not jargon-heavy analysis. Based on these recent financial headlines, write a JSON object with this exact structure, no markdown formatting, no extra text before or after, just the raw JSON:
{
  "usd_bias": "Bullish or Bearish or Neutral",
  "usd_reason": "one simple sentence why",
  "gold_bias": "Bullish or Bearish or Neutral",
  "gold_reason": "one simple sentence why",
  "indices_bias": "Bullish or Bearish or Neutral",
  "indices_reason": "one simple sentence why",
  "lead_story": "2-3 simple sentences on the single biggest driver right now",
  "drivers": [
    {"title": "short driver name", "tag": "Bullish or Bearish or Mixed", "explanation": "2 simple sentences explaining this driver and why it moves price"},
    {"title": "short driver name", "tag": "Bullish or Bearish or Mixed", "explanation": "2 simple sentences explaining this driver and why it moves price"},
    {"title": "short driver name", "tag": "Bullish or Bearish or Mixed", "explanation": "2 simple sentences explaining this driver and why it moves price"},
    {"title": "short driver name", "tag": "Bullish or Bearish or Mixed", "explanation": "2 simple sentences explaining this driver and why it moves price"}
  ],
  "central_banks": [
    {"bank": "Federal Reserve", "rate": "current rate or stance", "stance": "Hawkish or Dovish or Neutral", "note": "one simple sentence on why it matters"},
    {"bank": "Bank of England", "rate": "current rate or stance", "stance": "Hawkish or Dovish or Neutral", "note": "one simple sentence on why it matters"},
    {"bank": "ECB", "rate": "current rate or stance", "stance": "Hawkish or Dovish or Neutral", "note": "one simple sentence on why it matters"},
    {"bank": "Bank of Japan", "rate": "current rate or stance", "stance": "Hawkish or Dovish or Neutral", "note": "one simple sentence on why it matters"}
  ]
}

Do not include an "updated" field, it will be added separately. Keep every explanation simple, plain-English, no jargon without explaining it.

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
        "Authorization": "Bearer " + key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

if "error" not in analysis:
    from datetime import datetime, timezone
    analysis["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

with open('data/analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("Done. Result:")
print(json.dumps(analysis, indent=2))
