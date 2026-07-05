import json, urllib.request, urllib.error, os, re
from datetime import datetime, timezone

with open('data/headlines.json') as f:
    headlines_data = json.load(f)

articles = headlines_data.get('articles', [])[:15]
titles = [a.get('title', '') for a in articles if a.get('title')]
headline_text = "\n".join(titles)

prompt = """You are a macro analyst writing for someone who wants simple, clear explanations. Based on these recent financial headlines, write a JSON object with this exact structure, no markdown formatting, no extra text, just raw JSON:
{
  "usd_bias": "Bullish or Bearish or Neutral",
  "usd_reason": "one simple sentence why",
  "gold_bias": "Bullish or Bearish or Neutral",
  "gold_reason": "one simple sentence why",
  "indices_bias": "Bullish or Bearish or Neutral",
  "indices_reason": "one simple sentence why",
  "lead_story": "2-3 simple sentences on the single biggest macro driver right now"
}

Headlines:
""" + headline_text

key = os.environ.get('GROQ_KEY', '').strip()
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
        "User-Agent": "Mozilla/5.0"
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

# Save analysis.json as before
analysis["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open('data/analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

# Now inject directly into index.html
if "error" not in analysis:
    with open('index.html', 'r') as f:
        html = f.read()

    updated_time = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC (auto-generated)")

    # Replace USD bias
    html = re.sub(
        r'(<div class="bias-cell">[\s\S]*?<div class="bias-asset">USD \(DXY\)</div>\s*<div class="bias-dir[^"]*">)[^<]*(</div>\s*<div class="bias-sub">)[^<]*(</div>)',
        lambda m: m.group(0).split('>')[0] + '>' +
            f'<div class="bias-asset">USD (DXY)</div>\n      <div class="bias-dir {("bull" if "bull" in analysis["usd_bias"].lower() else "bear" if "bear" in analysis["usd_bias"].lower() else "neutral")}">{analysis["usd_bias"]}</div>\n      <div class="bias-sub">{analysis["usd_reason"]}</div>',
        html
    )

    # Simpler targeted replacement using unique markers
    # USD cell
    html = re.sub(r'(?<=<div class="bias-asset">USD \(DXY\)</div>\n      <div class="bias-dir [^"]*">)[^<]*', analysis['usd_bias'], html)
    html = re.sub(r'(?<=<div class="bias-asset">USD \(DXY\)</div>\n      <div class="bias-dir [^"]*">[^<]*</div>\n      <div class="bias-sub">)[^<]*', analysis['usd_reason'], html)

    # Gold cell
    html = re.sub(r'(?<=<div class="bias-asset">Gold \(XAU/USD\)</div>\n      <div class="bias-dir [^"]*">)[^<]*', analysis['gold_bias'], html)
    html = re.sub(r'(?<=<div class="bias-asset">Gold \(XAU/USD\)</div>\n      <div class="bias-dir [^"]*">[^<]*</div>\n      <div class="bias-sub">)[^<]*', analysis['gold_reason'], html)

    # Indices cell
    html = re.sub(r'(?<=<div class="bias-asset">S&amp;P 500 / DAX</div>\n      <div class="bias-dir [^"]*">)[^<]*', analysis['indices_bias'], html)
    html = re.sub(r'(?<=<div class="bias-asset">S&amp;P 500 / DAX</div>\n      <div class="bias-dir [^"]*">[^<]*</div>\n      <div class="bias-sub">)[^<]*', analysis['indices_reason'], html)

    # Lead story - replace first <p> inside .lead-story
    html = re.sub(r'(<div class="lead-story">[\s\S]*?<p>)[^<]*(</p>)', r'\g<1>' + analysis['lead_story'] + r'\2', html, count=1)

    # Update last built timestamp
    html = re.sub(r'(<span id="lastBuilt">)[^<]*(</span>)', r'\g<1>' + updated_time + r'\2', html)

    with open('index.html', 'w') as f:
        f.write(html)

    print("Injected analysis into index.html successfully")
else:
    print("Skipping HTML injection due to error:", analysis.get("error"))

print("Done:", json.dumps(analysis, indent=2))
