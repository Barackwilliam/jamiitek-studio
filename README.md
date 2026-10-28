# JamiiTek AI Marketing Studio

**An AI-powered marketing content creation platform that transforms website information into professional marketing assets.**

## 1. Project Overview

JamiiTek AI Marketing Studio is a planned AI-powered platform designed to help businesses turn their existing websites into high-quality marketing content.

Users will be able to provide a website URL, allow the platform to analyze relevant business information, and use that information to generate marketing concepts and creative assets.

The long-term vision is to support promotional videos, posters, images, advertising copy, voice-overs, social media content, and complete marketing campaigns through one flexible platform.

The product is intended to support businesses across different industries, website technologies, languages, and markets.

**Important:** This project is currently in the planning and specification stage. Features described in this README are goals, not claims that the features have already been implemented.

## 2. Vision

Build a powerful, accessible, and internationally competitive AI marketing studio that helps businesses create professional marketing content without requiring advanced design, video-editing, or marketing skills.

The platform should combine accurate business understanding, creative intelligence, flexible editing, reliable media generation, and an intuitive user experience.

## 3. Planned Core Capabilities

### Website Analysis

- Accept a website URL as the starting point, or let users enter business information manually.
- Identify relevant pages and extract useful business information.
- Understand products, services, brand identity, target audiences, and marketing objectives.
- Extract suitable images and other publicly accessible brand assets where permitted.
- Handle different website structures, including JavaScript-heavy websites and e-commerce platforms.
- Let users review or correct important information before content generation.

### AI Marketing Intelligence

- Develop marketing concepts based on verified website information.
- Generate promotional scripts, headlines, calls to action, and campaign ideas.
- Adapt creative direction to different industries and audiences.
- Support multiple languages and localized marketing content.
- Avoid inventing prices, testimonials, certifications, business facilities, or other unsupported claims.

### Creative Content Generation

The long-term product may support:

- Promotional and advertising videos.
- Marketing posters and images.
- Social media content.
- Advertising copy and captions.
- Voice-overs and narration.
- Subtitles and multilingual content.
- Campaign concepts and related marketing assets.

### Video Production

The planned video workflow combines authentic website assets, motion graphics, text animation, narration, music, captions, and AI-generated supplementary footage where appropriate.

Users should be able to preview their results and export suitable MP4 videos in formats such as:

- Vertical 9:16 for short-form social media.
- Horizontal 16:9 for websites and video platforms.
- Square 1:1 for supported social media placements.

### Editing and Customization

The platform should progressively support editing of scripts, scenes, images, narration, captions, branding, timing, and output settings.

Generated content should be reviewable before final export.

## 4. Guiding Principles

1. **Accuracy first:** Generated marketing content must remain grounded in available business information.
2. **Broad compatibility:** Website analysis should adapt to different technologies rather than depend on one website structure.
3. **Professional quality:** Outputs should be polished, coherent, and suitable for real marketing use.
4. **User control:** Users should be able to review and customize important creative decisions.
5. **Modular architecture:** AI and media providers should be replaceable where practical.
6. **Zero-budget start:** Build initially with free and open-source tools and free service tiers only, and verify each tool's license (see `docs/DECISIONS.md`, DEC-016). Keep providers replaceable so paid services can be added later if justified.
7. **Security by design:** Protect the platform, users, websites, files, credentials, and generated media.
8. **Incremental development:** Build, test, and verify capabilities in manageable stages.
9. **Honest reporting:** Never claim that an unimplemented or untested feature works.
10. **International readiness:** Design for multiple languages, markets, business types, and output formats.

## 5. Intended Technology Direction

The initial development direction is:

- **Backend:** Python and Django.
- **Frontend:** HTML, CSS, and vanilla JavaScript.
- **Initial database:** SQLite.
- **Future database option:** PostgreSQL.
- **Website analysis:** Playwright and Beautiful Soup where appropriate.
- **Video processing:** FFmpeg.
- **Version control:** Git and GitHub.
- **Development environment:** Windows and Visual Studio Code.

These are planned technical choices. All of them are free and open source. The actual repository structure, installed dependencies, and implemented components must be verified before setup instructions are finalized.

## 5A. Local Setup

**Requirements:** Python 3.10 or newer (tested with 3.12 and 3.13) and Git. No paid services are needed.

The project uses Django 5.2, a long-term support release.

**Windows (PowerShell):**

```powershell
git clone <repository-url> jamiitek-ai-marketing-studio
cd jamiitek-ai-marketing-studio
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

**Linux or macOS:**

```bash
git clone <repository-url> jamiitek-ai-marketing-studio
cd jamiitek-ai-marketing-studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. The health check is at <http://127.0.0.1:8000/health/>.

### Running the analysis worker

Website analysis runs in the background so pages stay responsive. Open a **second terminal**, activate the virtual environment the same way, and run:

```bash
python manage.py run_analysis_worker
```

Keep it running while you use the application; stop it with Ctrl+C. Without it, analyses stay at "Waiting to start". `python manage.py run_analysis_worker --once` processes whatever is queued and exits.

