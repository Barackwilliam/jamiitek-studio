# System Architecture — JamiiTek AI Marketing Studio

**Document type:** Technical Architecture  
**Version:** 1.1  
**Status:** Proposed — subject to validation during implementation  
**Budget constraint:** Zero budget (see `docs/DECISIONS.md`, DEC-016)

## 1. Purpose

This document defines the proposed technical architecture for JamiiTek AI Marketing Studio.

It establishes component boundaries, data flow, security requirements, provider integration principles, and implementation guidelines.

This architecture is a design proposal. The actual repository, installed dependencies, and implemented components must be inspected before assuming that any part of this architecture exists.

## 2. Architectural Goals

The system should be designed to:

- Support a complete workflow from website analysis to downloadable marketing content.
- Adapt to different website technologies and business types.
- Keep AI and media providers replaceable where practical.
- Isolate slow or resource-intensive operations.
- Protect against malicious URLs, unsafe files, and unauthorized data access.
- Preserve user edits and project history.
- Support testing at component and workflow levels.
- Begin with a manageable implementation and evolve as requirements become clearer.

## 3. Proposed High-Level Architecture

```text
User Browser
    |
    v
Django Web Application
    |
    +-- Authentication and Authorization
    |
    +-- Project and Workflow Management
    |
    +-- Website Analysis Service
    |       |
    |       +-- URL Security Validation
    |       +-- HTTP Fetching and HTML Parsing
    |       +-- Browser Automation
    |       +-- Page Discovery and Extraction
    |
    +-- Business Intelligence and Content Service
    |       |
    |       +-- Structured Business Profile
    |       +-- AI Provider Interfaces
    |       +-- Script and Copy Generation
    |
    +-- Creative Asset Service
    |       |
    |       +-- Image and Audio Providers
    |       +-- Asset Selection and Validation
    |
    +-- Media Production Service
    |       |
    |       +-- Scene Composition
    |       +-- Audio and Caption Processing
    |       +-- Video Rendering
    |
    +-- Job Management
            |
            +-- Website Analysis Jobs
            +-- AI Generation Jobs
            +-- Media Processing Jobs

Shared Infrastructure:
    Database | File Storage | Configuration | Logging
```

The diagram describes logical responsibilities, not a requirement to create a separate server or service for every component.

The initial implementation should favor a modular Django application unless actual performance, deployment, or reliability needs justify separating components into independent services.

## 4. Proposed Django Application Structure

The following is a possible target structure, not an assertion about the current repository.

```text
jamiitek-ai-marketing-studio/
|
|-- manage.py
|-- config/
|   |-- settings/
|   |-- urls.py
|   |-- asgi.py
|   |-- wsgi.py
|
|-- apps/
|   |-- accounts/
|   |-- projects/
|   |-- website_analyzer/
|   |-- business_profiles/
|   |-- marketing_content/
|   |-- creative_assets/
|   |-- media_production/
|   |-- jobs/
|   |-- exports/
|
|-- integrations/
|   |-- ai/
|   |-- image/
|   |-- speech/
|   |-- video/
|
|-- templates/
|-- static/
|
|-- docs/
|-- tests/
|   |-- fixtures/
|       |-- websites/
|       |-- media/
|
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- .gitattributes
|-- README.md
```

Create applications progressively as their responsibilities become necessary. Avoid creating empty applications or unnecessary abstractions simply to match this diagram.

User-uploaded and generated files must not be stored inside the source-code tree or committed to Git. Configure `MEDIA_ROOT` (and any private storage location) through an environment variable that points outside the repository, and keep that location in `.gitignore` if a local default is ever placed inside the project folder. Private files must not be served directly as public static files.

## 5. Component Responsibilities

### 5.1 Web Interface

The frontend should use Django templates, HTML, CSS, and vanilla JavaScript as the initial direction.

Responsibilities:

- Present project workflows.
- Collect URLs and creative preferences.
- Display analysis results and validation errors.
- Allow editing and approval of content.
- Show job progress.
- Preview available outputs.
- Provide authorized export links.

