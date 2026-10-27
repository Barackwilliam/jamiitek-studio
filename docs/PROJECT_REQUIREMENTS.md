# Project Requirements — JamiiTek AI Marketing Studio

**Document type:** Functional and Non-Functional Requirements  
**Project:** JamiiTek AI Marketing Studio  
**Status:** Planning  
**Version:** 1.1  
**Budget constraint:** Zero budget (see `docs/DECISIONS.md`, DEC-016)

---

## 1. Purpose

This document defines the functional requirements, non-functional requirements, constraints, and acceptance criteria for JamiiTek AI Marketing Studio.

It serves as a shared reference for developers, AI coding assistants, testers, and product stakeholders.

All requirements describe intended behavior. A requirement must not be considered implemented until the relevant functionality exists and has been verified.

## 2. Product Objective

The system shall enable users to transform information from their business websites into professional marketing content through an integrated AI-assisted workflow.

The platform shall prioritize:

- Accurate understanding of business information.
- High-quality marketing outputs.
- Broad compatibility with different website technologies.
- Flexible creative customization.
- Reliable media production.
- Secure handling of websites, files, credentials, and user data.
- An intuitive workflow for users without advanced technical skills.

## 3. User Types

The initial product may support the following user types.

### 3.1 Guest or New User

A visitor who can learn about the platform and, depending on the implemented access policy, try selected features.

### 3.2 Registered User

A user who can create and manage marketing projects, analyze websites, generate content, save work, and export available results.

### 3.3 Administrator

A user authorized to manage system settings, supported providers, usage limits, operational health, and other administrative functions.

Authorization must be enforced on the server. Hiding interface elements alone is not sufficient security.

## 4. Functional Requirements

### FR-01: Project Creation

The system shall allow users to create identifiable marketing projects.

Each project should support, where implemented:

- Project name.
- Business or brand name.
- Website URL.
- Project status.
- Creation and modification timestamps.
- Associated website analysis.
- Generated content and creative settings.
- Export history.

Users must be able to distinguish between different projects and avoid accidentally mixing content from unrelated businesses.

**Acceptance criteria:**
- A valid project can be created and retrieved.
- Project data remains associated with the correct user.
- Invalid input is rejected with a clear explanation.
- Unauthorized users cannot access another user's private project.

### FR-02: Website URL Submission and Validation

The system shall accept a website URL as the starting point for a marketing project.

It shall validate URL syntax, supported protocols, hostname resolution, redirects, and destination addresses before accessing the target.

The implementation must defend against SSRF and unsafe network destinations, including loopback, private, link-local, and cloud metadata addresses.

URL validation must account for DNS resolution changes, redirect chains, and alternate IP representations where relevant.

**Acceptance criteria:**
- Valid public website URLs can proceed to analysis.
- Malformed or unsupported URLs are rejected.
- Unsafe destinations are blocked.
- Redirects are revalidated at each step.
- Requests have appropriate time, response-size, and resource limits.

### FR-02A: Manual Business Information Entry

The system shall allow users to enter or paste business information manually when they have no website, when the website cannot be analyzed, or when they prefer not to submit a URL.

Manually entered information shall be recorded as user-provided and follow the same review and approval workflow as extracted information.

**Acceptance criteria:**
- A project can proceed to content generation without a website URL.
- A failed website analysis offers manual entry as an alternative.
- User-provided facts are distinguishable from extracted facts.

### FR-03: Website Analysis

The system shall analyze publicly accessible website content to understand the business represented by the submitted URL.

The analysis workflow should adapt to website complexity rather than depend on one fixed HTML structure.

It should support appropriate combinations of:

- HTTP requests and HTML parsing.
- Browser automation for JavaScript-rendered content.
- Internal link discovery.
- Page title and metadata extraction.
- Main content extraction.
- Product and service information extraction.
- Image and brand asset discovery.
- Relevant contact and business information.
- Sitemap discovery where appropriate.

The system should handle common websites, content management systems, online stores, and custom websites where technically feasible.