If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use `.venv\Scripts\activate.bat` from Command Prompt.

### Configuration

All settings come from environment variables. `.env.example` lists every variable with safe defaults for local development. Never commit `.env`.

`DJANGO_DEBUG` defaults to `False`. With debug off, the application refuses to start without `DJANGO_SECRET_KEY`, and it enables HTTPS-only cookies, HTTPS redirects, and HSTS.

### Using Supabase PostgreSQL

Without `DATABASE_URL`, the application uses a local SQLite file. To use Supabase instead (see `docs/DECISIONS.md`, DEC-018):

1. Create a project at supabase.com and keep the database password safe.
2. In the project, open **Connect** and copy the **Session pooler** connection string (port 5432). It works on ordinary IPv4 internet connections; the direct connection needs IPv6.
3. Put it in `.env` as `DATABASE_URL=...`, with your real password in place of `[YOUR-PASSWORD]`. If the password contains special characters such as `@`, `#` or `/`, URL-encode them.
4. Run `python manage.py migrate`. Row level security is switched on for every Django table automatically, so Supabase's Data API cannot read them.
5. Optionally, in the Supabase dashboard, turn off the Data API or stop exposing the `public` schema, because this application does not use it.

On Supabase's free plan, a project is paused after about a week without activity; restore it from the dashboard when that happens. Automated tests never connect to Supabase.

### Running checks and tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The workflow in `.github/workflows/tests.yml` runs the same checks on GitHub Actions, on SQLite and on PostgreSQL 16.

## 6. Development Roadmap

The proposed implementation sequence is:

1. Establish the project foundation and development environment.
2. Build secure website URL validation and analysis.
3. Extract and organize business and brand information.
4. Generate grounded marketing concepts and scripts.
5. Add configurable creative settings and user approval.
6. Integrate suitable image, audio, and video generation providers.
7. Build the video rendering and preview workflow.
8. Add editing, export, project saving, and history.
9. Improve reliability, security, testing, and performance.
10. Prepare deployment and progressively expand into additional marketing tools.

The roadmap may change as technical research, testing, and product decisions provide new evidence.

## 7. Security and Privacy

Website analysis must treat submitted URLs and retrieved website content as untrusted input.

Implementation should include appropriate protections against server-side request forgery (SSRF), unsafe redirects, private-network access, cloud metadata access, excessive downloads, malicious files, and resource exhaustion.

Browser automation and media processing should be isolated appropriately. API credentials must be stored securely and must not be exposed in frontend code, logs, or source control.

Only collect and retain the data necessary for the product's intended operation.

## 8. Project Documentation

Before making significant changes, AI coding assistants and developers should review the applicable project documentation, including:

- `AI_PROJECT_GUIDE.md` — Universal guidance for AI assistants.
- `PROJECT_MASTER.md` — Overall product vision and master specification.
- `AGENTS.md` — Instructions for AI coding and development agents.
- `docs/PROJECT_REQUIREMENTS.md` — Detailed functional and non-functional requirements.
- `docs/ARCHITECTURE.md` — Technical architecture and component boundaries.
- `docs/PROJECT_STATUS.md` — Verified implementation status.
- `docs/DECISIONS.md` — Important decisions and their rationale.
- `docs/TASKS.md` — Development tasks and priorities.
- `docs/TESTING.md` — Testing strategy and verification procedures.

Documentation must be kept consistent with the actual implementation.

## 9. Current Project Status

As of 2026-10-28, the following exist and are tested: user accounts, private projects (with a website address, manual business details, or both), website address safety checks against SSRF, website analysis of HTML websites (up to 8 relevant pages, respecting robots.txt, run by a background worker), and PostgreSQL/Supabase support with automatic row level security. Analysis has not yet been tried against real public websites. See `docs/PROJECT_STATUS.md` for the verified status.

The following items do not exist yet and must not be assumed to exist until they are verified in the repository:

- Business profiles built from the analysis, or browser automation for JavaScript-only websites.
- AI provider integrations.
- Image, audio, or video generation.
- Video rendering and exporting.
- File uploads and Supabase Storage.
- Deployment infrastructure.

As development progresses, update the project status documentation with implemented features, test results, known limitations, and the next development priorities.

## 10. Contributing and AI-Assisted Development

Anyone working on this project should:

- Inspect the existing repository before modifying files.
- Understand the relevant documentation and current implementation.
- Make focused, maintainable changes.
- Avoid unnecessary rewrites and unverified assumptions.
- Add or update tests for relevant functionality.
- Run appropriate checks and report their actual results.
- Update documentation when behavior, architecture, or decisions change.
- Preserve existing work and avoid exposing secrets.

## 11. Long-Term Goal

JamiiTek AI Marketing Studio aims to become a flexible, reliable, and high-quality marketing creation platform that enables businesses of different sizes to produce compelling marketing content from their existing digital presence.

The immediate priority is to establish a strong technical foundation, validate the product workflow, and deliver useful features incrementally without compromising security, accuracy, or quality.
