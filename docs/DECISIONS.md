# Architecture and Product Decisions — JamiiTek AI Marketing Studio

**Document:** Decision Log  
**Version:** 1.1  
**Status:** Initial Draft  
**Last Updated:** 2026-10-27

Decisions DEC-001 to DEC-015 were recorded during initial planning on 2026-10-27. Later decisions carry their own dates.

## 1. Purpose

This document records important product, architecture, security, and development decisions for JamiiTek AI Marketing Studio.

It provides a shared record for developers, AI coding assistants, and project stakeholders.

The decision log exists to:

- Preserve important decisions across development sessions.
- Explain why decisions were made.
- Prevent conflicting recommendations from different AI assistants.
- Identify decisions that are final versus provisional.
- Record changes when new evidence justifies a different approach.

**Important:** A proposed decision must not be treated as finalized unless its status explicitly indicates that it has been accepted.

## 2. Decision Status Definitions

Use these statuses consistently:

- **Proposed:** Suggested but not yet approved.
- **Accepted:** Approved for implementation.
- **Provisional:** Accepted temporarily and subject to evaluation.
- **Under Review:** Being reconsidered.
- **Superseded:** Replaced by a newer decision.
- **Rejected:** Considered and explicitly declined.

## 3. Accepted Decisions

### DEC-001: Build a Unified AI Marketing Studio

**Status:** Accepted

**Decision:** The product should develop toward an integrated marketing content creation platform rather than remain limited to a single-purpose video generator.

**Reasoning:** Businesses may need videos, posters, images, advertising copy, voice-overs, social media content, and related campaign materials. A unified platform can provide a more consistent workflow.

**Implementation implications:**
- Start with a clearly defined core workflow.
- Design reusable components where practical.
- Add additional content types incrementally.
- Avoid implementing every possible feature before the core workflow works.

### DEC-002: Prioritize Accuracy of Business Information

**Status:** Accepted

**Decision:** Generated marketing content must be grounded in available website evidence, user-provided information, or explicitly approved assumptions.

**Reasoning:** Invented prices, certifications, product features, testimonials, and other business claims can mislead customers and damage trust.

**Implementation implications:**
- Keep extracted facts distinguishable from AI-generated suggestions.
- Preserve source information for important claims where practical.
- Let users review and correct business profiles.
- Avoid presenting uncertain information as verified.

### DEC-003: Support Diverse Website Technologies

**Status:** Accepted

**Decision:** Website analysis should adapt to different website architectures instead of relying on a single HTML structure.

**Reasoning:** Target websites may use traditional HTML, content management systems, JavaScript frameworks, online-store platforms, or custom implementations.

**Implementation implications:**
- Combine appropriate retrieval and extraction strategies.
- Use browser automation when justified.
- Handle inaccessible or unsupported pages gracefully.
- Avoid promising universal compatibility without testing.

### DEC-004: Build Incrementally and Verify Honestly

**Status:** Accepted

**Decision:** Develop the system in manageable stages, and report implementation status based on actual evidence.

**Reasoning:** A large AI-generated codebase can appear complete while containing untested workflows, placeholders, or incompatible components.

**Implementation implications:**
- Inspect the repository before changing it.
- Implement small, coherent features.
- Add and run appropriate tests.
- Record known limitations.
- Never claim a feature works without suitable verification.

### DEC-005: Security Is a Core Requirement

**Status:** Accepted

**Decision:** Security must be incorporated into website analysis, authentication, file handling, AI integrations, background processing, and export delivery from the beginning.

**Reasoning:** The platform will process external URLs, untrusted content, uploaded assets, generated files, and potentially sensitive credentials.

**Implementation implications:**
- Protect against SSRF and unsafe redirects.
- Validate uploaded and retrieved files.
- Enforce server-side authorization.
- Protect API credentials.
- Isolate browser automation and resource-intensive processing where appropriate.

### DEC-011: Provider-Independent AI Integrations

**Status:** Accepted

**Decision:** Keep external AI and media providers behind modular internal interfaces where practical.

**Reasoning:** Provider capabilities, quality, cost, availability, and commercial terms can change. Under the zero-budget decision (DEC-016), free tiers are especially likely to change or disappear, so switching providers must be cheap.