It must not promise compatibility with every website. Login-protected, blocked, highly dynamic, or technically incompatible sites may require user assistance or a clear limitation message.

**Acceptance criteria:**
- Analysis produces a structured result when sufficient public content is available.
- Failed pages are recorded without necessarily failing the entire analysis.
- The user can see which pages were analyzed and which failed.
- The system does not treat arbitrary page content as trusted instructions.
- The user can retry an unsuccessful analysis.

### FR-04: Page Selection and Crawl Limits

The system shall support controlled website exploration.

Where appropriate, users should be able to review discovered pages and select which ones are relevant to the project.

The crawler shall apply configurable limits to page count, crawl depth, request rate, file size, execution time, and total resource consumption.

It should prioritize relevant business pages, such as:

- Home.
- About.
- Products.
- Services.
- Product details.
- Pricing.
- Contact.
- Relevant campaign or landing pages.

The system must respect applicable access restrictions and avoid aggressive crawling. It shall read and honor `robots.txt`, identify itself with an honest user agent, and limit its request rate per website.

**Acceptance criteria:**
- Crawl limits are enforced.
- Duplicate URLs are handled consistently.
- Irrelevant or unsupported pages can be excluded.
- Users can understand the scope of the analysis.

### FR-05: Business and Brand Profile

The system shall convert collected website information into a structured business profile.

Potential fields include:

- Business name.
- Business description.
- Products and services.
- Target audiences.
- Brand voice.
- Value propositions.
- Published prices.
- Contact information.
- Brand colors and visual identity.
- Available logos and images.
- Geographic markets and supported languages.

Each important fact should retain its source or provenance where practical.

The system should distinguish confirmed information from inferred suggestions and unknown details.

**Acceptance criteria:**
- The profile is editable before major content generation.
- Unsupported facts are not presented as verified.
- Users can correct incorrect extraction.
- Updates to the profile can be used in subsequent generation steps.

### FR-06: Content Accuracy and Approval

Generated content must be grounded in the available business profile and its supporting sources.

The system shall not invent business facts, prices, product features, testimonials, certifications, guarantees, customer numbers, awards, or facilities.

When essential information is missing, the system should ask the user, omit the claim, or use clearly marked draft language that requires approval.

**Acceptance criteria:**
- Unsupported factual claims can be identified and removed before export.
- Users can review important claims.
- User-provided corrections are reflected in subsequent generation.
- The system does not silently convert uncertain inferences into verified facts.

### FR-07: AI Marketing Concept Generation

The system shall generate marketing concepts based on the business profile and user-selected objectives.

Possible objectives include:

- Brand awareness.
- Product promotion.
- Service promotion.
- Lead generation.
- Website traffic.
- Sales conversion.
- Event promotion.
- Social media engagement.

Concepts should account for the target audience, intended platform, tone, language, content format, and available assets.

The system should provide useful variations rather than returning essentially identical concepts.

**Acceptance criteria:**
- Concepts reflect the selected business and objective.
- Users can regenerate or refine concepts.
- Missing inputs are handled transparently.
- Generation failures produce actionable error messages.

### FR-08: Script and Copy Generation

The system should generate relevant marketing text, including:

- Video scripts.
- Headlines.
- Captions.
- Calls to action.
- Advertisement copy.
- Scene descriptions.
- Voice-over scripts.
- Subtitles.
- Social media descriptions.

Users should be able to edit generated text before it is used to produce media.

Text should be appropriate for the selected language, audience, platform, and requested duration.

**Acceptance criteria:**
- Generated text can be reviewed and edited.
- Saved changes persist.
- The system does not overwrite user edits without a clear action.
- Scripts and captions remain associated with the correct project and version.

### FR-09: Creative Configuration

The system should allow users to customize relevant creative settings, including:

- Content objective.
- Audience.
- Language.
- Tone and style.
- Duration.
- Aspect ratio.
- Brand colors.
- Logo usage.
- Selected images.
- Narration preferences.
- Music preferences.
- Caption settings.
- Calls to action.

Available options must reflect the actual capabilities of the selected production workflow.

