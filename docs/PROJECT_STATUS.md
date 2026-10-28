# Project Status — JamiiTek AI Marketing Studio

**Project:** JamiiTek AI Marketing Studio  
**Document:** Project Status and Progress Tracking  
**Version:** 1.1  
**Last Updated:** 2026-10-27  
**Overall Status:** Planning and Documentation  
**Budget constraint:** Zero budget (see `docs/DECISIONS.md`, DEC-016)

---

## 1. Purpose

This document tracks the verified implementation status of JamiiTek AI Marketing Studio.

It provides a shared reference for developers, AI coding assistants, testers, and project stakeholders so that work can continue consistently across different sessions and tools.

The purpose is to prevent:

- Repeating work that has already been completed.
- Assuming planned features are already implemented.
- Claiming tests passed when they were never run.
- Losing track of known problems and unfinished work.
- Making architectural changes without understanding existing decisions.
- Creating conflicting implementations of the same feature.

## 2. Current Project State

The product vision, initial requirements, and proposed architecture have been documented. Phases 1 to 5 are implemented and verified with automated tests, a local test website and a local stand-in for the AI service: Django foundation, accounts and projects, secure website analysis for HTML websites, a reviewable business profile, AI-written concepts and scripts based only on confirmed facts, a private image library with poster generation, and MP4 videos made from approved scripts. Analysis has not yet been tried against real public websites, AI writing has not yet been tried with a real provider, and Supabase Storage has not yet been tried with a real bucket. AI images, narration and video do not exist yet.

As of 2026-10-27, all planned documentation files exist and have been reviewed together for consistency:

| Document | Status |
|---|---|
| `AI_PROJECT_GUIDE.md` | Written; reviewed for consistency |
| `PROJECT_MASTER.md` | Written; reviewed for consistency |
| `AGENTS.md` | Written; reviewed for consistency |
| `README.md` | Written; reviewed for consistency |
| `docs/PROJECT_REQUIREMENTS.md` | Written; reviewed for consistency |
| `docs/ARCHITECTURE.md` | Written; reviewed for consistency |
| `docs/PROJECT_STATUS.md` | Written; this document |
| `docs/DECISIONS.md` | Written; reviewed for consistency |
| `docs/TASKS.md` | Written; reviewed for consistency |
| `docs/TESTING.md` | Written; reviewed for consistency |

**Important:** The code is on GitHub at `Barackwilliam/jamiitek-studio` (private). GitHub Actions jobs fail before any step runs, which points to an account-level setting or billing restriction rather than the code; the owner needs to read the job annotation (see section 5.1). No deployment exists, and no Supabase project has been connected yet.

### 2.1 Key decisions recorded so far

- **Zero budget (DEC-016):** The project must be built using only free and open-source software and free service tiers until this decision is revised.
- The first video workflow is recommended to animate authentic website assets with captions, with narration optional, because free narration and AI footage suitable for commercial use have not been verified.

## 3. Feature Implementation Status

Use the following status definitions consistently:

- **Not Started:** Implementation has not begun.
- **In Progress:** Work has begun but the acceptance criteria are not yet satisfied.
- **Implemented — Unverified:** Code exists, but sufficient verification has not been completed.
- **Implemented — Verified:** Implementation exists and the relevant verification has passed.
- **Blocked:** Progress depends on resolving a documented issue.
- **Deferred:** Intentionally postponed.
- **Needs Review:** Existing behavior or implementation requires inspection.

### Current Feature Register