**Implementation implications:**
- Separate provider adapters from core business logic.
- Document capability differences.
- Support configuration and graceful error handling.
- Avoid unnecessary abstraction when only one simple integration exists.

### DEC-016: Zero-Budget Development

**Status:** Accepted

**Date:** 2026-10-27

**Context:** The project owner has decided to start with no budget for paid services. This resolves OPEN-003.

**Decision:** Until this decision is explicitly revised, the project must be buildable, testable, and demonstrable without paying for any software, API, hosting, or media license.

**Rules:**
1. Use free and open-source software, or free tiers of hosted services, only.
2. Do not add a service that requires a payment card to function, unless the owner explicitly approves it.
3. Before adopting any free tool, model, voice, font, image, or music track, verify its current license and terms and record the result. "Free to download" does not mean "free for commercial use".
4. Treat free tiers as unreliable: they can change limits, add charges, or close. Every hosted AI feature must fail gracefully when its quota is exhausted or the service disappears.
5. Do not send private or sensitive user data to a free tier whose terms allow the provider to use submitted content for training or product improvement, unless the user has been clearly informed. Public website content is lower risk but must still be considered.
6. Prefer approaches that need no AI at all where they produce acceptable results, such as template-based posters, website images instead of generated images, and captions instead of narration.
7. Automated tests must never require a paid service or consume a hosted free-tier quota.
8. Paid services may be added later only through a new recorded decision, and only behind the provider interfaces required by DEC-011.

**Reasoning:** A zero-budget start lowers financial risk while the core workflow is validated. The modular architecture means paid providers can be added later without a rewrite.

**Alternatives considered:**
- Mixed free and paid providers. Rejected for now because no budget is available.
- Quality-first with cost controls. Deferred until the product shows evidence of user value.

**Consequences:**
- Initial output quality, speed, and language coverage will be limited by free tools. This must be communicated honestly to users.
- Kiswahili narration and high-quality AI image or video generation may be unavailable or restricted at zero cost. The first video workflow must therefore work with authentic website assets, text animation, and captions, with narration optional.
- Free hosting has tight memory, CPU, and storage limits. Playwright and FFmpeg rendering may not run reliably on free hosting, so development and demonstrations should start locally.
- Free-tier rate limits require quota tracking, caching, and avoidance of unnecessary regeneration.

**Review conditions:** Revisit when the project has funding, paying users, or evidence that a specific paid service is required for acceptable quality.

See `docs/ARCHITECTURE.md`, section 17, for the candidate zero-budget tools and their verification status.

## 4. Provisional Technical Decisions

### DEC-006: Initial Backend Framework

**Status:** Provisional

**Decision:** Use Python and Django as the initial backend direction.

**Reasoning:** Django provides a structured web framework, database integration, authentication facilities, migrations, and an established development ecosystem.

**Review conditions:** Reconsider only if repository inspection or concrete technical requirements demonstrate that Django is unsuitable.

### DEC-017: Django 5.2 LTS and a Single Environment-Driven Settings Module

**Status:** Accepted

**Date:** 2026-10-27

**Context:** Phase 1 required choosing a Django version and a settings layout.

**Decision:**
- Use Django 5.2, the current long-term support release (security updates until April 2028), pinned as `Django>=5.2,<5.3`.
- Use one settings module, `config/settings.py`, that reads all environment-specific values from environment variables, with `python-dotenv` loading an optional local `.env` file.
- `DJANGO_DEBUG` defaults to `False`, and the application refuses to start without `DJANGO_SECRET_KEY` when debug is off.

**Reasoning:** An LTS release reduces forced upgrades for a small team with no budget. A single environment-driven settings file is simpler than the `config/settings/` package shown as a possible structure in `docs/ARCHITECTURE.md`, while still separating configuration from code. Defaulting to debug off means a forgotten setting fails safely.

**Alternatives considered:**
- Django 6.x: newer features but a shorter support window.
- A `config/settings/` package with separate development and production modules: more files without a current need.
- No `.env` support: fewer dependencies, but harder local setup on Windows.