**Acceptance criteria:**
- Supported settings can be selected and saved.
- Invalid combinations are rejected or resolved with an explanation.
- The user can review settings before starting an expensive generation task.

### FR-10: Asset Management

The system should support collecting, selecting, and organizing assets used in a project.

Assets may include:

- Logos.
- Product images.
- Website photographs.
- Uploaded images.
- Generated images.
- Audio files.
- Video clips.
- Captions and other supporting files.

The platform must respect applicable rights and permissions. Public accessibility does not automatically mean an asset is free of copyright restrictions.

Uploaded and retrieved files must be validated and stored securely.

**Acceptance criteria:**
- Assets are associated with the correct project.
- Unsupported or unsafe files are rejected.
- Missing assets are handled gracefully.
- The user can distinguish website assets from AI-generated or uploaded assets where practical.

### FR-11: Image and Poster Generation

The long-term platform should support marketing image generation and poster creation.

Under the zero-budget constraint, the first poster workflow should compose posters from templates, approved business images, brand colors, and approved text, without requiring an AI image-generation service.

Generated designs should use the approved business information, appropriate brand assets, and the user's selected creative direction.

Text-heavy graphics should be checked for readability, spelling, layout problems, and unsupported claims.

**Acceptance criteria:**
- Supported image outputs can be previewed.
- The user can request revisions.
- Image generation failures do not corrupt the project.
- Exported files meet the selected output specifications.

### FR-12: Audio and Narration

The platform should support narration and related audio features through suitable providers or local tools.

Possible features include:

- Text-to-speech narration.
- Voice and language selection.
- Background music.
- Audio trimming.
- Volume adjustment.
- Synchronization with video scenes.
- Captions aligned with narration where supported.

Provider capabilities and usage restrictions must be respected.

Narration shall be optional. Under the zero-budget constraint, a free voice licensed for commercial use may not be available for every language, so the video workflow must produce a complete result using captions and on-screen text without narration.

**Acceptance criteria:**
- Audio tasks report their status.
- Missing or failed audio does not silently produce a misleading final export.
- Audio levels and synchronization are checked during rendering where feasible.
- Users can preview available audio before final export.

### FR-13: Video Generation and Rendering

The platform shall progressively support generating promotional videos from selected creative components.

The workflow may combine:

- Website images and approved business assets.
- AI-generated supplementary footage.
- Motion graphics.
- Animated text.
- Transitions.
- Narration.
- Background music.
- Captions.
- Calls to action.

The system should use an appropriate rendering pipeline, with FFmpeg as a planned option.

**Acceptance criteria:**
- A supported project can produce a playable MP4 file.
- Rendering errors are reported clearly.
- Temporary files are managed safely.
- Exported dimensions, duration, frame rate, and audio settings are validated against the selected output profile.
- A failed render can be retried without unnecessarily repeating unrelated expensive operations.

### FR-14: Output Formats

The system should progressively support commonly used aspect ratios:

- 9:16 vertical.
- 16:9 horizontal.
- 1:1 square.

Other resolutions, codecs, frame rates, and formats may be added according to product priorities.

The layout should adapt to each aspect ratio rather than simply stretch or crop essential content.

**Acceptance criteria:**
- The output matches the selected aspect ratio.
- Important text and brand elements remain within safe visual areas.
- Cropping and resizing do not unnecessarily hide essential content.

### FR-15: Editing and Revision

Users should be able to revise generated work before final export.

The initial editing workflow should prioritize editable scripts, scenes, images, narration, captions, and creative settings.

A complete timeline editor may be considered later if justified by user needs and technical feasibility.

**Acceptance criteria:**
- User edits are saved.
- Changes can be previewed before export.
- The system distinguishes saved changes from an older rendered version.
- Regeneration affects only the intended content where technically practical.

### FR-16: Preview, Export, and Download

Users should be able to preview supported outputs and export the final result.

The platform should provide clear export status and useful error feedback.

Download links must be authorized, time-limited where appropriate, and protected from access by unauthorized users.