| Feature | Status | Evidence or Notes |
|---|---|---|
| Product requirements | In Progress | Specification written (v1.1); open decisions remain |
| Technical architecture | In Progress | Proposed architecture written (v1.1), including zero-budget tooling candidates |
| Testing strategy | In Progress | `docs/TESTING.md` written; foundational tests exist |
| Repository creation | Implemented — Verified | `Barackwilliam/jamiitek-studio` on GitHub |
| Django application foundation | Implemented — Verified | See section 4.1 |
| Home page | Implemented — Verified | `/`; states honestly that no features are available yet |
| Health check | Implemented — Verified | `/health/`; database check, 503 on failure, no internal details |
| Continuous integration | Blocked | Workflow exists (SQLite and PostgreSQL jobs); GitHub stops the jobs before any step runs (see section 5.1) |
| User accounts | Implemented — Verified | Sign up, log in, log out (POST only), using Django authentication |
| PostgreSQL / Supabase support | Implemented — Verified locally | `DATABASE_URL`; tested on local PostgreSQL 16, not yet on a real Supabase project |
| Row level security for Supabase | Implemented — Verified | See section 4.2 |
| Project and user management | Implemented — Verified | Create, view, edit, delete; each user sees only their own projects |
| Secure URL validation | Implemented — Verified | `apps/website_analyzer/url_safety.py`; used when saving a project |
| Safe page fetching | Implemented — Verified | `apps/website_analyzer/fetch.py`; used by the crawler |
| Manual business details (FR-02A) | Implemented — Verified | A project can be saved without a website |
| Website analysis (HTML sites) | Implemented — Verified locally | Crawler, extraction, robots.txt, background worker and results page; see section 4.3 |
| JavaScript website analysis | Deferred | DEC-019 |
| Business profile extraction and review | Implemented — Verified locally | See section 4.4 |
| Source-grounded marketing scripts | Implemented — Verified locally | See section 4.5 |
| AI provider integration | Implemented — Unverified with a real provider | OpenAI-compatible adapter (DEC-021); tested with mocks and a local stand-in server |
| Image library (uploads and website images) | Implemented — Verified locally | See section 4.6 |
| Posters | Implemented — Verified locally | Template-based, no AI; see section 4.6 |
| AI image generation | Deferred | DEC-022 |
| Supabase Storage | Implemented — Unverified | Configured through `STORAGE_S3_*`; not tried with a real bucket |
| Speech and audio generation | Partial | User-uploaded music and voice-over supported; AI narration not available (OPEN-014) |
| Video rendering | Implemented — Verified locally | See section 4.7 |
| Editing and preview | Not Started | Requirements documented |
| MP4 export | Implemented — Verified locally | Download from the video page |
| Project history and persistence | Not Started | Data architecture proposed |
| Automated tests | In Progress | 304 tests passing on SQLite and PostgreSQL 16 |
| Login and sign-up rate limiting | Implemented — Verified | See section 4.8 |
| Content-Security-Policy | Implemented — Verified | See section 4.8 |
| Worker health monitoring | Implemented — Verified | `/health/` and admin |
| Script version history | Implemented — Verified | Restore requires new approval |
| Production deployment | Not Started | Hosting and infrastructure unconfirmed |

Update these statuses as soon as code is written and verified.

## 4. Verified Development Evidence

Every meaningful status update should be supported by evidence.

Examples of acceptable evidence include:

- A repository path containing the relevant implementation.
- A successful test run with the command and result recorded.
- A verified database migration.
- A reproducible manual test.
- A generated media file that has been checked for validity.
- A deployment check with a recorded result.
- A confirmed provider integration using a controlled test.

Statements such as "the feature should work," "the code looks correct," or "the AI generated the implementation" are not sufficient proof that a feature works.

For every important verification, record:

1. Feature or requirement tested.
2. Date of verification.
3. Test method or command.
4. Actual result.
5. Known limitations.
6. Relevant commit or file references, where available.

### 4.1 Verification record: Phase 1 foundation

**Date:** 2026-10-27  
**Environment:** Linux, Python 3.13.17, Django 5.2.18, python-dotenv 1.2.4  
**Files:** `manage.py`, `config/`, `apps/core/`, `templates/`, `static/`, `requirements.txt`, `.env.example`, `.github/workflows/tests.yml`