**Review conditions:** Plan the upgrade to the next LTS release before April 2028. Split settings into a package only if the environments diverge substantially.

### DEC-007: Initial Frontend Approach

**Status:** Provisional

**Decision:** Begin with HTML, CSS, Django templates, and vanilla JavaScript rather than introducing React immediately.

**Reasoning:** A simpler initial frontend can reduce setup complexity and help focus development on validating the core product workflow.

**Implementation implications:**
- Keep frontend interactions organized.
- Avoid unnecessary JavaScript complexity.
- Reconsider a frontend framework only when the product's interaction requirements justify it.

### DEC-008: Initial Database

**Status:** Provisional

**Decision:** Use SQLite for early local development, with PostgreSQL as a possible production or scaling option.

**Reasoning:** SQLite simplifies initial setup. PostgreSQL may become more suitable as concurrency, deployment, and operational requirements increase.

**Review conditions:** Reassess before production deployment or when database requirements exceed the initial approach.

### DEC-009: Website Analysis Tools

**Status:** Provisional

**Decision:** Evaluate Beautiful Soup for HTML extraction and Playwright for JavaScript-rendered websites.

**Reasoning:** Ordinary HTML parsing is often sufficient for some websites, while browser automation may be necessary for others.

**Implementation implications:**
- Prefer the least resource-intensive method that works.
- Apply strict URL, network, and resource protections.
- Test with representative websites before finalizing crawler behavior.

### DEC-010: Video Processing

**Status:** Provisional

**Decision:** Evaluate FFmpeg as the initial media-processing and video-rendering tool.

**Reasoning:** A dedicated media-processing engine can combine images, clips, audio, subtitles, and other components into exportable video.

**Review conditions:** Validate codec support, deployment compatibility, rendering quality, and resource requirements through working prototypes.

### DEC-012: Windows and Visual Studio Code Development

**Status:** Provisional

**Decision:** Use Windows and Visual Studio Code as the initial development environment.

**Reasoning:** This matches the intended development workflow.

**Implementation implications:**
- Document environment setup.
- Avoid unnecessary operating-system-specific assumptions.
- Validate command-line and media-processing workflows in the supported environment.
- Most hosting environments, including free ones, run Linux. Use `pathlib` for paths, avoid Windows-only commands in application code, and test media workflows on Linux before deployment.

**Hardware (recorded 2026-10-27):** The owner develops on a Dell laptop with Windows 11 and 8 GB of RAM. Consequences:
- Windows and the browser use a large share of 8 GB, so local AI models (for example through Ollama) are impractical except very small ones whose quality, especially in Kiswahili, is unlikely to be acceptable. Prefer a hosted free tier for text generation (OPEN-013).
- Docker Desktop and similar heavy tools are avoided; the project runs with Python and a virtual environment only.
- Playwright may be used, but with one browser and one page at a time, and only for pages that need JavaScript.
- FFmpeg rendering must use short, low-resolution previews during development, with bounded concurrency.
- Database work does not need local resources, because PostgreSQL runs on Supabase (DEC-018) and tests use SQLite.

### DEC-019: Website Analysis Design for Phase 3

**Status:** Accepted

**Date:** 2026-10-28

**Decision:**
- Analyze HTML with Beautiful Soup using Python's built-in `html.parser`, which needs no compiled extension and installs cleanly on Windows.
- Crawl politely: honour `robots.txt` (RFC 9309, including treating an unreachable robots.txt as "do not crawl"), wait at least 1 second between requests (more if `Crawl-delay` asks, up to 10 seconds), and limit each analysis to 8 pages, depth 2 and 120 seconds by default.
- Prefer pages whose links mention about, services, products, prices, contact and similar words in English and Kiswahili.
- Run analyses in a background worker started with `python manage.py run_analysis_worker`, using the database as the job queue. No Redis or Celery (DEC-016, DEC-012).
- Store only observed content. Nothing is inferred or summarized in this phase, and website text is displayed as plain text.
- Do not load the analyzed site's images in our pages; list their addresses instead. This avoids leaking users' IP addresses to third-party sites and avoids mixed content.
- **Defer Playwright.** JavaScript-only websites will produce little content for now. A headless browser uses several hundred megabytes per page, which is significant on the 8 GB development laptop, and needs careful network isolation (TASK-037, TASK-038). It will be reconsidered when real-site testing shows how many target websites need it.

