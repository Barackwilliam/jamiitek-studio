# Development Tasks — JamiiTek AI Marketing Studio

**Document:** Development Task Register  
**Version:** 1.1  
**Status:** Initial Planning  
**Last Updated:** 2026-10-27  
**Budget constraint:** Zero budget (see `docs/DECISIONS.md`, DEC-016)  
**Priority Convention:** P0 = Critical, P1 = High, P2 = Medium, P3 = Later

## 1. Purpose

This document defines the development roadmap and actionable tasks for JamiiTek AI Marketing Studio.

It is intended to help developers and AI coding assistants work consistently, prioritize important dependencies, track progress, and avoid implementing unrelated features before the core workflow is functional.

Tasks must be updated based on the actual repository and verified implementation status.

**Important:** An unchecked task means it has not been confirmed complete. Do not mark a task complete without appropriate evidence.

## 2. Task Management Rules

1. Inspect the repository before starting implementation work.
2. Review `AI_PROJECT_GUIDE.md`, `PROJECT_MASTER.md`, `AGENTS.md`, and relevant documents in `docs/`.
3. Check Git status and preserve existing changes.
4. Select one clearly defined task or a small group of closely related tasks.
5. Identify dependencies and acceptance criteria before coding.
6. Implement the smallest useful solution.
7. Run relevant tests and record their actual results.
8. Update documentation and project status.
9. Commit changes only when appropriate and only after reviewing them.
10. Select the next task based on dependencies, evidence, and product priorities.

Do not create multiple competing implementations of the same feature. Before starting a task, verify whether the required functionality already exists.

## 3. Priority Definitions

- **P0 — Critical:** Required for safe development or for the first end-to-end workflow.
- **P1 — High:** Required for a useful initial product.
- **P2 — Medium:** Improves quality, flexibility, usability, or operational reliability.
- **P3 — Later:** Advanced or optional capabilities that can follow after the core product is validated.

Priorities may change when new technical evidence or product decisions justify a different sequence.

---

## Phase 0: Documentation and Project Preparation

**Goal:** Establish consistent instructions and a shared understanding of the project.

### Tasks

- [x] **TASK-001 — P0:** Create the project's Git repository. *(`Barackwilliam/jamiitek-studio`, 2026-10-27.)*
- [x] **TASK-002 — P0:** Verify which planning documents exist. *(2026-10-27: all ten documents exist.)*
- [x] **TASK-003 — P0:** Save and reconcile the agreed project documentation. *(Pushed to GitHub 2026-10-27.)*
- [x] **TASK-004 — P0:** Complete `docs/TESTING.md`. *(Written 2026-10-27.)*
- [x] **TASK-005 — P0:** Review `docs/PROJECT_REQUIREMENTS.md` for consistency with the master specification. *(2026-10-27: added manual business-information entry, robots.txt handling, prompt-injection protection, language and licensing requirements.)*
- [x] **TASK-006 — P1:** Record important technical and product decisions in `docs/DECISIONS.md`. *(Initial log written; DEC-016 zero budget added 2026-10-27.)*
- [ ] **TASK-007 — P1:** Confirm the initial product scope and first milestone.
- [x] **TASK-008 — P1:** Establish a documented method for updating project status. *(Defined in `docs/PROJECT_STATUS.md`, sections 8 and 9.)*

### Acceptance criteria

- The documentation exists in the intended repository locations.
- Conflicting requirements and decisions are identified.
- The first implementation milestone is clear.
- The project status reflects the actual state of the repository.

**Dependency:** None.

---

## Phase 1: Development Environment and Application Foundation

**Goal:** Establish a working, testable Django foundation.

### Tasks