| Check | Command or method | Result |
|---|---|---|
| System checks | `python manage.py check` | Passed: no issues |
| Missing migrations | `python manage.py makemigrations --check --dry-run` | Passed: no changes detected |
| Automated tests | `python manage.py test` | Passed: 17 tests |
| Production settings | Test runs `check --deploy` with debug off | Passed. Only W005 (HSTS for subdomains) and W021 (HSTS preload) remain; both are deliberate opt-ins that depend on the real domain |
| Regression detection | `check --deploy` with HSTS disabled | Reports W004, which the test would treat as a failure |
| Missing secret key | Test starts Django with debug off and no key | Refused to start, as intended |
| Manual server test | `runserver` with `.env` copied from `.env.example`, then HTTP requests | `/` 200, `/health/` 200 with `no-store`, CSS 200, unknown URL 404, POST to `/health/` 403 (CSRF) |
| Layout | Playwright screenshots at 375px (light) and 1280px (dark) | No horizontal scrolling; content readable |
| Git hygiene | `git status --ignored` | `.env` and `db.sqlite3` are ignored |

**Known limitations:**
- Not yet verified on Windows.
- No Kiswahili translations exist yet; the template text is marked for translation.

### 4.2 Verification record: Phase 2 (accounts, projects, URL safety, Supabase support)

**Date:** 2026-10-27  
**Environment:** Linux, Python 3.13.17, Django 5.2.18, psycopg 3.3.6, dj-database-url 3.1.2, PostgreSQL 16

| Check | Command or method | Result |
|---|---|---|
| Automated tests on SQLite | `python manage.py test` | Passed: 84 tests (1 PostgreSQL-only test file skipped) |
| Automated tests on PostgreSQL 16 | Same command with `DATABASE_URL` pointing to a local PostgreSQL 16 server, connecting as a non-superuser role | Passed: 84 tests (1 SQLite-only test skipped) |
| Missing migrations | `python manage.py makemigrations --check --dry-run` | No changes detected |
| RLS after migrate | `migrate` on PostgreSQL, then counted tables without RLS | 0 of 11 tables without RLS |
| Data API protection | Granted `SELECT` on all tables to an `anon` role (as Supabase does), then queried as `anon` | `anon` read 0 projects, 0 users, 0 sessions while Django read its data normally |
| Negative control | Disabled RLS on the project table and queried as `anon` again | `anon` could read the project, proving the check is meaningful; RLS was then re-enabled |
| SSRF: unsafe addresses | Unit tests with a fake resolver (no real DNS) | Loopback, private, link-local/metadata, carrier-grade NAT, multicast, reserved, IPv6 equivalents, IPv4-mapped, 6to4 and NAT64 forms, decimal/hex/octal IPv4 forms, credentials in URLs, non-HTTP schemes and blocked hostnames are rejected |
| SSRF: redirects and rebinding | Local test server | Every redirect hop is revalidated; redirects to private hosts, cloud metadata and `file:` are blocked before connecting; the hostname is resolved once per hop and the connection uses the validated address |
| Fetch limits | Local test server | Timeouts, oversized responses (declared and streamed), compressed responses, non-HTML content, redirect loops and too many redirects are all refused with clear errors |
| Ownership | View tests | Another user's project returns 404 on view, edit and delete; edits and deletes of it have no effect |
| Browser flow | Playwright at 375 px: sign up, submit `http://169.254.169.254/latest/meta-data/`, then save with business details only | Metadata address rejected with a clear message; project saved; no horizontal scrolling |

**Defect found and fixed during verification:** an IP address typed directly into the URL was checked through the DNS resolver rather than on its own. With the real resolver this was still blocked, but the check now validates IP literals directly so it cannot depend on resolver behaviour. A regression test covers it.

**Known limitations:**
- Not yet tested against a real Supabase project (no connection string available in this environment).
- Login has no rate limiting yet (brute-force protection is still needed before public launch).
- Email addresses are not collected, so password reset is not available yet.
- Supabase Storage is decided but not implemented.

### 4.3 Verification record: Phase 3 (website analysis)

**Date:** 2026-10-28  
**Environment:** Linux, Python 3.13.17, Django 5.2.18, beautifulsoup4 4.15.0, PostgreSQL 16

