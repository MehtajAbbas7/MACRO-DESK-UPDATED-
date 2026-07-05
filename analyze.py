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

analysis["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open('data/analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

def bias_class(bias):
    b = bias.lower()
    if 'bull' in b: return 'bull'
    if 'bear' in b: return 'bear'
    return 'neutral'

def replace_bias_cell(html, asset_label, bias, reason):
    # Find the bias-cell containing this asset label and replace dir + sub
    pattern = (
        r'(<div class="bias-asset">' + re.escape(asset_label) + r'</div>\s*'
        r'<div class="bias-dir)[^"]*(">[^<]*)(</div>\s*<div class="bias-sub">)[^<]*(</div>)'
    )
    cls = bias_class(bias)
    replacement = r'\g<1> ' + cls + r'\2'.replace(r'\2', '">' + bias) + r'\3' + reason + r'\4'
    # Simpler approach - use a function
    def replacer(m):
        return (
            '<div class="bias-asset">' + asset_label + '</div>\n      '
            '<div class="bias-dir ' + cls + '">' + bias + '</div>\n      '
            '<div class="bias-sub">' + reason + '</div>'
        )
    return re.sub(pattern, replacer, html, count=1)

if "error" not in analysis:
    with open('index.html', 'r') as f:
        html = f.read()

    html = replace_bias_cell(html, 'USD (DXY)', analysis['usd_bias'], analysis['usd_reason'])
    html = replace_bias_cell(html, 'Gold (XAU/USD)', analysis['gold_bias'], analysis['gold_reason'])
    html = replace_bias_cell(html, 'S&amp;P 500 / DAX', analysis['indices_bias'], analysis['indices_reason'])

    # Replace lead story first paragraph
    html = re.sub(
        r'(<div class="lead-story">.*?<p>)(.*?)(</p>)',
        lambda m: m.group(1) + analysis['lead_story'] + m.group(3),
        html, count=1, flags=re.DOTALL
    )

    # Update timestamp
    updated_time = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC (auto-generated)")
    html = re.sub(
        r'(<span id="lastBuilt">)[^<]*(</span>)',
        r'\g<1>' + updated_time + r'\2',
        html
    )

    with open('index.html', 'w') as f:
        f.write(html)

    print("Injected successfully")
else:
    print("Skipping injection, error:", analysis.get("error"))

print("Done:", json.dumps(analysis, indent=2))
print("Done:", json.dumps(analysis, indent=2))