**Acceptance criteria:**
- Successful exports are available to the authorized user.
- Incomplete exports are not presented as successful.
- Export files are checked for existence and basic validity.
- Expired or unavailable files produce a clear message.

### FR-17: Project Saving and History

The system should preserve project data and important generation results.

Where implemented, it should maintain relevant history for scripts, settings, assets, and exports.

Users should be able to reopen a project without losing saved work.

**Acceptance criteria:**
- Saved projects can be reopened.
- Project records remain isolated between users.
- Changes are persisted reliably.
- Deletion and retention behavior is documented and implemented consistently.

### FR-18: AI and Media Provider Integration

The architecture should separate business logic from external AI and media providers.

Possible provider categories include:

- Language models.
- Image generation.
- Video generation.
- Speech synthesis.
- Music or audio generation.
- Other specialized media services.

Provider integrations should use consistent internal interfaces where practical.

The platform should support configurable provider selection, capability checks, error handling, usage tracking, and appropriate fallbacks.

**Acceptance criteria:**
- Provider-specific logic is isolated from core project workflows.
- Missing credentials are handled safely.
- Provider failures do not crash unrelated features.
- Unsupported capabilities are not falsely advertised.
- Fallback behavior is tested where implemented.

### FR-19: Background Processing

Long-running website analysis, media generation, and video rendering should not unnecessarily block normal web requests.

The architecture should support background processing when the workload requires it.

Jobs should expose relevant states, such as queued, running, completed, failed, and cancelled where supported.

**Acceptance criteria:**
- Job status is persisted or recoverable according to the chosen architecture.
- Repeated requests do not unintentionally duplicate expensive work.
- Failures are recorded without exposing secrets.
- Retry behavior is bounded and appropriate to the task.

### FR-20: User Interface

The interface should be professional, responsive, understandable, and usable on desktop and mobile devices.

The primary workflow should guide users through:

1. Creating a project.
2. Entering a website URL or business information.
3. Reviewing website analysis, where a URL was provided.
4. Confirming business information.
5. Choosing a marketing objective.
6. Generating concepts and scripts.
7. Configuring creative settings.
8. Generating and previewing assets.
9. Editing and exporting the result.

The user should understand what is happening during long-running operations.

**Acceptance criteria:**
- Forms provide useful validation messages.
- Loading, success, empty, and error states are clear.
- Main workflows work on supported screen sizes.
- Keyboard accessibility and readable contrast are considered.
- Destructive and potentially expensive actions require appropriate confirmation.

## 5. Non-Functional Requirements

### NFR-01: Security

- Validate and sanitize all untrusted input.
- Apply appropriate Django security protections.
- Enforce authentication and authorization where required.
- Protect against SSRF, unsafe uploads, path traversal, injection, and unauthorized file access.
- Store secrets outside source control.
- Avoid logging passwords, API keys, and sensitive content unnecessarily.
- Treat website content passed to language models as untrusted, and prevent instructions embedded in website text from changing application behavior (prompt injection).
- Inform users which external services receive their business information, particularly when a free tier's terms allow the provider to use submitted content.

### NFR-02: Reliability

- Handle partial failures gracefully.
- Use bounded retries and timeouts.
- Preserve user work when external services fail.
- Provide meaningful error messages and diagnostic logs.
- Avoid marking incomplete operations as successful.

### NFR-03: Performance

- Apply configurable resource limits to crawling and rendering.
- Avoid unnecessary repeated website requests or expensive AI calls.
- Use background tasks for operations that would otherwise block web requests.
- Monitor bottlenecks before introducing premature optimization.

### NFR-04: Scalability

The initial architecture may be suitable for a small deployment, but components should be organized so that database, task-processing, storage, and provider infrastructure can evolve as demand grows.

### NFR-05: Maintainability

- Use modular Django applications and clearly defined component responsibilities.
- Keep views, business logic, provider integrations, and media-processing code appropriately separated.
- Use configuration rather than hard-coded secrets and environment-specific values.
- Maintain readable code, useful tests, and current documentation.