| Check | Command or method | Result |
|---|---|---|
| Automated tests | `python manage.py test` on SQLite and on PostgreSQL 16 | Passed: 142 tests on each |
| Extraction | Unit tests on the fixture site and malformed HTML | Title, description, language, canonical, Open Graph, headings, main text (without scripts, styles, navigation or footer), images (no inline data), links (no mailto or nofollow) and JSON-LD extracted; broken HTML and invalid JSON-LD handled |
| Crawling | Unit tests with a fake fetcher, plus an end-to-end test with the real `safe_fetch` against a local server | Relevant pages first; external, file and low-value links skipped; duplicates fetched once; page, depth and time limits enforced; robots.txt honoured; failed pages recorded while the crawl continues |
| Jobs | Unit tests | One active analysis per project (also enforced by a database constraint); a worker claims each job once; interrupted jobs are marked failed; crashes are recorded without internal details |
| Full workflow | Fixture site served locally, analysis run through the worker code path, results viewed in a browser at 375 px | Result "partial": 4 of 5 pages analyzed, the missing page shown as HTTP 404, the robots-disallowed page shown as skipped; no horizontal scrolling; no images from the analyzed site are loaded |
| Real websites | Worker run against `https://example.com/` and `https://www.python.org/` | Not possible here: the development container has no direct DNS access. This exposed a defect, now fixed: an unreachable site was reported as a robots.txt refusal. It is now reported as unreachable, with a regression test |

**Known limitations:**
- Not yet tried against real public websites (needs the owner's computer or a deployed environment).
- JavaScript-only websites will show little or no content (Playwright deferred, DEC-019).
- Sitemaps are not used yet.
- The worker must be started separately (`python manage.py run_analysis_worker`).

### 4.4 Verification record: Phase 4 (business profile)

**Date:** 2026-10-28  
**Environment:** as in section 4.3

| Check | Command or method | Result |
|---|---|---|
| Automated tests | `python manage.py test` on SQLite and on PostgreSQL 16 | Passed: 176 tests on each |
| Suggestions | Unit tests | Business name, description, phone, email, address, opening hours, logo, social profiles, offerings and prices from structured data; description, name, sharing image and theme colour from the home page; phones and emails from page text; offerings from list lines on services pages only; duplicates merged with all evidence; share buttons, invalid colours, failed pages and dates are not suggested |
| No invention | Unit test with page text claiming an award, a certification and prices | No suggestions created |
| User decisions | Unit tests | After re-analysis: confirmed facts kept (and gain new evidence), rejected values not suggested again, user entries untouched, an edited value's original wording not suggested again, unreviewed suggestions replaced |
| Mutation check | Temporarily disabled the preservation logic | 3 tests failed as expected; logic restored |
| Ownership and safety | View tests | Other users' profiles and facts return 404 (including mixing a project ID with another user's fact ID); actions are POST only; website values are HTML-escaped |
| Full workflow | Fixture site analyzed through the worker code path, then the profile page used in a browser at 375 px | 17 sourced suggestions created automatically; confirm and reject worked; conflicting descriptions and logos flagged; no horizontal scrolling |

**Defect found and fixed during testing:** the "update suggestions" action crashed because `_` was used both for translations and as a throwaway variable in the same function.

**Known limitations:**
- Suggestions are rule-based. Businesses whose websites lack structured data will mostly get name, description and contact suggestions; products and services must often be added by hand.
- Prices are suggested only from structured data, never from free text.
- Brand colours come only from the `theme-color` meta tag.
- There is no "confirm all" action, deliberately, so each fact is reviewed.

### 4.5 Verification record: Phase 5 (AI concepts and scripts)

**Date:** 2026-10-28  
**Environment:** as in section 4.3

| Check | Command or method | Result |
|---|---|---|
| Automated tests | `python manage.py test` on SQLite and on PostgreSQL 16 | Passed: 224 tests on each |
| Provider adapter | Unit tests with a fake HTTP opener | Correct request and headers; JSON mode optional; 401/403, 429, 4xx, 5xx, network errors and timeouts mapped to user-safe errors; one retry only for server and network errors; truncated, empty, malformed and oversized answers rejected; API key never logged |
| Grounding | Unit tests | Only confirmed facts reach the prompt (a suggested price and a rejected "award" did not); user notes are labelled as not facts; the system prompt tells the AI to ignore instructions inside data |
| Claim checks | Unit tests | Numbers not in confirmed facts flagged with exact matching ("15" is flagged even if "15000" is a fact); risky phrases flagged in English and Kiswahili with whole-word matching; phrases present in facts not flagged; unknown fact references flagged and removed |
| Failures | Unit tests | Unusable answers retried once then failed cleanly; quota exhaustion and missing configuration explained; brief and earlier drafts kept |
| Ownership | View tests | Other users get 404 on every content page and action; no jobs created |
| Full workflow | Local stand-in for an OpenAI-compatible API, the real worker, and a browser at 375 px | 3 concepts written; script written with "Based on" sources per scene; "bora zaidi" flagged; approval refused until the claim box was ticked, then approved; no horizontal scrolling |

