# AGENTS.md — AI Coding Agent Instructions for JamiiTek AI Marketing Studio

## 1. Project Identity

You are working on **JamiiTek AI Marketing Studio**, an ambitious AI-powered marketing creation platform developed under the JamiiTek brand.

The long-term goal is to build a flexible, reliable, and globally competitive product that can understand diverse websites and transform their business information into high-quality marketing content.

Read `AI_PROJECT_GUIDE.md` and `PROJECT_MASTER.md` when they are available before performing substantial work.

These documents describe the intended product vision. Always inspect the actual repository to determine what has been implemented.

## 2. Primary Objective

Build real, working, maintainable software.

Do not confuse:

- A visual mockup with a working feature.
- A placeholder with a real integration.
- A successful API request with a validated final result.
- A proposed architecture with an implemented architecture.
- A demonstration with production readiness.

Never claim a feature works unless the implementation and available verification support that claim.

## 3. Mandatory Workflow

Before starting a significant task:

1. Inspect the repository structure.
2. Read relevant project instructions and documentation.
3. Check the current Git status.
4. Examine the existing implementation.
5. Identify the exact files and components affected.
6. Understand the expected behavior and acceptance criteria.
7. Identify important dependencies, risks, and assumptions.
8. Prepare a concise implementation plan.

Then implement the task in small, coherent steps.

After implementation:

1. Review all relevant changes.
2. Run applicable tests.
3. Perform additional verification where appropriate.
4. Check for regressions.
5. Inspect the Git diff.
6. Update relevant documentation.
7. Report the actual result and any remaining limitations.

Do not skip verification merely because the change appears simple.

## 4. Preserve Existing Work

Do not unnecessarily rewrite, rename, delete, or replace existing files, functions, classes, database structures, UI components, or working features.

Before changing existing behavior:

- Understand how it currently works.
- Identify dependencies and potential side effects.
- Preserve unrelated functionality.
- Prefer minimal, focused changes.

Never overwrite uncommitted user work.

Never run destructive Git commands, delete significant user data, or perform irreversible operations without explicit authorization.

If a requested change requires a major architectural alteration, explain the impact before proceeding.

## 5. Architecture and Code Quality

Use the existing architecture unless there is a justified reason to change it.

The initial technology direction is:

- Python and Django for the backend.
- HTML, CSS, and vanilla JavaScript for the frontend.
- SQLite for initial local development.
- PostgreSQL when appropriate for production.
- Playwright for browser automation where appropriate.
- Beautiful Soup for HTML parsing where useful.
- FFmpeg for video rendering where appropriate.
- Git and GitHub for version control.

Do not introduce every technology automatically.

Choose tools based on actual requirements, compatibility, maintainability, performance, and cost.

Keep modules focused and separate concerns such as website analysis, AI orchestration, content generation, media processing, rendering, and user-facing workflows.

Avoid unnecessary abstractions, duplicated logic, giant files, and tightly coupled provider integrations.

Do not migrate frameworks or replace working dependencies without a clear benefit.

## 6. Universal Website Compatibility

Treat website analysis as a major product capability.

Do not assume that all websites use the same framework, HTML structure, CMS, navigation system, or rendering method.

Where appropriate, account for:

- Static HTML.
- JavaScript-rendered content.
- Multiple pages.
- E-commerce products.
- Structured metadata.
- Different image formats.
- Different page layouts.
- Different languages.
- Missing or inconsistent information.

Use appropriate extraction strategies and provide graceful failure handling.

Do not claim that every website is supported.

If a website cannot be accessed or analyzed completely, explain what failed and provide practical alternatives.

Never invent extracted information.

## 7. AI and Content Accuracy

All AI-generated marketing content must be grounded in available information.

Do not invent:

- Products or services.
- Prices or discounts.
- Customer testimonials.
- Reviews or ratings.
- Certifications or awards.
- Statistics.
- Guarantees.
- Business locations.
- Product capabilities.
- Booking availability.
- Partnerships or endorsements.

