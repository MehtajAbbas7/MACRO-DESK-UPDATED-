# Macro Desk — free auto-update setup

This makes the headline-pulling part run on its own, for £0/month. Total setup time: ~15 minutes, one time.

## What this does
A GitHub Action wakes up every 3 hours, pulls fresh macro/forex headlines and an economic
calendar, and saves them into your repo as JSON files. Your site (hosted free on Vercel)
reads that JSON. No server, no credit card, no ongoing cost.

The "explain this to me" layer stays manual and free: open the site, then come back to
Claude and say "explain today's headlines" — I'll read the stored JSON and write the
breakdown, same as I did for this first version.

## Step 1 — Get a free NewsAPI key
1. Go to newsapi.org → Get API key → sign up free (100 requests/day, plenty for this)
2. Copy your API key

## Step 2 — Create a GitHub repo
1. Go to github.com → New repository → name it e.g. `macro-desk` → Public → Create
2. Upload these two files into it:
   - `macro-desk.html` → keep at the root, rename to `index.html`
   - `.github-workflows-fetch-headlines.yml` → put it at the exact path
     `.github/workflows/fetch-headlines.yml` (note: this is a folder structure,
     the dots in the filename I gave you were just so it could be attached as one file —
     rename and move it when uploading)

## Step 3 — Add your API key as a secret
1. In your repo: Settings → Secrets and variables → Actions → New repository secret
2. Name: `NEWSAPI_KEY`
3. Value: paste the key from Step 1
4. Save

## Step 4 — Turn on the workflow
1. Go to the Actions tab in your repo → you should see "Fetch macro headlines"
2. Click "Run workflow" once manually to test it
3. Check the `data/` folder appears with `headlines.json` and `calendar.json`
4. From now on it runs automatically every 3 hours, free, forever (GitHub Actions
   gives unlimited free minutes on public repos)

## Step 5 — Host it live and free on Vercel
1. Go to vercel.com → sign up with your GitHub account (free)
2. Import the `macro-desk` repo → Deploy (no config needed, it's a static site)
3. You'll get a real URL like `macro-desk-yourname.vercel.app`
4. Every time the GitHub Action commits new data, Vercel auto-redeploys — so the
   site is always showing the latest pulled headlines

## What you do day to day
1. Open your live URL — see fresh raw headlines + calendar (auto-pulled, no API cost)
2. Come back to Claude, paste in or describe what you're seeing, and ask for the
   explainer — that part is free because it's just a normal chat message to me
3. Optional: if you ever want it to feel fully automatic with zero manual step,
   that's the point where a small Claude API cost comes in (pennies/day) —
   not needed unless you want it

## If something breaks
- Action not running → check the secret name matches exactly `NEWSAPI_KEY`
- No data showing → check the Actions tab for a red X and open the log, it'll say why
- Vercel not updating → check it's watching the right branch (usually `main`)

Bring me the error message if you get stuck on any step — paste it here and I'll fix it with you.