### NFR-06: Portability

The initial development environment is Windows with Visual Studio Code. Hosting environments, including free tiers, usually run Linux. Setup and processing workflows should be documented and tested for both.

Operating-system-specific assumptions should be isolated where practical.

### NFR-07: Accessibility and Usability

- Use clear labels and understandable error messages.
- Support keyboard navigation for key workflows.
- Provide sufficient contrast and readable typography.
- Avoid unnecessary complexity for users without technical backgrounds.

### NFR-08: Cost Control

The project operates under a zero-budget constraint (DEC-016). The initial system shall not depend on any paid service.

The platform should track free-tier quota usage, and later costs, where provider information makes that possible. When a free quota is exhausted, the system shall report this clearly and preserve the user's work instead of failing silently or switching to an unapproved paid option.

Potential controls include:

- Configurable usage limits.
- Maximum generation duration.
- Preview quality options.
- Reuse of existing assets.
- Avoidance of unnecessary regeneration.
- Caching of analysis and generation results.
- Provider selection based on cost and quality.

Cost estimates must be presented as estimates when actual charges are uncertain.

### NFR-09: Observability

Important operations should have structured status information and useful logs.

Operational diagnostics must avoid exposing secrets, sensitive user data, or unrestricted access to private media.

### NFR-10: Data Integrity

Database relationships, project ownership, asset references, and job states must remain consistent.

Schema changes should use appropriate migrations, and destructive operations must be handled carefully.

### NFR-11: Language Support

The product is intended for multilingual use. Kiswahili and English are the proposed initial languages (pending OPEN-002). Language support must be tested per feature, because a tool that supports a language for text may not support it for speech or captions.

### NFR-12: Rights and Licensing

Assets, fonts, music, voices, and models must be used only within the terms of their licenses. The system should record the source and, where known, the license of each asset used in an export.

## 6. Initial Technical Constraints

The planned initial technology direction is:

- Python and Django.
- HTML, CSS, and vanilla JavaScript.
- SQLite during early development.
- PostgreSQL as a possible later database.
- Playwright and Beautiful Soup for suitable website-analysis tasks.
- FFmpeg for media processing.
- Git and GitHub for version control.

These choices may be revised through documented decisions if implementation evidence justifies a change.

Under DEC-016, only free and open-source software and free service tiers may be used. Each tool's license and terms must be verified for commercial use before adoption. Paid services may be considered only through a new recorded decision.

## 7. Out of Scope for the Initial Foundation

The following are not required before the core workflow has been validated:

- A full professional video timeline editor.
- Automated advertising campaign purchasing.
- Autonomous publication to every social platform.
- Guaranteed compatibility with every website.
- Guaranteed studio-quality AI-generated footage.
- Enterprise-scale distributed infrastructure.
- Every possible AI provider or export format.

These may be evaluated in later phases. Excluding them initially does not prevent the architecture from supporting them in the future.

## 8. Definition of Done

A feature may be marked complete only when:

1. Its intended behavior is implemented.
2. Relevant input validation and failure handling exist.
3. Security and authorization implications are addressed.
4. Appropriate tests have been added or updated.
5. Relevant checks have been executed and their results recorded.
6. Documentation reflects the actual behavior.
7. Known limitations are documented.
8. The implementation does not rely on unacknowledged placeholders for its core behavior.

A feature that is implemented but not tested must be reported accurately as unverified.

## 9. Requirements Change Management

New requirements and significant changes should be documented.

When a requirement changes, the responsible developer or AI assistant should consider the effect on:

- User workflows.
- Architecture.
- Security.
- Existing data.
- Testing.
- Dependencies.
- Costs.
- Documentation.
- Previously implemented features.

Significant decisions should be recorded in `docs/DECISIONS.md`.

## 10. Final Principle

JamiiTek AI Marketing Studio must be developed as a dependable marketing production platform, not merely as a collection of AI API calls.

Every implemented feature should contribute to a coherent user workflow, maintain factual accuracy, protect user data, and deliver a verifiable result.