**Defects found and fixed during testing:** numbers from different facts were joined when checking claims; a repeated fact reference was reported as unknown.

**Known limitations:**
- Not tried with Gemini or Groq: no key is available here and the development container cannot reach those services. JSON mode support on Gemini's compatibility endpoint is unverified (it can be turned off).
- Claim checks are word and number rules. They catch common unsupported claims but not every possible one; human approval remains essential.
- Concepts cannot be edited (choose one and edit the script).
- Remaining free quota is not shown.

### 4.6 Verification record: Phase 6 (images and posters)

**Date:** 2026-10-28  
**Environment:** as in section 4.3, plus Pillow 13.0.0 and django-storages 1.14.6

| Check | Command or method | Result |
|---|---|---|
| Automated tests | `python manage.py test` on SQLite and on PostgreSQL 16 | Passed: 258 tests on each |
| Image validation | Unit tests | JPEG, PNG, WebP and GIF accepted; empty files, text, HTML, SVG, PHP disguised as JPEG, truncated JPEG, BMP, too small, too wide and a 90-megapixel decompression bomb rejected; EXIF camera and GPS data removed; orientation applied; large images scaled down |
| Uploads | View tests | Random storage names (a `../../etc/passwd.jpg` upload name is not used); rights confirmation required; size limit enforced |
| Private files | View tests | Files stream only to the owner, with `nosniff` and private caching; other users get 404, including when mixing their project ID with someone else's asset ID; unknown URL variants are not routed |
| Clean-up | View tests | Deleting an image, a poster or a whole project removes the stored files |
| Website images | Unit tests with a fake fetcher | Only images found by the analysis can be imported (a metadata address was dropped); robots.txt honoured; non-images rejected; duplicates detected |
| Posters | Unit tests and visual checks | Exact sizes for 1:1, 9:16 and 16:9; long text shrinks to fit; text contrast at least 8.7:1 even on a pure white photo (measured); button text contrast at least 4.5:1 for any brand colour; claims checked against confirmed facts |
| Full workflow | Browser at 375 px | Photo and logo uploaded; poster made from an approved script with text prefilled; 1080×1080 JPEG displayed and downloadable; no horizontal scrolling |

**Defect found and fixed during development:** in the first poster layout, headline text could sit on bright parts of the photo; the shading now starts just above the measured text block.

**Known limitations:**
- Supabase Storage not tried with a real bucket.
- One poster layout; the logo is always in the top-left corner.
- Images cannot be cropped or edited in the application.

### 4.7 Verification record: Phase 7 (videos)

**Date:** 2026-10-28  
**Environment:** as in section 4.3, plus FFmpeg 6.1.1 (Linux)

| Check | Command or method | Result |
|---|---|---|
| Automated tests | `python manage.py test` on SQLite and on PostgreSQL 16 | Passed: 283 tests on each; render tests make real (tiny) videos with FFmpeg |
| Output checks | Unit tests | Every finished video is checked with FFprobe (MP4, one H.264 stream, exact size, yuv420p, duration within 0.6 s, sound present only when expected) and fully decoded; tests confirm the checks catch a wrong size, missing sound, wrong duration, a half-written file and a non-video file |
| Safety | Unit tests | FFmpeg runs without a shell and never receives user text (text is drawn into images); hostile text such as `'; rm -rf /` renders harmlessly; a missing FFmpeg is reported clearly |
| Audio | Unit tests | M4A, WAV and OGG accepted and re-encoded to AAC without tags; images, text, recordings under 1 s or over 10 minutes rejected |
| Timing | Unit tests | Scene lengths, the total length and voice-over length are checked before queueing |
| Jobs | Unit tests | One render at a time per project; deleted images fall back to the brand colour; failures recorded without internal details; temporary folders removed |
| Ownership | View tests | Other users get 404 on every video and audio page and file; only approved scripts and the user's own images can be used; unfinished videos are not served |
| Full workflow | Browser at 375 px, real worker | 31.5 s portrait video from an approved script: preview 540×960 ready in about 11 s, final 1080×1920 in about 47 s (on this development machine; an 8 GB laptop will be slower); both play in the browser |

