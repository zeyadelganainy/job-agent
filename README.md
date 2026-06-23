# job-agent (V1)

A free, self-hosted job-application assistant. You bring your own API keys (BYOK),
run it on your own machine, and your data never leaves it.

**The loop:** `/scan` pulls jobs from company ATS feeds + job boards, an LLM scores
each one against your profile, and you get a ranked digest in Telegram. You reply
`/pick 3 7 12` and it generates a tailored resume + cover letter (in your voice)
for each, and sends the files back. You apply manually.

```
scan  ──►  score  ──►  digest to you  ──►  you /pick  ──►  generate docs  ──►  you apply
```

## Why BYOK / self-host
You bring your own keys, so usage is billed to **you**, not a shared instance — and
your resume data stays on your machine. Claude (Anthropic) is the primary model for
quality; Gemini's free tier is the fallback. Cost scales with how many jobs you
`/pick` (each generates a tailored resume + cover letter). Keep it cheap by using a
smaller Claude model (`claude-sonnet-4-6` / `claude-haiku-4-5` in `config.yaml`), or
rely on the free Gemini fallback by leaving `ANTHROPIC_API_KEY` unset.

## Setup

1. **Python 3.10+**, then:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get API keys:**
   - Claude (primary, paid BYOK): https://console.anthropic.com/settings/keys
   - Gemini (fallback, free tier): https://aistudio.google.com/apikey
   - Telegram bot token: message [@BotFather](https://t.me/BotFather), `/newbot`
   - Your Telegram chat ID: message [@userinfobot](https://t.me/userinfobot)

   You can run on Gemini alone (free) by leaving `ANTHROPIC_API_KEY` unset — the code
   falls back to Gemini automatically.

3. **Copy and fill the env file:**
   ```bash
   cp .env.example .env   # then edit
   ```

4. **Fill in `profile/profile.yaml`** with your real details, and drop 1–3 past
   cover letters / a bio into `profile/samples/` (any `.txt`/`.md`). These are what
   make the output "sound like you" — don't skip them.

5. **Edit `config.yaml`**: your keywords, locations, the ATS companies you're
   targeting, and which boards to pull from.

## Run

Two entry points:

```bash
# One-off scan from the terminal (ingest -> score -> push digest to Telegram)
python run_scan.py

# Long-running bot: /scan, /list, /pick, and receive generated docs
python bot.py
```

Generated resumes and cover letters land in `output/<job_id>/`.

## A few honest notes
- **Job-board scraping** (via JobSpy) is convenient but sits in legally grey, ToS-violating
  territory and can get your IP blocked. The cleanest source is **ATS feeds**
  (Greenhouse / Lever / Ashby) — public JSON, no scraping. Lean on those; treat boards as
  a bonus. Configure which sources you use in `config.yaml`.
- **Where your resume data goes.** Your resume is in every prompt. Anthropic does not
  train on API inputs/outputs. Gemini's **free** tier may use your prompts to improve
  their models — fine for personal use, just know it (the paid Gemini tier does not).
- This is a personal-use tool. If you grow it beyond yourself, read each source's ToS and
  think about handling other people's data properly.
