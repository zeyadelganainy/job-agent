# job-agent

A self-hosted, bring-your-own-keys (BYOK) job-application assistant. It finds jobs,
scores them against *your* profile, sends you a ranked shortlist in Telegram, and —
for the ones you pick — writes a tailored résumé and cover letter in your voice.
**You always apply manually.** Everything runs on your machine; your data never
leaves it.

```
scan  ─►  score  ─►  Telegram digest  ─►  you /pick 1 2 3  ─►  tailored docs  ─►  you apply
```

- **scan** – pull open roles from company ATS feeds (Greenhouse / Lever / Ashby) and,
  optionally, job boards.
- **score** – an LLM rates each role 0–100 against your profile, with reasons + gaps.
- **digest** – you get a numbered shortlist in Telegram, each with an Apply link.
- **/pick** – reply with the numbers you want; it generates a résumé + cover letter
  per job and sends the files back.
- **apply** – you review and submit. The tool never auto-applies.

---

## 1. What you need

- **Python 3.10+**
- A **Telegram** account (the digest + files come to you there)
- At least one **LLM API key**:
  - **Gemini** — free tier, good enough to start: https://aistudio.google.com/apikey
  - **Claude (Anthropic)** — paid, higher quality, *optional*:
    https://console.anthropic.com/settings/keys

Claude is used first when its key is set; otherwise it falls back to Gemini. You can
run **completely free on Gemini alone** by leaving the Claude key blank.

---

## 2. Quickstart

### 2.1 Install
```bash
pip install -r requirements.txt
```