**Known limitations:**
- No AI narration (OPEN-014); users can upload their own recording.
- Text is static on screen; motion is a slow zoom and cross-fades.
- The browser player cannot seek before the video has loaded (no HTTP range support yet).
- Not yet tried on Windows.

### 4.8 Verification record: Phase 8 (reliability and security)

**Date:** 2026-10-28  
**Environment:** as in section 4.7

| Check | Command or method | Result |
|---|---|---|
| Automated tests | `python manage.py test` on SQLite and on PostgreSQL 16 | Passed: 304 tests on each |
| Log-in limits | Unit tests | Locked after 5 failures even with the right password; same message for unknown usernames; other users unaffected; 20 attempts across usernames from one address locked; success clears failures; lock expires after 15 minutes; only hashes stored |
| Mutation check | Raised the limits so they could never trigger | 3 rate-limit tests failed as expected; limits restored |
| Sign-up limit | Unit test | 11th attempt from one address in an hour refused with HTTP 429 |
| Security headers | Unit test and browser | Strict CSP without `unsafe-inline`; 15 application pages and the admin pages loaded in a browser with no CSP violations |
| Range requests | Unit tests and browser | Partial content for start, open-ended, suffix and oversized ranges; 416 for impossible ranges; ownership still enforced; seeking to 25 s in a 31.5 s video worked in the browser |
| Worker | Unit tests | An exception in one job type is logged and the worker continues; heartbeat records errors; health shows `not_seen`, `ok` and `stale` |
| Cleanup | Unit tests | Dry run deletes nothing; `--delete` removes old orphan files and the application's own old temporary folders, keeps referenced files, recent files and unrelated folders |
| History and retry | Unit tests | Edits keep the previous version; restore needs new approval; history capped at 20; failed videos can be retried with the same settings |

**Defects found and fixed during testing:**
- The first `cleanup` version matched any temporary folder starting with `jamii-`; a dry run showed it would have deleted an unrelated folder. The application now uses a dedicated `jamiitek-tmp-` prefix.
- `cleanup` could have removed a file saved a moment before its database row; files changed in the last hour are now kept.
- The worker closed database connections inside transactions (seen only on PostgreSQL in tests); it now skips that inside a transaction.

**Known limitations:**
- Rate limits use the connecting address; behind a proxy this must be configured (README).
- Exports never expire automatically.

## 5. Current Blockers and Open Questions

The following items must be resolved or investigated as implementation progresses.

### 5.1 Repository and Environment

- GitHub Actions jobs stop before any step runs. The owner should open the failed run on GitHub and read the annotation; the usual causes are a billing or spending-limit problem on the account, or Actions being disabled. Making the repository public would also make Actions free without limits.
- Create a Supabase project and test the application against it using the session pooler connection string.
- Confirm the setup steps on the owner's Windows computer.
- Confirm that FFmpeg can be installed on the development computer (needed later, not for Phase 1).

### 5.2 Product Decisions

The following choices remain open unless explicitly decided in the project discussion:

- Initial product scope and launch priorities.
- Which free AI options to use for text and speech (budget is decided: zero, DEC-016).
- Supported languages and launch markets (Kiswahili and English proposed).
- Initial editing capabilities.
- Website crawl limits and page-selection workflow.
- User access, subscription, and usage-limit policies.
- Initial deployment environment.

These questions should be resolved deliberately and documented. AI coding assistants must not silently invent final decisions.

### 5.3 Technical Validation

- Confirm the best initial approach to safe website analysis.
- Evaluate when Playwright is necessary.
- Choose a suitable background-processing strategy when needed.
- Validate the proposed media-rendering workflow.
- Establish test fixtures and security tests.
- Define the first end-to-end workflow before expanding the feature set.