The frontend must not contain provider secrets or perform privileged security decisions that belong on the server.

### 5.2 Project Management

The project layer manages the relationship between users, business profiles, website analyses, creative configurations, generated content, and exports.

It should enforce ownership and prevent data belonging to one user from leaking to another.

### 5.3 Website Analyzer

The website analyzer should be organized into focused stages:

1. Validate the submitted URL.
2. Resolve and validate network destinations.
3. Apply crawl and resource limits.
4. Discover relevant pages.
5. Fetch content through an approved retrieval mechanism.
6. Use browser automation when necessary and safe.
7. Extract structured information and assets.
8. Record page-level results and failures.
9. Return a structured analysis to the next stage.

The analyzer should not be coupled directly to a specific AI provider.

### 5.4 Business Profile Service

This component converts extracted website data into a structured representation of the business.

It should distinguish:

- Facts extracted from a source.
- User-confirmed information.
- AI-generated suggestions.
- Unknown or uncertain information.

Where practical, important fields should preserve their source URL and extraction metadata.

### 5.5 Marketing Content Service

This component generates marketing concepts, scripts, captions, headlines, and related text.

It should accept structured business information and explicit user preferences rather than passing an uncontrolled collection of website content to every provider.

It should support content validation and user review before production.

### 5.6 Provider Integration Layer

Provider integrations should be separated from application workflows.

The application should call internal interfaces rather than scattering provider-specific API calls across Django views.

Illustrative interfaces could include:

```python
class TextGenerationProvider:
    def generate(self, request):
        raise NotImplementedError


class ImageGenerationProvider:
    def generate(self, request):
        raise NotImplementedError


class SpeechProvider:
    def synthesize(self, request):
        raise NotImplementedError
```

These are illustrative interface examples, not implemented classes.

Each real integration should define its supported capabilities, input validation, output format, error handling, timeouts, usage reporting, and configuration requirements.

Do not force providers with materially different capabilities into a misleading common interface.

### 5.7 Media Production Service

The media production layer should convert approved creative inputs into renderable output.

Its responsibilities may include:

- Building a scene plan.
- Selecting and validating media assets.
- Preparing images and video clips.
- Calculating scene timing.
- Applying motion graphics and transitions.
- Adding captions and narration.
- Mixing audio.
- Rendering with FFmpeg or another suitable engine.
- Validating the final output.

Rendering logic should be independent of Django request handling so it can be executed by a worker process when needed.

### 5.8 Job Management

Long-running tasks should be represented as trackable jobs.

Potential job types include website analysis, script generation, asset generation, and video rendering.

Job records should capture the task type, project association, status, timestamps, and sanitized error information.

Retries should be bounded and should not repeat expensive operations unnecessarily.

A job queue and worker framework should be selected based on the actual workload. The architecture must not assume that background processing is already configured.

Under the zero-budget constraint, prefer a job mechanism that uses the existing database and a separately started worker process (for example, a Django management command that claims queued jobs) before introducing Redis, RabbitMQ, or another service that must be hosted and maintained.

## 6. Data Architecture

The database should represent important business objects and their relationships.

Potential models include:

| Model | Responsibility |
|---|---|
| User | Authentication and account ownership |
| Project | Main marketing workspace |
| WebsiteAnalysis | Analysis request and overall status |
| AnalyzedPage | Extracted content and page-level status |
| BusinessProfile | Structured business information |
| BusinessFact | Important facts and source provenance, if normalized separately |
| CreativeConfiguration | User-selected creative settings |
| ContentDraft | Generated or edited scripts and copy |
| Asset | Metadata for uploaded, retrieved, or generated media |
| GenerationJob | Long-running task state |
| Render | Video or other rendered output |
| Export | Downloadable output metadata |

This is a conceptual model list. The actual Django models should be introduced according to validated requirements, not all at once.

### Data integrity rules

- Associate private records with their correct owner and project.
- Enforce authorization in server-side operations.
- Use appropriate database constraints and relationships.
- Keep generated files and database metadata consistent.
- Track relevant versions of editable content.
- Use migrations for schema changes.
- Define retention and deletion behavior before production use.