### 2.2 Create a Telegram bot
1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the **bot token**.
2. Open a chat with your new bot and send it any message (e.g. `hi`).
3. Message [@userinfobot](https://t.me/userinfobot) → copy your numeric **chat ID**
   (a number like `6599293547`, **not** a `t.me/...` link).

### 2.3 Add your secrets
Copy the example env file and fill it in:
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
```ini
# .env  (gitignored — never committed)
ANTHROPIC_API_KEY=        # leave blank to run free on Gemini
GEMINI_API_KEY=your_gemini_key
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=6599293547
```

### 2.4 Set up your profile
Fill in the files under `profile/` — these are *you*, and they drive both scoring and
the generated documents. See [Your profile](#4-your-profile) for what each file does.
At minimum: `profile/profile.yaml` and `profile/master.md`.

### 2.5 Tell it what jobs to look for
Edit `config.yaml` — your target titles, locations, and the companies to watch. See
[Tailoring with config.yaml](#3-tailoring-with-configyaml).

### 2.6 Run it
```bash
python bot.py        # interactive: /scan, /list, /pick, /skip  (recommended)
# or
python run_scan.py   # one-off: scan + push a digest, then reply in the bot
```

---

## 3. Tailoring with `config.yaml`

This is where you point the agent at the jobs you want. Edit the file, then re-run a
scan. Each section:

### `search` — what and where
```yaml
search:
  keywords:                 # a role is kept if its title/description contains ANY of these
    - software engineer
    - backend engineer
    - new grad
  locations:                # a role is kept if its location text contains ANY of these
    - Canada                #   (case-insensitive substring match)
    - Vancouver
    - Toronto
    - Remote                # add this only if you want remote roles regardless of country
  remote_ok: true           # used by the job-board search
  max_age_days: 7           # ignore postings older than this (when a date is available)
```
- **keywords** are your filter for *which kinds of roles* to surface. Broaden to see
  more, narrow to see less. (This is a coarse text filter; the *fine* judgment of fit
  is done later by the scorer against your profile.)
- **locations** restrict by place. The Canadian set above keeps only Canadian roles.
  A role with no location listed is kept (you decide). Want one specific city? List
  just that city. Want anywhere? Leave `locations` empty.

### `sources` — where the jobs come from
```yaml
sources:
  ats:                      # public company feeds — the preferred, ToS-safe source
    greenhouse: [stripe, figma, wealthsimple, clio]
    lever: []
    ashby: [1password]
  boards:                   # job boards via JobSpy — optional, see the warning below
    enabled: false
    sites: [indeed, linkedin, zip_recruiter, google]
    results_per_site: 25
```
**ATS feeds are the heart of targeting** — they're how you watch specific companies.
Each company has a short **token**. Find it in the company's careers URL:

| Provider   | Careers URL looks like               | Token to use |
|------------|--------------------------------------|--------------|
| Greenhouse | `boards.greenhouse.io/stripe`        | `stripe`     |
| Lever      | `jobs.lever.co/figma`                | `figma`      |
| Ashby      | `jobs.ashbyhq.com/1password`         | `1password`  |

Add the companies you'd love to work at to the matching list. (Tip: try opening
`https://boards-api.greenhouse.io/v1/boards/<token>/jobs` in a browser — if you get
JSON, the token works.)

> **Job boards (`boards`) are off by default for a reason.** JobSpy scrapes Indeed /
> LinkedIn / etc., which is ToS-grey and can get your IP blocked. ATS feeds give you
> clean, public data with none of that risk. If you enable boards, also run
> `pip install python-jobspy` (otherwise they're silently skipped), and know the
> tradeoff.

### `scoring` — how picky, and how much to score
```yaml
scoring:
  threshold: 60        # only roles scoring >= this appear in the digest
  digest_size: 10      # max roles shown per digest
  max_to_score: 25     # cap NEW roles scored per scan (free-tier friendly); 0 = no cap
```
- Raise **threshold** to see only strong matches; lower it to cast a wider net.
- **max_to_score** stops a single scan from trying to score hundreds of roles at once
  (which would blow through free LLM limits). Anything not scored this run is picked up
  on the next scan, so running scans regularly works through your backlog.

### `models` — quality vs. cost
```yaml
models:
  claude: claude-opus-4-8    # primary (paid). Cheaper options: claude-sonnet-4-6, claude-haiku-4-5
  gemini: gemini-2.5-flash   # fallback (free tier)
```
Swap these freely. To run **free**, leave `ANTHROPIC_API_KEY` blank and it uses Gemini.
See [Models & cost](#6-models--cost).

### `llm` — rate-limit behavior (rarely need to touch)
```yaml
llm:
  max_retries: 5          # attempts per provider before giving up / falling back
  base_delay_seconds: 2   # exponential backoff base
  max_delay_seconds: 60   # cap on any single backoff wait
  max_tokens: 4096        # per-response output cap
  gen_delay_seconds: 3    # pause between document generations in one /pick batch
```

### `paths` — where files live (defaults are fine)
DB, output folder, and the four profile files.

---

## 4. Your profile

Four files under `profile/` describe you. They are **personal data and are gitignored**
— they never get committed. Each has a distinct job:

| File | Used for | What to put in it |
|------|----------|-------------------|
| **`profile/profile.yaml`** | **Scoring** every role | A compact, structured CV (identity, skills, experience, education). Small on purpose — it's sent on every score call, so keep it token-light. |
| **`profile/master.md`** | **Generating** résumés + cover letters | Your full "source of truth" — every role, project, bullet, and metric you might ever use. Longer than any one résumé; it's a *pool to select from*. The generator obeys instructions you put at the top (see below). |
| **`profile/samples/`** | **Voice** of the cover letter | 1–3 past cover letters or a bio as `.txt`/`.md`. The cover letter is written to match this tone. Skipping these makes the output sound generic. |
| **`profile/resume.docx`** | **Look** of the generated résumé | Your own polished résumé. The generator opens it as a **template** and reuses its fonts, margins, and layout, then fills in tailored content — so output looks like *your* résumé, not a generic one. |

**How they work together when you `/pick` a job:**
1. The LLM reads `master.md` and the job description, then selects/reorders/rephrases
   your real content into a one-page résumé (as structured data).
2. That content is rendered into a `.docx` styled like your `resume.docx` template
   (section rules, two-column layout, clickable links).
3. A cover letter is written from `master.md` facts in the voice of your `samples/`.

**About `master.md`:** the top of the file can hold agent instructions — truthfulness
rules ("never fabricate", "reproduce these numbers exactly"), what to lead with for
different role types, and a registry of immutable facts. The generator follows them,
and it will only include a project link if that exact URL appears in `master.md`
(no invented links).

> Keep `profile.yaml` and `master.md` factually identical. `profile.yaml` is the short
> version for quick scoring; `master.md` is the long version for writing.

---

## 5. Day-to-day use

Run `python bot.py` and talk to your bot:

| Command | What it does |
|---------|--------------|
| `/scan` | Find new roles, score them, and show a numbered shortlist. |
| `/list` | Re-show the roles currently waiting on your decision. |
| `/pick 1 3 4` | Generate a résumé + cover letter for those numbers; files are sent back. |
| `/skip 2 5` | Dismiss those numbers. |

The digest is **numbered** — reply with the numbers, not any IDs. Each entry shows the
match %, location, the scorer's reasoning, and an **Apply** link to the posting.

`run_scan.py` does a one-off scan and pushes a digest (handy for a daily cron / Task
Scheduler job); you then open the bot and `/pick`.

Generated files land in `output/<job_id>/`:
`resume.docx` (apply with this), `cover_letter.md`, and `resume.md` (a quick-read copy).

---

## 6. Models & cost

- **Free path:** leave `ANTHROPIC_API_KEY` blank → everything runs on Gemini's free
  tier. Great for trying it out. Caveats: the free tier has **daily request caps**
  (e.g. ~20/day on `gemini-2.5-flash`) and occasional `503` "high demand" errors. The
  built-in backoff retries those, but heavy use in one day can hit the wall —
  especially document generation, which is the most token-heavy step.
- **Reliable path:** set `ANTHROPIC_API_KEY` and use Claude. Cost scales with how many
  jobs you `/pick` (each is 2 LLM calls). Use `claude-sonnet-4-6` or
  `claude-haiku-4-5` in `config.yaml` to cut cost.
- A practical mix: score on the free tier, and set a Claude key so the *generation*
  step (where quality matters most) is dependable.

---

## 7. Honest notes & safety

- **It never auto-applies.** A human always does the final submit — deliberate, to
  keep you in control and avoid account bans.
- **ATS feeds are the safe primary source.** Job boards are optional, ToS-grey, and can
  get your IP blocked — see the warning in [`sources`](#sources--where-the-jobs-come-from).
- **Where your data goes:** your résumé is in every prompt. Anthropic does not train on
  API inputs/outputs. Gemini's **free** tier may use prompts to improve their models
  (the paid tier does not) — fine for personal use, just know it.
- This is a personal-use tool. If you grow it beyond yourself, read each source's ToS
  and handle other people's data responsibly.

---

## 8. Development

```bash
pip install -r requirements-dev.txt
pytest
```
The test suite is hermetic — no network, LLM, or Telegram calls. See `CLAUDE.md` for
the architecture and contributor conventions.

## Project layout
```
run_scan.py        # one-off scan -> digest
bot.py             # interactive Telegram bot
config.yaml        # search, sources, scoring, models  (you edit this)
profile/           # your data: profile.yaml, master.md, samples/, resume.docx  (gitignored)
jobagent/          # ingest/ (ats, boards, runner), score, generate, llm, store, pipeline
tests/             # pytest suite
```