## 6. Immediate Priorities

The next development priorities should be completed in order, adjusting the sequence when repository inspection reveals a necessary change.

### Priority 1 — Finish the Planning Documents

- [x] Create `docs/DECISIONS.md`.
- [x] Create `docs/TASKS.md`.
- [x] Create `docs/TESTING.md`.
- [x] Check that all documents agree on product goals and technical direction (consistency review completed 2026-10-27).
- [x] Record the budget decision (DEC-016: zero budget).

### Priority 2 — Create the Repository

- [x] Create a local Git repository and commit the documentation with `.gitignore` and `.gitattributes`.
- [x] Create the GitHub repository and push.
- [ ] Confirm that GitHub Actions runs and passes (blocked; see section 5.1).
- [ ] Record the owner's development environment (Windows, Python version).

### Priority 3 — Establish a Minimal Working Foundation

- [x] Create the Django project (Django 5.2 LTS, DEC-017).
- [x] Confirm the application starts locally (verified on Linux; Windows pending).
- [x] Establish a repeatable development environment.
- [x] Configure the initial database.
- [x] Add a basic health or application availability check.
- [x] Add foundational tests.
- [x] Document exact setup and run commands.

### Priority 4 — Build the First End-to-End Feature

Implement a small but complete workflow before attempting the entire platform.

The proposed first milestone is:

1. Create a marketing project.
2. Submit a public website URL.
3. Validate the URL securely.
4. Analyze a controlled test website.
5. Display extracted business information.
6. Allow the user to review and correct the information.
7. Save the results.
8. Test the workflow and its failure cases.

This milestone should establish the website-analysis foundation before image and video generation are introduced. It needs no AI service at all, so it can be completed fully at zero cost.

## 7. Current Known Risks

| Risk | Required response |
|---|---|
| Unsupported business claims | Ground generated content in verified information and user approval |
| SSRF and unsafe website access | Implement layered URL and network protections |
| Free-tier limits change or a free tier closes | Keep providers replaceable (DEC-011), track quotas, fail gracefully, and keep a no-AI fallback where practical |
| Free tools with restrictive licenses | Verify and record the license of every model, voice, font, and music track before use |
| Free hosting too weak for rendering | Develop and demonstrate locally first; do not depend on free hosting for rendering or persistent files |
| Business data sent to free tiers that use it for training | Inform users and avoid sending private data to such services |
| Website compatibility failures | Support graceful failures and page-level diagnostics |
| Expensive video rendering | Use resource limits and background processing when appropriate |
| Lost user edits | Save edits reliably and define versioning behavior |
| Inconsistent AI coding sessions | Require documentation review and status updates |
| False implementation claims | Require test results or other verifiable evidence |
| Growing architectural complexity | Implement incrementally and justify new components |

## 8. Rules for Updating This Document

Update this document whenever:

- A major feature changes status.
- A milestone is completed.
- A blocker is discovered or resolved.
- An important test result changes.
- A dependency or infrastructure decision affects implementation.
- A release is prepared.
- A feature is deferred or removed.

Do not mark a feature as verified based solely on the existence of code.

If a feature is only partially implemented, record the completed portion and the outstanding acceptance criteria.

When evidence is unavailable, explicitly state that the status is unknown or unverified.

## 9. Development Session Handoff

At the end of each meaningful development session, record:

### Work Completed
List the actual changes made.

### Files Changed
List the important files created, modified, or removed.

### Verification
List the commands or manual tests performed and their actual outcomes.

### Outstanding Problems
Describe errors, blockers, and known limitations.

### Next Steps
Identify the next small, actionable tasks.

### Git Status
Record whether changes were committed and whether uncommitted work remains. Never claim a commit or push occurred without verifying it.

## 10. Definition of Project Progress

Progress should be measured by working, tested, documented capabilities rather than the number of files created, the size of the codebase, or the number of AI services connected.

The immediate goal is to establish a secure, testable foundation and deliver a working website-to-marketing-content workflow.

**Final rule:** This document is the shared progress record, but the actual repository, executed tests, and verified behavior remain the ultimate source of truth.