When factual information is uncertain, identify the uncertainty or ask for clarification.

Keep AI-generated creative suggestions distinguishable from verified business facts.

Where practical, retain source references for factual claims so they can be reviewed.

Require appropriate user approval before finalizing important marketing claims.

## 8. AI Provider Independence

Avoid unnecessarily coupling the application to one AI provider.

Where justified, use clear interfaces for text generation, website understanding, image generation, video generation, speech generation, and other AI capabilities.

Provider integrations should be replaceable without rewriting unrelated business logic.

Before adding a provider, check its current capabilities, pricing, API requirements, language support, licensing, and commercial restrictions.

Do not hardcode API keys or provider credentials.

Use environment variables and safe configuration patterns.

If an API is unavailable, report the issue honestly and implement an appropriate error-handling strategy.

**Zero budget (DEC-016):** Do not add any paid service, or any service that requires a payment card, without the owner's explicit approval. Use free and open-source tools and free tiers only, verify the current license and terms of each one before adopting it, and record the result in `docs/DECISIONS.md`. Never make routine tests consume a hosted free-tier quota.

Do not silently replace a real provider with fake output.

## 9. Security Requirements

Treat external websites, uploaded files, generated media, and user-provided content as potentially untrusted.

For website analysis, apply appropriate protections against server-side request forgery, including:

- Blocking loopback and private network destinations.
- Blocking cloud metadata endpoints.
- Validating DNS resolution and redirects.
- Rechecking destinations after redirects.
- Enforcing timeouts and response-size limits.
- Isolating browser automation.
- Restricting access to local files and internal services.

Also follow appropriate Django security practices, including CSRF protection, authentication and authorization, safe file uploads, secure session handling, and secret management.

Never commit credentials, passwords, API keys, access tokens, or private user data.

Do not disable security controls just to make a feature work.

## 10. Database and Data Integrity

Inspect existing models and migrations before changing database structures.

When schema changes are required:

1. Update the relevant models.
2. Create appropriate migrations.
3. Check migration consistency.
4. Apply migrations in the intended development environment.
5. Test affected functionality.
6. Document important changes.

Avoid destructive schema changes without authorization.

Do not delete user projects, media, or business information as an incidental consequence of unrelated work.

Preserve approved scripts and editing decisions when regenerating content.

## 11. Frontend and User Experience

Build a responsive, professional, accessible interface.

Ensure that:

- Forms validate input.
- Buttons perform their stated actions.
- Loading states reflect real work.
- Errors are understandable.
- Empty states provide useful guidance.
- Navigation is consistent.
- Text remains readable.
- Controls work on desktop and mobile.
- Important actions are keyboard accessible.

Do not create decorative controls that appear functional but do nothing.

Do not simulate completed AI processing or video rendering.

Prioritize clarity, usability, and reliability over unnecessary visual effects.

## 12. Video and Media Processing

When working on video production:

- Validate source media.
- Check output paths and file permissions.
- Use appropriate resource limits.
- Handle failed rendering jobs.
- Verify output files exist and are readable.
- Check relevant video and audio properties.
- Handle temporary files safely.
- Avoid unnecessary repeated processing.
- Preserve user-approved assets and edits.

Do not report successful rendering merely because an FFmpeg command was submitted.

Where appropriate, validate the final media file and inspect its technical properties.

Never use copyrighted or restricted assets without appropriate authorization or licensing.

## 13. Background Jobs and Reliability

Long-running tasks such as website analysis, AI generation, and video rendering should not unnecessarily block normal web requests.

When the project requires background processing, implement an appropriate job architecture with:

- Persistent job status.
- Error reporting.
- Timeouts.
- Controlled retries.
- Cancellation where appropriate.
- Duplicate-work prevention.
- Resource limits.
- Progress based on actual processing.
- Safe recovery from partial failures.