**Review conditions:** Revisit page limits and Playwright after testing against real websites from target industries.

### DEC-018: Supabase for PostgreSQL and File Storage

**Status:** Accepted (database implemented; storage decided, not yet implemented)

**Date:** 2026-10-27

**Context:** The owner chose Supabase for the PostgreSQL database and a Supabase Storage bucket for images. This resolves the database part of OPEN-009 and supports DEC-016 (zero budget) through Supabase's free plan.

**Decision:**
- Django connects to Supabase PostgreSQL directly with `psycopg` through `DATABASE_URL`. Django does not use Supabase's Data API (REST), Supabase Auth, or `supabase-py`; Django's own authentication remains in use.
- Use the **session pooler** connection string (port 5432) for the long-running Django server, because it works on IPv4 networks. Supabase's direct connection is IPv6-only unless a paid add-on is bought. The transaction pooler (port 6543) is supported through `DJANGO_DB_TRANSACTION_POOLER=True`, which disables server-side cursors and prepared statements, but it is intended for serverless workloads.
- TLS is required for database connections (`DJANGO_DB_SSL_REQUIRE=True`).
- **Row level security is enabled automatically on every Django table after each migration** (`apps/core/db_security.py`). Supabase exposes tables in the `public` schema to its `anon` and `authenticated` roles through the Data API. With RLS enabled and no policies, those roles can read nothing, while Django is unaffected because PostgreSQL does not apply RLS to a table's owner. This was verified on PostgreSQL 16 (see `docs/PROJECT_STATUS.md`, section 4.2).
- Automated tests use SQLite by default and never connect to Supabase, so they cost nothing and use no quota. Continuous integration also runs the tests against a temporary PostgreSQL 16 service.
- Images and other media will be stored in a **private** Supabase Storage bucket, accessed from the server through Supabase's S3-compatible API (expected: `django-storages` with `boto3`), and shown to users through short-lived signed URLs. The S3 access keys are server-side secrets with broad access and must never reach the browser. This will be implemented when file uploads are built (Phase 6), after re-checking Supabase's current S3 documentation.