## 7. Website Analysis Security Architecture

Website fetching is a major security boundary.

### Required protections

- Accept only explicitly supported URL schemes, normally HTTP and HTTPS.
- Reject loopback, private, link-local, multicast, reserved, and cloud metadata destinations as appropriate.
- Validate all resolved IP addresses.
- Revalidate every redirect destination.
- Address DNS rebinding and time-of-check/time-of-use risks.
- Prevent access to internal services through browser automation.
- Apply connection and total-operation timeouts.
- Limit downloaded bytes, response sizes, page counts, and browser resource consumption.
- Avoid executing unnecessary downloads or opening unsafe file types.
- Isolate browser automation and media-processing tasks from sensitive application resources.
- Treat website text and HTML as untrusted data, never as privileged instructions.
- When website text is passed to a language model, separate it clearly from system instructions and treat the model's output as unverified. Text such as "ignore previous instructions" on a web page must not change application behavior (prompt injection).
- Read and respect `robots.txt` and identify the crawler with an honest `User-Agent`.
- Connect to the IP address that was validated, rather than resolving the hostname a second time, so that DNS rebinding cannot redirect the request after validation.

Network-level restrictions should supplement application-level validation where possible.

### Browser automation

Playwright may be used for JavaScript-rendered websites when ordinary HTTP extraction is insufficient.

Browser contexts should be isolated, temporary, and configured to restrict unnecessary network access, downloads, and resource consumption.

The browser must not gain unrestricted access to private networks simply because the target page requires JavaScript.

## 8. AI Content and Factual Grounding

The AI workflow should receive structured, relevant business data with source information where available.

The system should maintain a distinction between source facts and creative suggestions.

Recommended sequence:

```text
Website Evidence
      |
      v
Structured Business Profile
      |
      v
User Review and Corrections
      |
      v
Marketing Brief
      |
      v
Concept and Script Generation
      |
      v
Claim and Content Review
      |
      v
Approved Creative Inputs
```

The system should not invent prices, testimonials, certifications, guarantees, product specifications, or other business facts.

Where factual verification is not possible, the relevant claim should be omitted, qualified, or sent to the user for review.

## 9. Media Storage Architecture

Storage should be designed around the distinction between:

- Temporary processing files.
- Retrieved website assets.
- User-uploaded files.
- AI-generated assets.
- Final rendered outputs.

Storage requirements:

- Generate safe internal filenames.
- Do not trust user-supplied filenames or file extensions.
- Validate file type, size, and actual media content where practical.
- Keep private files outside publicly accessible application paths.
- Serve downloads through authorized, controlled mechanisms.
- Define cleanup rules for temporary files and expired exports.
- Avoid deleting assets still referenced by active projects.

The first implementation may use local storage for development. Production storage should be selected based on deployment requirements, access control, retention, and cost.

Many free hosting tiers use ephemeral disks, where files are lost on restart or redeploy. Do not rely on such a disk for user uploads, SQLite databases, or exports that must persist.

Every retrieved or uploaded asset should record its origin (website URL, user upload, or generated) and, where known, its license or usage permission, because public availability does not grant the right to reuse an image in an advertisement.

## 10. Video Rendering Pipeline

A proposed rendering workflow is:

1. Receive an approved creative configuration.
2. Validate the script, assets, and output settings.
3. Construct a structured scene plan.
4. Prepare images, clips, captions, and audio.
5. Calculate timing and transitions.
6. Render a preview where supported.
7. Render the final video.
8. Validate the resulting file.
9. Store output metadata and update job status.
10. Provide an authorized download link.

The scene plan should be represented as structured data rather than embedding all editing decisions inside one large shell command.

FFmpeg commands must be constructed safely. Avoid passing untrusted text directly into shell execution. Prefer argument lists, controlled paths, and validated parameters.

Failed rendering must not mark an export as completed.

## 11. Background Jobs and Idempotency