- [ ] **TASK-009 — P0:** Verify the installed Python version and development environment. *(Verified on Linux with Python 3.13 on 2026-10-27. Not yet verified on the owner's Windows computer.)*
- [x] **TASK-010 — P0:** Verify or create the Django project, depending on the existing repository. *(Django 5.2 project created; DEC-017.)*
- [x] **TASK-011 — P0:** Establish a repeatable dependency-installation workflow. *(`requirements.txt` with version ranges; virtual environment steps in `README.md`.)*
- [x] **TASK-012 — P0:** Configure development settings and environment variables. *(`config/settings.py`, `.env.example`.)*
- [x] **TASK-013 — P0:** Configure the initial database. *(SQLite, path configurable through `DJANGO_SQLITE_PATH`.)*
- [x] **TASK-014 — P0:** Verify Django migrations and database connectivity. *(`migrate` applied; `makemigrations --check` reports no changes; `/health/` confirms database access.)*
- [x] **TASK-015 — P0:** Establish a basic application entry page. *(`/` describes the product and states honestly that no features are available yet.)*
- [x] **TASK-016 — P0:** Add a basic health or availability check. *(`/health/` returns 200 or 503 JSON without internal details.)*
- [x] **TASK-017 — P0:** Add foundational automated tests. *(17 tests in `apps/core/tests/`; all passing on 2026-10-27.)*
- [x] **TASK-018 — P1:** Configure Git hygiene, `.gitignore`, `.gitattributes` (consistent line endings between Windows and Linux), and a safe example environment file.
- [x] **TASK-019 — P1:** Document the actual setup, run, and test commands in `README.md`. *(Linux commands verified; Windows commands not yet verified on Windows.)*
- [ ] **TASK-019A — P1:** Run checks and tests automatically on GitHub Actions. *(Workflow written with SQLite and PostgreSQL jobs; blocked because GitHub stops the jobs before they start. See `docs/PROJECT_STATUS.md`, section 5.1.)*
- [x] **TASK-019B — P1:** Support PostgreSQL through `DATABASE_URL`, with automatic row level security for Supabase (DEC-018).

### Acceptance criteria

- The application starts successfully in the documented environment.
- Database setup is reproducible.
- Basic automated tests run successfully.
- Secrets are not committed to version control.
- Setup instructions match the actual implementation.

**Dependencies:** Phase 0.

---

## Phase 2: Project and User Data Foundation

**Goal:** Establish the data structures needed to manage marketing projects.

### Tasks

- [x] **TASK-020 — P0:** Define the initial data model and ownership rules. *(Each project has one owner; other users get 404.)*
- [x] **TASK-021 — P0:** Implement the initial project model.
- [x] **TASK-022 — P0:** Implement project creation and retrieval.
- [x] **TASK-023 — P0:** Implement server-side validation for project input. *(Website address safety-checked; a website or business details required; length limits.)*
- [x] **TASK-024 — P0:** Add appropriate authentication and authorization for private projects. *(Sign up, log in, log out; all project pages require login.)*
- [x] **TASK-025 — P0:** Add tests for project ownership and unauthorized access.
- [x] **TASK-026 — P1:** Build the initial project dashboard.
- [x] **TASK-027 — P1:** Add project editing and deletion behavior with appropriate safeguards. *(Deletion requires a confirmation page and POST.)*
- [ ] **TASK-027A — P1:** Add login rate limiting before any public launch.
- [ ] **TASK-027B — P2:** Collect email addresses and enable password reset (needs a free email-sending option).

### Acceptance criteria

- A user can create and reopen a project.
- Project data is stored correctly.
- Private project data cannot be accessed by unauthorized users.
- Invalid input and missing records are handled clearly.
- Relevant tests pass.

**Dependencies:** Phase 1.

---

## Phase 3: Secure Website Analysis

**Goal:** Accept a website URL and safely extract useful public business information.

### Tasks

- [x] **TASK-028 — P0:** Define URL-validation rules and supported protocols. *(`url_safety.py`: HTTP/HTTPS on ports 80 and 443 only.)*
- [x] **TASK-029 — P0:** Implement protection against SSRF and unsafe network destinations.
- [x] **TASK-030 — P0:** Validate resolved IP addresses and redirect destinations. *(Every hop revalidated; connections pinned to validated addresses.)*
- [x] **TASK-031 — P0:** Apply request timeouts and response-size limits. *(`fetch.py`.)*
- [x] **TASK-032 — P0:** Build a controlled test website containing representative HTML content. *(`apps/website_analyzer/tests/fixtures/site/`: Kiswahili business site with JSON-LD, robots.txt, a disallowed page, a missing page and a prompt-injection sentence.)*
- [x] **TASK-033 — P0:** Implement basic HTML retrieval and parsing. *(`fetch.py` and `extract.py` with Beautiful Soup's built-in parser.)*
- [x] **TASK-034 — P0:** Extract page titles, metadata, and relevant text. *(Title, description, language, canonical, Open Graph, headings, main text, images, JSON-LD.)*
- [x] **TASK-035 — P1:** Discover relevant internal pages and avoid duplicate URLs. *(English and Kiswahili relevance keywords; low-value pages such as login and cart skipped.)*
- [x] **TASK-036 — P1:** Add configurable page-count, crawl-depth, and resource limits. *(Defaults: 8 pages, depth 2, 120 seconds, at least 1 second between requests.)*
- [ ] **TASK-037 — P1:** Evaluate Playwright for JavaScript-rendered websites. *(Deferred: see DEC-019.)*
- [ ] **TASK-038 — P1:** Isolate browser automation and restrict unnecessary network access. *(Deferred with TASK-037.)*
- [x] **TASK-039 — P1:** Record individual page outcomes and analysis failures.
- [x] **TASK-040 — P1:** Display analysis progress and meaningful error messages. *(Status page refreshes every 5 seconds while active; warns if the worker seems not to be running.)*
- [x] **TASK-041 — P1:** Add security tests for malicious URLs, redirects, and resource exhaustion.
- [x] **TASK-041A — P1:** Read and honor `robots.txt`, and apply a per-site request-rate limit. *(RFC 9309 behaviour; `Crawl-delay` honoured up to 10 seconds.)*
- [ ] **TASK-041C — P2:** Use sitemaps to find relevant pages.
- [ ] **TASK-041D — P2:** Test analysis against a set of real public websites from different industries (not possible in the development container, which has no direct internet access).
- [x] **TASK-041B — P1:** Allow manual entry of business information when no website is available or analysis fails (FR-02A). *(Basic free-text version; structured fields come with the business profile in Phase 4.)*

### Acceptance criteria

- Valid public test websites can be analyzed.
- Unsafe destinations are blocked.
- Redirects and DNS resolution are handled securely.
- Crawl limits are enforced.
- A failed page does not unnecessarily destroy all successful analysis results.
- Users can understand what was analyzed and what failed.

**Dependencies:** Phase 2.

---

## Phase 4: Business Profile and Evidence Management

**Goal:** Convert website content into structured, reviewable business information.

### Tasks

- [x] **TASK-042 — P0:** Define the initial business-profile schema. *(`BusinessProfile` and `ProfileFact`: key, value, source, status, evidence; DEC-020.)*
- [x] **TASK-043 — P0:** Extract business names, descriptions, products, and services where available. *(From structured data, meta tags, the home page title, and list lines on services/products pages; no AI.)*
- [x] **TASK-044 — P0:** Associate extracted information with its source where practical. *(Every website fact lists each page and the part of the page it came from.)*
- [x] **TASK-045 — P0:** Distinguish source facts, user-confirmed facts, inferences, and unknowns. *("Needs your review" vs "Confirmed" vs "Entered by you"; missing essential information listed. No inferences exist yet; AI suggestions in Phase 5 must be stored with their own source.)*
- [x] **TASK-046 — P0:** Build the business-profile review interface.
- [x] **TASK-047 — P0:** Allow users to correct extracted information. *(Confirm, edit, reject, undo, add, remove own entries.)*
- [x] **TASK-048 — P0:** Persist user-confirmed corrections. *(Kept across re-analysis; rejected and edited website values are not suggested again.)*
- [ ] **TASK-049 — P1:** Extract relevant logos, brand colors, and images where feasible. *(Partial: logo from structured data or Open Graph, brand colour from `theme-color`; colours from CSS and image selection not done.)*
- [x] **TASK-050 — P1:** Add tests for incomplete, conflicting, and unsupported website information. *(Including text that tries to instruct the AI.)*

### Acceptance criteria

- The profile represents available source information accurately.
- Users can correct errors before content generation.
- Unsupported business claims are not treated as verified facts.
- Important source information is preserved where practical.

**Dependencies:** Phase 3.

---

## Phase 5: AI Provider Foundation and Marketing Content

**Goal:** Generate useful marketing concepts and scripts from reviewed business information.

### Tasks

- [x] **TASK-051 — P0:** Define the initial marketing brief and generation request structures. *(`MarketingBrief`, `GenerationJob`, `ContentDraft`.)*
- [x] **TASK-052 — P0:** Decide which free AI text option to use first. *(DEC-021: any OpenAI-compatible API; Gemini recommended for Kiswahili, Groq as the privacy-friendlier option. Terms must be re-checked by the owner when creating keys.)*
- [x] **TASK-053 — P0:** Implement a modular text-generation provider interface appropriate to the selected provider. *(`integrations/ai/`, standard library only.)*
- [x] **TASK-054 — P0:** Configure credentials securely outside source control. *(`.env`; key never logged or sent to the browser.)*
- [x] **TASK-055 — P0:** Implement provider timeouts and error handling. *(Timeout, one retry for server errors and unusable answers, no retry for quota or key errors.)*
- [x] **TASK-056 — P0:** Generate marketing concepts from the reviewed business profile. *(Confirmed facts only.)*
- [x] **TASK-057 — P0:** Generate scripts, headlines, captions, and calls to action.
- [x] **TASK-058 — P0:** Allow users to edit generated text. *(Scripts; concepts are chosen, not edited.)*
- [x] **TASK-059 — P0:** Save drafts and user edits. *(Regenerating creates new drafts; edited and approved drafts are never overwritten.)*
- [x] **TASK-060 — P1:** Add language, tone, audience, objective, and platform settings.
- [x] **TASK-061 — P1:** Add claim-review rules and safeguards against unsupported factual assertions. *(Numbers and risky phrases in English and Kiswahili flagged; approval requires ticking that they were checked.)*
- [x] **TASK-061A — P1:** Protect generation against instructions embedded in website content (prompt injection). *(Only user-confirmed facts are sent, as a JSON data block; the system prompt says to ignore instructions in data; output is validated.)*
- [x] **TASK-062 — P1:** Add tests using mocked provider responses.
- [x] **TASK-063 — P1:** Track generation errors and free-tier quota usage, and handle quota exhaustion without losing user work. *(Token usage stored per job; quota errors explained; brief and drafts kept.)*
- [ ] **TASK-063A — P1:** Try AI writing with a real provider key and review Kiswahili quality with real users.
- [ ] **TASK-063B — P2:** Allow editing concepts, and show remaining free quota where the provider reports it.

### Acceptance criteria

- Marketing concepts use the correct business profile.
- Users can edit and save scripts.
- Provider failures produce understandable messages.
- Secrets are not exposed to the frontend.
- Unsupported factual claims are avoided or flagged for review.
- Routine tests do not call live AI services or consume free-tier quotas.

**Dependencies:** Phase 4.

---

## Phase 6: Creative Configuration and Asset Management

**Goal:** Prepare approved content and media assets for production.

### Tasks

- [x] **TASK-064 — P1:** Define the initial creative configuration model. *(Brief settings from Phase 5 plus poster format, photo, logo and brand colour.)*
- [x] **TASK-065 — P1:** Implement settings for aspect ratio, language, tone, and duration. *(Language, tone, duration in the brief; 1:1, 9:16 and 16:9 for posters.)*
- [x] **TASK-066 — P1:** Implement project asset metadata and ownership. *(`Asset`: origin, source URL, description, size, checksum, rights confirmation.)*
- [x] **TASK-067 — P1:** Support safe selection of website images. *(Only images found by the analysis; SSRF-safe fetch; robots.txt; no third-party images loaded in our pages.)*
- [x] **TASK-068 — P1:** Add secure user uploads where required.
- [x] **TASK-069 — P1:** Validate file types, sizes, and relevant media properties. *(Pillow decides the format; size, dimension and decompression-bomb limits; re-encoded without metadata.)*
- [x] **TASK-070 — P1:** Implement brand asset selection and logo placement options. *(Logo and photo chosen per poster; logo placement fixed in the top corner.)*
- [x] **TASK-071 — P2:** Evaluate free image-generation options. *(Deferred, DEC-022.)*
- [x] **TASK-072 — P2:** Add poster generation from templates and approved assets. *(No AI; AI images deferred.)*
- [ ] **TASK-073 — P2:** Add asset preview and replacement workflows. *(Partial: previews, removal and re-upload; no in-place replacement or cropping.)*
- [ ] **TASK-073A — P1:** Try Supabase Storage with a real private bucket.
- [ ] **TASK-073B — P2:** More poster layouts and choice of logo position.

### Acceptance criteria

- Assets are linked to the correct project.
- Unsafe uploads are rejected.
- Creative settings persist.
- Users can distinguish available source assets from generated assets.
- Asset failures do not corrupt unrelated project data.

**Dependencies:** Phases 4 and 5, where applicable.

---

## Phase 7: Audio, Scenes, and Video Rendering

**Goal:** Produce a functional promotional MP4 from approved content and media.

### Tasks

- [x] **TASK-074 — P1:** Define the initial video scene-plan format. *(Snapshot of approved script scenes: texts, durations, image IDs, end card.)*
- [x] **TASK-075 — P1:** Validate scene timing and asset references. *(2–15 s per scene, 120 s total, voice-over must fit; checked before queueing and again before rendering; missing images fall back to the brand colour.)*
- [x] **TASK-076 — P1:** Establish a working FFmpeg rendering prototype using local test assets.
- [x] **TASK-077 — P1:** Implement image and video preparation for scenes. *(Photos; video clips as scene sources are not supported yet.)*
- [x] **TASK-078 — P1:** Implement basic transitions and animated text. *(Slow zoom and cross-fades; text is static.)*
- [x] **TASK-079 — P1:** Implement audio and caption composition. *(Narration text as captions; music looped and faded; user voice-over mixed above music.)*
- [ ] **TASK-080 — P1:** Evaluate free narration options (OPEN-014). *(Still open: no free Kiswahili voice with a confirmed commercial licence. Users can upload their own recorded voice-over instead.)*
- [x] **TASK-081 — P1:** Render an initial playable MP4.
- [x] **TASK-082 — P1:** Validate output dimensions, duration, and playback. *(FFprobe checks plus a full decode; a failed check fails the render.)*
- [x] **TASK-083 — P1:** Implement safe temporary-file handling. *(Temporary folders always removed.)*
- [ ] **TASK-084 — P1:** Add rendering failure handling and bounded retries. *(Failures recorded with safe messages; no automatic retry, the user starts it again.)*
- [x] **TASK-085 — P2:** Evaluate AI-generated supplementary video footage. *(Deferred, DEC-023.)*
- [ ] **TASK-086 — P2:** Add a hybrid workflow with supplementary generated footage. *(Deferred.)*
- [x] **TASK-087 — P2:** Evaluate 9:16, 16:9, and 1:1 output profiles.
- [ ] **TASK-088 — P2:** Add scene-level preview and revision where practical. *(Whole-video preview quality only.)*
- [ ] **TASK-088A — P2:** Support seeking in long videos (HTTP range requests) and video clips as scene sources.

### Acceptance criteria

- A controlled test project produces a playable MP4.
- Output settings match the selected profile.
- Failed renders are not marked successful.
- Rendering does not unnecessarily block normal web requests.
- Temporary files are cleaned up safely.
- Users can preview available output before final delivery.

**Dependencies:** Phase 5 and the relevant tasks in Phase 6.

---

## Phase 8: Job Processing, Exports, and Reliability

**Goal:** Make longer workflows dependable and manageable.

### Tasks

- [ ] **TASK-089 — P1:** Define job states and allowed state transitions.
- [ ] **TASK-090 — P1:** Decide when background workers become necessary.
- [ ] **TASK-091 — P1:** Implement background processing for the first long-running operation.
- [ ] **TASK-092 — P1:** Persist job status and sanitized error information.
- [ ] **TASK-093 — P1:** Prevent unnecessary duplicate generation or rendering.
- [ ] **TASK-094 — P1:** Implement export metadata and authorized downloads.
- [ ] **TASK-095 — P1:** Add retry behavior for recoverable failures.
- [ ] **TASK-096 — P1:** Add cleanup rules for temporary files and expired exports.
- [ ] **TASK-097 — P1:** Test worker interruption and failed-job recovery.
- [ ] **TASK-098 — P2:** Add project history and version tracking.
- [ ] **TASK-099 — P2:** Add operational logs and basic health monitoring.

### Acceptance criteria

- Long-running jobs have visible and reliable status.
- Failed tasks can be diagnosed.
- Export access is authorized.
- Duplicate operations are controlled where practical.
- Cleanup does not remove active project assets.

**Dependencies:** Earlier phases, particularly media production.

---

## Phase 9: User Experience and Product Quality

**Goal:** Make the complete workflow understandable and professional.

### Tasks

- [ ] **TASK-100 — P1:** Review the end-to-end user journey.
- [ ] **TASK-101 — P1:** Improve loading, success, empty, and error states.
- [ ] **TASK-102 — P1:** Validate desktop and mobile layouts.
- [ ] **TASK-103 — P1:** Improve form validation and user feedback.
- [ ] **TASK-104 — P1:** Add confirmations for destructive or potentially expensive actions.
- [ ] **TASK-105 — P2:** Improve accessibility and keyboard navigation.
- [ ] **TASK-106 — P2:** Add clearer previews and generation progress.
- [ ] **TASK-107 — P2:** Conduct usability testing with representative users.

### Acceptance criteria

- Users can complete the main workflow without developer intervention.
- Errors explain what happened and what the user can do next.
- Important actions are accessible and understandable.
- The interface works on supported screen sizes.

**Dependencies:** The relevant features from Phases 2–8. UX review should continue throughout development, not only at this stage.

---

## Phase 10: Production Readiness

**Goal:** Prepare the platform for controlled real-world use.

### Tasks

- [ ] **TASK-108 — P1:** Complete the production security review.
- [ ] **TASK-109 — P1:** Select the initial deployment infrastructure within the zero-budget constraint, confirming memory limits, outbound network access, and persistent storage.
- [ ] **TASK-110 — P1:** Configure production secrets and environment settings.
- [ ] **TASK-111 — P1:** Select production database and storage solutions.
- [ ] **TASK-112 — P1:** Configure backups and recovery procedures.
- [ ] **TASK-113 — P1:** Establish appropriate rate and resource limits.
- [ ] **TASK-114 — P1:** Run integration and end-to-end tests.
- [ ] **TASK-115 — P1:** Test the system using representative websites and realistic workloads.
- [ ] **TASK-116 — P1:** Document deployment and troubleshooting.
- [ ] **TASK-117 — P2:** Establish a process for collecting user feedback.
- [ ] **TASK-118 — P2:** Review usage costs and generation quality.
- [ ] **TASK-119 — P2:** Plan the next product expansion based on evidence.

### Acceptance criteria

- Production configuration does not expose secrets.
- Core workflows have passed relevant tests.
- Backup and recovery procedures are documented.
- Resource limits and failure handling are in place.
- Known limitations are communicated honestly.

**Dependencies:** Phases 1–9.

---

## 4. Long-Term Expansion

These tasks should be considered only after the core workflow is functional and validated.

- [ ] **TASK-120 — P3:** Add a more advanced timeline editor.
- [ ] **TASK-121 — P3:** Expand image, poster, and social-content workflows.
- [ ] **TASK-122 — P3:** Expand multilingual narration and localization.
- [ ] **TASK-123 — P3:** Add reusable campaign templates.
- [ ] **TASK-124 — P3:** Explore social-platform publishing integrations.
- [ ] **TASK-125 — P3:** Explore advertising campaign analytics and optimization.
- [ ] **TASK-126 — P3:** Evaluate subscription and usage-based billing.
- [ ] **TASK-127 — P3:** Improve collaborative workflows and team access.
- [ ] **TASK-128 — P3:** Evaluate additional providers and deployment scaling.
- [ ] **TASK-129 — P3:** Revisit DEC-016 (zero budget) when funding or paying users exist, and evaluate which paid services would most improve quality.

Each expansion requires its own requirements, security review, tests, and acceptance criteria.

## 5. Current Recommended Starting Point

As of 2026-10-27, the planning documents are complete and no code exists. The next tasks are TASK-001 (create the repository), TASK-003 (commit the documents), and then Phase 1.

Before implementing any task:

1. Inspect the real repository.
2. Review the current Git status.
3. Identify any existing implementation.
4. Update `docs/PROJECT_STATUS.md`.
5. Select the first task that is genuinely unfinished.

If working code already exists, preserve it and adapt this roadmap to the verified state.

Do not assume the project needs to be rebuilt from scratch.

## 6. Task Completion Record

For significant completed tasks, record:

- Task ID and title.
- Completion date.
- Files created or changed.
- Implementation summary.
- Tests performed and their actual results.
- Known limitations.
- Related commit, if one exists.
- Next recommended task.

A task may be marked complete only when its defined acceptance criteria have been satisfied. If implementation exists but verification is incomplete, document that distinction.

## 7. Task Prioritization Rules

When selecting the next task, prioritize:

1. Security and data-integrity issues.
2. Blockers preventing the core workflow.
3. Tasks with important downstream dependencies.
4. High-value user functionality.
5. Testing and reliability gaps.
6. Usability improvements.
7. Optional advanced features.

Avoid beginning multiple expensive or complex features simultaneously without a clear reason.

## 8. Final Principle

The objective is not to complete the largest possible number of tasks. The objective is to build a reliable product through small, verifiable steps.

Every AI coding assistant must check the current repository and this task register before deciding what to implement next.