Do not add a complex task queue until the requirements justify it.

## 14. Testing Rules

Write or update tests for meaningful functionality.

Test appropriate scenarios, including:

- Valid and invalid inputs.
- Successful processing.
- Missing website information.
- External service failures.
- Permission errors.
- Malformed media.
- Rendering failures.
- Security-sensitive edge cases.
- Existing functionality that could regress.

Run the tests that are available and relevant.

Clearly state which tests were executed and their results.

Never fabricate test results or claim full coverage without evidence.

## 15. Dependencies and Environment

Before installing a dependency:

1. Determine whether an existing dependency already solves the problem.
2. Check compatibility with the current Python and Django versions.
3. Consider maintenance, licensing, security, and operating cost.
4. Add only the dependencies that are needed.
5. Update dependency files appropriately.
6. Explain any required installation steps.

Do not expose local machine paths, private configuration, or environment-specific assumptions as universal requirements.

Keep `.env` and other secret files out of version control.

Maintain a safe `.env.example` containing configuration names and non-sensitive example values only.

## 16. Documentation Rules

Keep project documentation consistent with the implementation.

Update relevant documents when changes affect requirements, architecture, installation, testing, decisions, or project status.

Use these files where applicable:

- `AI_PROJECT_GUIDE.md`
- `PROJECT_MASTER.md`
- `README.md`
- `docs/PROJECT_REQUIREMENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATUS.md`
- `docs/DECISIONS.md`
- `docs/TASKS.md`
- `docs/TESTING.md`

Do not claim that a document exists unless it has been created.

Do not record planned functionality as completed functionality.

When documentation conflicts with the code, investigate and report the discrepancy.

## 17. Git Discipline

Before significant changes, inspect:

- Current branch.
- Working-tree status.
- Recent commits.
- Existing user modifications.

Keep changes focused and reviewable.

Do not discard user changes.

Do not force-push, reset, clean, or otherwise perform destructive Git operations without explicit authorization.

Use clear commit messages when asked to commit.

Never include secrets, private user data, or unnecessary generated media in commits.

## 18. Handling Ambiguity

If requirements are unclear, determine whether the ambiguity materially affects correctness, security, cost, architecture, or user experience.

Ask a concise clarifying question when an important decision cannot safely be inferred.

For small, reversible decisions, use a sensible default and document the assumption.

Do not repeatedly ask questions that have already been answered in the project documentation.

If a task conflicts with an established product decision, explain the conflict and recommend a solution.

## 19. Required Task Handoff

After completing a substantial task, report:

**Task:** The requested objective.

**Findings:** Relevant repository state and constraints.

**Files Changed:** Exact file paths and the nature of the changes.

**Implementation:** What now works and what remains incomplete.

**Verification:** Tests and checks actually performed, with results.

**Outstanding Issues:** Known limitations, risks, and failures.

**Documentation:** Documents updated.

**Next Step:** The next logical task based on the verified project state.

Include exact commands when useful.

Be concise but sufficiently detailed for another developer or AI assistant to continue the work.

## 20. New Session Initialization

At the beginning of a new coding session:

1. Read this file.
2. Read `AI_PROJECT_GUIDE.md` if available.
3. Read `PROJECT_MASTER.md` and `README.md` if available.
4. Read relevant architecture and requirements documents.
5. Inspect the repository and Git status.
6. Verify the current implementation.
7. Review the recorded project status.
8. Identify the next appropriate task.
9. Continue without assuming that unverified previous work exists.

If the repository is empty or has not been created, establish the required foundation before implementing advanced features.

## 21. Final Rule

Every change must support the long-term success of JamiiTek AI Marketing Studio.

Build real functionality, preserve consistency, prioritize security, test important behavior, document decisions, and avoid unnecessary complexity.

Do not sacrifice correctness for speed or claim superiority without evidence.

**Think globally. Build incrementally. Verify honestly. Preserve the project.**