**Free plan constraints (reported by third-party sources on 2026-10-27; verify on Supabase's pricing page):** about 500 MB of database per project, 1 GB of file storage, limited bandwidth, and projects are paused after about 7 days without activity until restored from the dashboard. These limits are adequate for development and demonstrations, not for production with real customers.

**Recommended Supabase dashboard settings:** Because Django does not use the Data API, disable the Data API or remove the `public` schema from its exposed schemas if the dashboard allows it. RLS remains the safeguard if it is left on.

**Alternatives considered:** Local PostgreSQL (uses RAM on an 8 GB laptop and is not reachable for demonstrations); other hosted PostgreSQL free tiers (several expire or delete data after a fixed period); SQLite in production (unsuitable for concurrent users and ephemeral hosting disks).

**Review conditions:** Revisit if free-plan limits or pausing block development, or when real customers require an always-on database.

## 5. Product Direction Decisions

### DEC-013: Hybrid Video Production

**Status:** Proposed

**Decision under consideration:** Combine authentic business assets, motion graphics, narration, music, captions, and AI-generated supplementary footage where appropriate.

**Reasoning:** A hybrid approach may offer better factual accuracy, creative control, and cost flexibility than relying exclusively on generated footage.

**Pending validation:**
- Which production workflow should be implemented first?
- Which video-generation providers or local tools are suitable?
- What level of visual quality can be achieved within acceptable costs?

**Zero-budget note:** Under DEC-016, the recommended first workflow is animation of authentic website assets with FFmpeg (motion, text, captions, optional narration and licensed music). AI-generated footage is deferred because suitable free options for commercial use have not been verified.

### DEC-014: User-Editable Creative Outputs

**Status:** Proposed

**Decision under consideration:** Allow users to review and edit scripts, scenes, images, narration, captions, and creative settings before final export.

**Reasoning:** Users need control over business claims, brand identity, and creative direction.

**Potential implementation sequence:**
1. Editable scripts and creative settings.
2. Scene and asset editing.
3. Preview and revision.
4. More advanced timeline editing if justified.

### DEC-015: Progressive Expansion of Content Types

**Status:** Accepted

**Decision:** Build and validate the core workflow before implementing the entire long-term marketing feature set.

**Reasoning:** Delivering one complete, tested workflow is more valuable than creating many disconnected or incomplete features.

**Implementation implications:**
- Prioritize website analysis and business-profile review.
- Add script generation and then a useful media-output workflow.
- Expand into additional content formats based on validated requirements.

## 6. Decisions Still Required

The following topics remain open until explicitly decided and recorded.

| ID | Topic | Decision Needed |
|---|---|---|
| OPEN-001 | Initial product scope | Videos only, multiple content types, or broader marketing studio |
| OPEN-002 | Initial target market and languages | East Africa first or international launch focus; whether Kiswahili and English are the launch languages |
| ~~OPEN-003~~ | ~~Provider budget~~ | **Resolved by DEC-016:** zero budget |
| OPEN-004 | Initial video method | Animation using authentic assets, generated footage, or a hybrid (DEC-016 recommends authentic-asset animation first) |
| OPEN-005 | Website crawl policy | Automatic relevant-page discovery, user-selected pages, or both |
| OPEN-006 | Initial editing depth | Basic settings and scripts, scene editor, or full timeline |
| OPEN-007 | Authentication | Initial account and access requirements |
| OPEN-008 | Background processing | When a job queue and separate workers become necessary; at zero budget, prefer a database-backed approach that needs no extra service |
| ~~OPEN-009~~ | ~~Storage~~ | **Resolved by DEC-018:** Supabase PostgreSQL and a private Supabase Storage bucket |
| OPEN-010 | Deployment | Hosting environment and production architecture; must fit free-tier limits under DEC-016 |
| OPEN-013 | Text AI provider | Which free hosted text-generation option to use first, after verifying current terms (local models are impractical on the 8 GB development laptop; see DEC-012) |
| OPEN-014 | Narration | Which free speech option, if any, is licensed for commercial use in the launch languages |
| OPEN-011 | Usage limits | Project, crawl, generation, and export limits |
| OPEN-012 | Commercial model | Free access, subscriptions, usage-based pricing, or a combination |

An AI assistant must not silently convert an open question into an accepted project decision.

When a decision is necessary to proceed, the assistant should explain the trade-offs, recommend an option, and ask for approval if the choice materially affects the product or architecture.

## 7. How to Record New Decisions

Use this format for significant new decisions:

### DEC-XXX: Short Decision Title

**Status:** Proposed / Accepted / Provisional / Under Review / Superseded / Rejected

**Date:** YYYY-MM-DD

**Context:** Explain the problem or requirement that led to the decision.

**Decision:** State the selected approach clearly.

**Reasoning:** Explain why the approach was selected.

**Alternatives considered:** List meaningful alternatives.

**Consequences:** Describe benefits, costs, limitations, and implementation effects.

**Review conditions:** Explain what evidence would justify revisiting the decision.

## 8. Changing an Existing Decision

Do not silently rewrite an accepted decision when new information appears.

Instead:

1. Identify the existing decision.
2. Explain the new requirement or evidence.
3. Evaluate the consequences of changing it.
4. Record the revised decision.
5. Mark the previous decision as superseded where appropriate.
6. Update affected architecture, requirements, tasks, and tests.

This preserves the reasoning behind important technical and product choices.

## 9. Rules for AI Coding Assistants

Every AI coding assistant working on this project must:

- Read this document before making major architectural changes.
- Distinguish accepted decisions from provisional proposals.
- Avoid treating proposed options as approved requirements.
- Explain when a requested change conflicts with an accepted decision.
- Record significant approved changes.
- Prefer evidence and tests over assumptions.
- Preserve the project's core principles when proposing alternatives.

## 10. Final Principle

This decision log exists to maintain continuity, not to prevent improvement.

Decisions should remain stable enough to support consistent development but flexible enough to change when testing, user feedback, security analysis, or technical evidence demonstrates a better approach.