Some operations may be expensive or take longer than a normal HTTP request should remain open.

Suitable candidates for background processing include:

- Multi-page website analysis.
- AI content generation.
- Image and audio generation.
- Video rendering.
- Large export operations.

Job handling should define:

- A stable job identifier.
- Allowed state transitions.
- Retry limits.
- Timeout behavior.
- Cancellation behavior where supported.
- Safe cleanup.
- Recovery behavior after worker interruption.

Repeated submissions should not unintentionally create duplicate charges or duplicate final outputs. Where practical, use idempotency keys or equivalent deduplication controls.

## 12. Error Handling and Observability

Errors should be categorized by component and severity.

Examples include:

- Invalid website URL.
- Website unreachable.
- Access denied by the target website.
- Unsupported page content.
- Provider timeout.
- Provider quota or billing limit.
- Invalid generated asset.
- Media rendering failure.
- Storage failure.
- Authorization failure.

Users should receive actionable messages without unnecessary internal details.

Logs should help developers diagnose failures without exposing API keys, passwords, private credentials, or sensitive information.

## 13. Testing Architecture

Testing should cover:

### Unit tests
- URL parsing and validation.
- Business fact normalization.
- Creative configuration validation.
- Provider request construction.
- Scene-plan generation.
- Job-state transitions.

### Integration tests
- Django views and models.
- Website analysis with controlled test sites.
- Provider adapters using mocked responses.
- Asset storage and authorization.
- Media rendering with small test assets.

### Security tests
- SSRF attempts.
- Unsafe redirects.
- Unauthorized project access.
- Malicious uploads.
- Path traversal.
- Oversized responses.
- Invalid job transitions.
- Secret leakage in logs.

### End-to-end tests
- Create a project.
- Analyze a test website.
- Review the business profile.
- Generate and edit a script.
- Produce a supported media output.
- Verify the export and access permissions.

External services should be mocked in ordinary automated tests wherever practical. Live-provider tests should be controlled to avoid unexpected costs.

## 14. Environment and Configuration

Configuration should be separated from application code.

Potential configuration includes:

- Django secret key.
- Debug and allowed-host settings.
- Database connection.
- AI provider credentials.
- Storage configuration.
- Browser and crawl limits.
- Job worker configuration.
- Media processing paths.
- Logging settings.

Use environment variables or an appropriate secrets-management solution.

A `.env.example` file may document required configuration names without containing real credentials. Actual secret files must be excluded from version control.

## 15. Deployment Evolution

### Phase 1: Local Development

- Django application.
- SQLite where appropriate.
- Local development storage.
- Small, controlled website-analysis tests.
- Local FFmpeg processing.
- Mocked external AI providers where possible.

### Phase 2: Working Prototype

- Validated website analysis.
- Structured business profiles.
- Initial provider integrations.
- Functional content-generation workflow.
- Basic media rendering and export.
- Automated tests and status documentation.

### Phase 3: Production Preparation

- Production database such as PostgreSQL where appropriate.
- Secure media storage.
- Background worker infrastructure.
- Deployment configuration.
- Monitoring, backups, rate limits, and resource controls.
- Security review and operational testing.

These are proposed phases, not commitments to a specific hosting provider or infrastructure.

Under the zero-budget constraint, Phase 1 and early Phase 2 should run on the developer's own computer. Free hosting can be used for demonstrations once its limits are understood (see section 17), but it should not be assumed to support Playwright, FFmpeg rendering, or persistent file storage.

## 16. Architecture Decision Rules

Before introducing a significant new framework, service, or infrastructure component:

1. Identify the requirement it addresses.
2. Check whether the current architecture can satisfy the requirement.
3. Evaluate complexity, security, cost, portability, and maintenance.
4. Test uncertain technical assumptions.
5. Record important decisions in `docs/DECISIONS.md`.
6. Update this document when the accepted architecture changes.

## 17. Zero-Budget Tooling Candidates

This section lists candidate tools for building the product without paid services, as required by DEC-016.

**Every entry is a candidate, not an adopted dependency.** Free-tier limits, terms, and licenses change frequently. Before adopting a tool, check its current official terms, record the date and result in `docs/DECISIONS.md`, and add it only when a task actually needs it. The notes below reflect information gathered on 2026-10-27 and must be re-checked.

### 17.1 Core software (open source, no usage cost)

| Need | Candidate | Notes to verify |
|---|---|---|
| Web framework | Django | Already the chosen direction (DEC-006). |
| Database | SQLite (development), PostgreSQL (later) | Both free. Free hosted PostgreSQL offers are often time-limited; confirm before relying on one. |
| HTTP fetching | Python standard library or `httpx`/`requests` | Must be wrapped by the SSRF protections in section 7. |
| HTML parsing | Beautiful Soup | Already the chosen direction (DEC-009). |
| JavaScript-rendered pages | Playwright with Chromium | Free, but memory-hungry; likely unsuitable for small free hosting instances. |
| Image and poster composition | Pillow, or HTML/CSS templates rendered to images | No AI needed. Fonts must have licenses that allow commercial and embedded use (for example, the SIL Open Font License). |
| Video rendering | FFmpeg | Free. Some builds include GPL components; acceptable for server-side use, but check before distributing binaries. |
| Background jobs | Database-backed jobs and a worker management command | Avoids paying for or maintaining Redis. |
| Tests | Django test runner and `unittest.mock` | No extra testing framework needed initially. |
| Continuous integration | GitHub Actions | Free for public repositories; private repositories receive a limited monthly free allowance. Verify current limits. |

### 17.2 Text generation (hosted free tiers or local models)

| Candidate | Notes to verify |
|---|---|
| Google Gemini API free tier | Free access and limits vary by model and are set per project. Content sent on the free tier may be used by Google to improve its products, so private user data must not be sent without informing the user. |
| Groq API free tier (open-weight models such as Llama) | Rate limits are per organization and vary by model. Confirm the current limits and terms. |
| Local models through Ollama or similar | No usage cost and no data leaves the machine, but quality and speed depend on the developer's hardware. Check each model's license for commercial use. |
| Template-based drafts without AI | Always available. Output must be clearly presented as a template draft, never as AI analysis. |

The text-generation interface must allow switching between these options through configuration, because any free tier may change or close.

### 17.3 Speech and narration

| Candidate | Notes to verify |
|---|---|
| Piper (local text-to-speech) | The software is open source, but each voice has its own license. The Kiswahili voice (`sw_CD`) depends on the license of its training dataset, which must be confirmed before commercial use. |
| Other open speech models | Several models that support Kiswahili are licensed for non-commercial use only. Do not use those for a commercial product. |
| No narration | Always available. Videos must work with captions, text animation, and licensed music only. |

Do not use unofficial or reverse-engineered access to commercial speech services, even if it is technically free.

### 17.4 Images, video footage, and music

- AI image and video generation is deferred. Free options suitable for commercial use have not been verified.
- Use authentic website images only where the business owner confirms they have the right to use them, plus the user's own uploads.
- Use only music tracks whose license explicitly permits use in commercial advertisements, and record the license for each track.

### 17.5 Hosting

- Start with local development on the developer's computer.
- Free hosting tiers typically sleep after inactivity, have small memory and CPU allocations, cap monthly hours, and use ephemeral disks that lose files on restart. For example, Render's free web services spin down after 15 minutes without traffic and lose local files, including SQLite databases, on restart or redeploy.
- Some free hosts block or restrict outbound internet access, which makes website analysis impossible there. Check this before choosing a host.
- Free hosting is suitable for demonstrating the web interface, not for production rendering.

## 18. Definition of Architectural Success


The architecture is successful when the platform can evolve from a small working prototype into a reliable marketing production system without requiring avoidable rewrites of unrelated components.

The system must remain modular, secure, testable, factually grounded, and understandable to both human developers and AI coding assistants.

**Final rule:** The implemented repository and verified test results remain the source of truth. This document describes the intended architecture until implementation confirms otherwise.
