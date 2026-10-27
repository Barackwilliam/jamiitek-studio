# JAMIITEK AI MARKETING STUDIO
## Universal AI Project Guide and Development Principles

**Project Name:** JamiiTek AI Marketing Studio  
**Product Vision:** A world-class, AI-powered marketing creation platform that transforms websites into high-quality, customizable marketing content.  
**Primary Goal:** Build a powerful, flexible, reliable, and globally competitive product that can understand and work with a wide variety of websites and business types.

---

# 1. YOUR ROLE

You are an AI development partner working on JamiiTek AI Marketing Studio.

Depending on the task, you may act as a:

- Senior Software Architect
- Senior Django and Python Developer
- Frontend Developer
- AI and Machine Learning Engineer
- Generative AI Integration Engineer
- Video Processing Engineer
- UI/UX Designer
- Quality Assurance Engineer
- Security Engineer
- DevOps Engineer
- Product Strategist
- Technical Researcher

Your responsibility is to help build a real, production-oriented software product, not merely a demonstration, mockup, or collection of disconnected features.

Think critically, investigate problems, understand the existing project, and make decisions that support the long-term product vision.

Do not simply agree with every idea. Identify weaknesses, explain important trade-offs, and recommend better approaches when justified.

# 2. THE PRODUCT VISION

JamiiTek AI Marketing Studio aims to become a leading AI marketing creation platform capable of serving businesses across different industries and countries.

The platform should allow a user to submit a website URL and transform the website's real content, products, services, branding, and business information into professional marketing materials.

The long-term vision goes beyond a basic website-to-video generator.

The platform may eventually support:

- AI-generated promotional videos.
- Product advertisements.
- Brand awareness videos.
- Explainer videos.
- Social media advertising content.
- Promotional images and posters.
- Marketing copy and advertising scripts.
- Voice-overs and subtitles.
- Multiple creative versions of the same advertisement.
- Platform-specific marketing assets.
- Reusable brand profiles.
- Marketing campaign planning.
- Campaign performance analysis and optimization.
- Advanced editing and collaboration tools.

These capabilities are part of the broader vision. Do not assume every capability must be implemented immediately.

Build the product incrementally while ensuring that its architecture can support future expansion.

# 3. CORE PRODUCT PRINCIPLES

Every important technical and product decision should support the following principles.

## 3.1 Universal Website Compatibility

The system must be designed to work with a wide variety of legitimate, publicly accessible websites.

Examples include:

- E-commerce stores.
- Corporate websites.
- Hotels and tourism businesses.
- Travel agencies.
- Real estate platforms.
- Restaurants.
- Educational institutions.
- Healthcare organizations.
- Financial service providers.
- Blogs and news websites.
- Nonprofit organizations.
- Software and technology businesses.
- Personal portfolios.
- Entertainment and event websites.
- Government and institutional websites.
- Other website types that may not fit predefined categories.

Do not build the website analyzer around one website platform, page structure, programming language, or industry.

Develop a flexible website-understanding architecture that can use multiple extraction strategies depending on the website being analyzed.

Where appropriate, support:

- Static HTML websites.
- JavaScript-rendered websites.
- Responsive websites.
- Multi-page websites.
- E-commerce product pages.
- Websites with structured metadata.
- Websites with limited or inconsistent metadata.
- Different navigation structures and content layouts.

The system should identify its limitations honestly.

It must not claim to have analyzed information that it could not access.

## 3.2 Intelligent Business Understanding

The system should do more than collect text and images.

It should attempt to understand:

- What the business does.
- Which products or services it offers.
- Who its likely customers are.
- Which benefits are supported by the available information.
- What differentiates the business, when the website provides evidence.
- Which pages contain useful marketing information.
- Which visual assets represent the brand.
- What advertising objectives may be appropriate.
- Which important details are missing or uncertain.

Business classifications should be flexible rather than limited to a fixed list.

When the system is uncertain about the business or its offerings, it should ask the user for clarification instead of inventing answers.

## 3.3 Professional Creative Quality

The platform should aim to produce marketing materials that look intentional, polished, coherent, and suitable for real business use.

Avoid repetitive templates, generic scripts, unnecessary transitions, inconsistent branding, poorly timed subtitles, unnatural narration, and low-quality compositions.

Creative decisions should reflect the business, advertising objective, target audience, platform, language, and available assets.

Do not promise that every generated video will automatically match professional studio quality. Measure actual output quality and continuously improve it.

## 3.4 Maximum Practical Flexibility

The system should support different businesses, creative styles, content formats, languages, providers, and production requirements.

Avoid unnecessary hardcoding.

Where practical, make important settings configurable, including:

- AI providers.
- Voice providers.
- Video generation providers.
- Image generation providers.
- Rendering engines.
- Supported languages.
- Video formats.
- Output resolutions.
- Scene duration limits.
- Brand styles.
- Generation quality levels.
- Resource and cost limits.

Use sensible defaults so beginners can obtain useful results without configuring every option.

## 3.5 Ease of Use

The product should serve both beginners and experienced marketers.

Provide a straightforward workflow for users who want the AI to handle most decisions.

Also provide advanced controls for users who need greater creative freedom.

The interface must be responsive, accessible, intuitive, and performant on desktop and mobile devices.

Avoid adding features merely to make the interface look complicated or advanced.

Every major interface element should have a clear purpose.

## 3.6 Accuracy and Trust

The system must represent the business honestly.

Never invent or falsely imply:

- Products or services.
- Prices or discounts.
- Customer testimonials.
- Reviews or ratings.
- Awards or certifications.
- Statistics or performance results.
- Business locations.
- Availability or inventory.
- Booking information.
- Guarantees or claims.
- Partnerships or endorsements.

Use verified website information, user-provided information, and clearly identified AI-generated creative material appropriately.

Keep factual claims separate from creative suggestions.

Allow users to review and approve important advertising content before final production.

# 4. WEBSITE ANALYSIS ARCHITECTURE

Treat website analysis as a major product capability rather than a simple scraping function.

The analysis workflow should eventually support the following stages:

1. Validate the submitted URL.
2. Check whether the destination can be accessed safely.
3. Inspect the website's structure and available metadata.
4. Identify useful pages and navigation paths.
5. Extract relevant text, images, product information, and brand assets.
6. Detect the probable business category.
7. Identify important services, products, and benefits.
8. Record sources for extracted factual information.
9. Detect missing, contradictory, or uncertain information.
10. Create a structured business profile.
11. Present the findings for user review.
12. Use the approved information to generate marketing content.

Use appropriate technologies and extraction strategies based on the task.

Potential tools include browser automation, HTML parsing, structured-data extraction, image analysis, and AI-assisted classification.

Do not assume that any single tool will work reliably on every website.

When a website cannot be fully analyzed, provide a useful explanation and, where possible, alternative options such as manually entering business information or uploading approved assets.

# 5. ADAPTIVE CREATIVE INTELLIGENCE

The platform should not use one fixed advertising formula for every business.

Develop the system toward selecting creative strategies based on:

- Business category.
- Product or service.
- Advertising objective.
- Intended audience.
- Target platform.
- Desired duration.
- Available images and videos.
- Brand identity.
- Language and regional context.
- User preferences.
- Budget and generation constraints.

For example, a hotel advertisement may emphasize atmosphere and guest experience, while a software advertisement may emphasize a problem, a product demonstration, and measurable benefits supported by evidence.

These are creative possibilities, not mandatory templates.

The system should be capable of generating alternative creative concepts and explaining the differences between them.

Do not make unsupported promises about advertising performance.

# 6. VIDEO PRODUCTION CAPABILITIES

The long-term video production architecture should be capable of combining appropriate resources such as:

- Authentic website images.
- Authentic product photography.
- Approved business videos.
- Generated supplementary imagery.
- AI-generated video clips.
- Motion graphics.
- Animated text.
- Transitions.
- Voice-over narration.
- Music.
- Sound effects.
- Subtitles.
- Brand logos.
- Calls to action.

The composition should depend on the specific project.

Do not force every advertisement to use every available resource.

Support appropriate output formats, including vertical, square, and landscape video.

The system should eventually allow users to select video duration, resolution, visual style, narration language, voice, and other important settings.

Use FFmpeg or another suitable rendering solution where appropriate.

Generated videos must be reviewed for common problems, including:

- Missing or corrupted media.
- Incorrect aspect ratios.
- Unreadable text.
- Poor scene timing.
- Audio synchronization problems.
- Unexpected blank frames.
- Repeated scenes.
- Missing narration.
- Rendering failures.

Do not report successful video generation unless the output has been verified to the extent practical.

# 7. EDITING AND CREATIVE CONTROL

Design the product so that it can evolve from a simple automated generator into an advanced creative studio.

The intended direction includes:

- Script editing.
- Scene replacement and reordering.
- Image and video selection.
- Voice and narration editing.
- Subtitle editing.
- Text positioning.
- Brand customization.
- Scene timing.
- Background music controls.
- Transition controls.
- Preview functionality.
- Project saving and reopening.
- Regeneration of selected sections.
- Exporting approved results.

Do not build a full professional video editor prematurely.

Prioritize the editing capabilities that are most valuable for the product's core workflow.

Preserve user changes whenever content is regenerated. Never silently overwrite approved edits.

# 8. AI PROVIDER INDEPENDENCE

Avoid unnecessary dependence on a single AI provider.

Where appropriate, define clear interfaces for:

- Website understanding.
- Text generation.
- Script generation.
- Image generation.
- Video generation.
- Speech generation.
- Music generation.
- Content moderation.
- Creative quality assessment.

Provider-specific implementations should remain separate from the core business logic.

The system should support replacing or adding providers without requiring a complete rewrite.

Do not integrate a provider merely because it is popular.

Evaluate each provider according to relevant factors, including:

- Output quality.
- Language support.
- Reliability.
- Cost.
- Latency.
- Licensing.
- Privacy.
- API availability.
- Usage limits.
- Commercial suitability.

Verify current provider capabilities, pricing, and licensing before making important implementation decisions.

Do not assume that a service is free, available, or commercially usable without checking its current terms.

# 9. COST, PERFORMANCE, AND RELIABILITY

The system should balance quality, speed, and operating cost.

The project starts with zero budget (`docs/DECISIONS.md`, DEC-016). Use only free and open-source technologies and free service tiers until that decision is revised.

Within that constraint, do not sacrifice security or honesty. If a free tool cannot reach acceptable quality, say so clearly and record it, rather than hiding the limitation or adding a paid service without approval.

Design for:

- Asynchronous processing of long-running jobs.
- Clear job status and progress reporting.
- Retry mechanisms for recoverable failures.
- Timeouts and resource limits.
- Prevention of unnecessary duplicate work.
- Caching where appropriate.
- Efficient media storage.
- Controlled concurrent processing.
- Transparent usage and cost estimates.
- Appropriate logging and monitoring.

The system should communicate when a task is taking longer than expected or has failed.

Do not simulate progress or display success messages that are not supported by actual processing results.

# 10. SECURITY AND PRIVACY

Security must be considered from the beginning.

Website analysis processes untrusted external input and must not create a path for unauthorized access to internal systems.

Implement appropriate protections, including:

- URL validation.
- SSRF protection.
- Blocking loopback, private, link-local, and cloud metadata destinations.
- Safe DNS resolution and redirect validation.
- Protection against redirects to prohibited addresses.
- Request timeouts and response-size limits.
- Safe browser automation isolation.
- Restricted file access.
- Secure handling of uploaded media.
- Authentication and authorization where required.
- Protection of API keys and environment variables.
- CSRF protection and secure session handling.
- File-type and upload-size validation.
- Appropriate access controls for generated media.
- Safe logging that avoids exposing secrets.

Do not execute arbitrary website scripts on the host system.

Do not disable security protections merely to make a demonstration work.

Respect access restrictions, copyright, licensing, website terms, and applicable law.

Never commit API keys, passwords, tokens, or other secrets to Git.

# 11. RECOMMENDED INITIAL TECHNOLOGY DIRECTION

The initial development direction is:

- Backend: Python and Django.
- Frontend: HTML, CSS, and vanilla JavaScript.
- Initial database: SQLite for local development.
- Potential production database: PostgreSQL.
- Browser inspection: Playwright where appropriate.
- HTML extraction: Beautiful Soup where useful.
- Video processing: FFmpeg where appropriate.
- Version control: Git and GitHub.
- Configuration: Environment variables and an example environment file.

This is the starting direction, not an instruction to use every technology for every task.

Before introducing a new framework, library, database, or external service, explain why it is needed and whether an existing component can solve the problem.

Keep the implementation modular and understandable.

Do not migrate to a more complicated stack without a clear benefit.

# 12. PROJECT DEVELOPMENT WORKFLOW

Work incrementally.

Before changing code:

1. Inspect the existing repository.
2. Read the project documentation.
3. Understand the current architecture.
4. Identify the relevant files and dependencies.
5. Check the current project status.
6. Determine what the requested task is supposed to achieve.
7. Identify potential risks and dependencies.
8. Create a small, concrete implementation plan.

Then implement the smallest complete solution that advances the project correctly.

After implementation:

1. Review the changed code.
2. Run relevant automated tests.
3. Perform appropriate manual verification.
4. Check for regressions.
5. Inspect the final Git diff.
6. Update documentation when necessary.
7. Record any remaining limitations.
8. Explain exactly what changed and how to verify it.

Do not claim that tests passed if they were not executed.

Do not claim that a feature is complete when only its interface or placeholder has been implemented.

# 13. REPOSITORY AND DOCUMENTATION CONSISTENCY

The repository is the primary source of truth for project-specific decisions and implementation status.

Use the following files where they exist:

- `AGENTS.md` — Instructions for AI coding agents.
- `README.md` — Setup, installation, and usage instructions.
- `PROJECT_MASTER.md` — Overall product vision and master specification.
- `docs/PROJECT_REQUIREMENTS.md` — Functional and non-functional requirements.
- `docs/ARCHITECTURE.md` — Technical architecture.
- `docs/PROJECT_STATUS.md` — Implemented features and current state.
- `docs/DECISIONS.md` — Important technical and product decisions.
- `docs/TASKS.md` — Planned and outstanding work.
- `docs/TESTING.md` — Testing strategy and verification procedures.

If some files do not exist, do not pretend they do.

Create or update them when requested or when they are necessary to maintain project consistency.

When documentation conflicts with the actual code, investigate the discrepancy and report it.

Do not silently treat outdated documentation as accurate.

# 14. RULES FOR ALL AI CODING ASSISTANTS

Every AI working on this project must follow these rules:

1. Read the available project instructions before beginning significant work.
2. Inspect the actual repository instead of assuming previous conversations describe its current state.
3. Respect established product decisions.
4. Preserve existing functionality unless a change is required and approved.
5. Avoid unnecessary rewrites and unrelated changes.
6. Do not replace working implementations with mock data or placeholders.
7. Do not add dependencies without a clear reason.
8. Do not hardcode credentials, private URLs, or environment-specific secrets.
9. Do not silently change the project's architecture.
10. Do not invent files, functions, test results, or deployment status.
11. Do not remove user changes or run destructive commands without authorization.
12. Do not hide limitations or unresolved errors.
13. Explain important assumptions.
14. Ask questions when an unresolved decision could materially affect the architecture or product direction.
15. If a reasonable, reversible implementation decision can be made safely, proceed and document the decision.
16. Keep the code maintainable, readable, secure, and testable.
17. Make changes consistent with the long-term product vision.
18. Prefer complete, working increments over large amounts of unfinished code.
19. Update project status after completing substantial work.
20. Always leave the project in a state that the next developer or AI can understand.

# 15. GIT AND CHANGE MANAGEMENT

Use Git to preserve development history and support collaboration between different AI assistants.

Before making significant changes, inspect:

- Current branch.
- Working-tree status.
- Recent commits.
- Relevant source files.
- Existing uncommitted user changes.

Never overwrite unrelated user work.

Do not run destructive Git commands without explicit approval.

Keep commits focused and descriptive.

Do not commit generated secrets, private data, temporary files, or unnecessary large media assets.

When practical, make each task small enough to review, test, and revert independently.

# 16. TESTING AND QUALITY BENCHMARKS

Build a repeatable testing process instead of judging the product using only one successful example.

Test across representative websites with different:

- Industries.
- Frameworks.
- Layouts.
- Languages.
- Content structures.
- Image formats.
- JavaScript requirements.
- Navigation patterns.
- Availability conditions.

Measure website-analysis success, factual accuracy, creative quality, rendering reliability, processing time, operating cost, editing flexibility, and user satisfaction.

Maintain regression tests for previously working functionality.

Use realistic test cases and clearly document known limitations.

Do not claim universal website compatibility until broad testing provides sufficient evidence.

The long-term goal is to maximize practical compatibility, reliability, and quality across diverse websites.

# 17. USER EXPERIENCE AND ACCESSIBILITY

Design a consistent, modern, professional interface.

The product should be easy to understand without requiring users to know AI terminology or video-production techniques.

Provide:

- Clear navigation.
- Helpful defaults.
- Useful validation messages.
- Visible job status.
- Understandable error messages.
- Responsive layouts.
- Accessible controls.
- Readable typography.
- Keyboard-friendly interactions.
- Appropriate loading and empty states.
- Clear preview and export workflows.

Avoid misleading progress indicators and unnecessary visual complexity.

Do not sacrifice usability for decorative animations.

# 18. PRODUCT DIFFERENTIATION

The product should aim to differentiate itself through the combined strength of:

- Broad website compatibility.
- Deep business understanding.
- Adaptive creative strategies.
- High-quality video production.
- Flexible editing.
- Multiple output formats.
- Multilingual support.
- Provider independence.
- Transparent costs.
- Reliable processing.
- Strong user experience.
- Continuous, evidence-based improvement.

Do not assume that adding more features automatically makes the product better.

Prioritize features that meaningfully improve output quality, usability, reliability, or business value.

When evaluating a proposed feature, consider:

- The user problem it solves.
- Its implementation cost.
- Its operating cost.
- Its effect on reliability.
- Its effect on the user experience.
- Whether it creates a meaningful competitive advantage.

# 19. TASK HANDOFF FORMAT

After completing a substantial task, provide a concise handoff containing:

**Task:** What was requested.

**Repository Findings:** Relevant existing implementation and constraints.

**Changes Made:** Files changed and functionality implemented.

**Verification:** Tests and checks actually performed, including their results.

**Outstanding Issues:** Known limitations, errors, and unfinished work.

**Documentation Updated:** Relevant documentation changes.

**Next Recommended Task:** The next logical step, based on the actual project state.

Include exact file paths and commands where useful.

Do not repeat the entire project specification in every handoff.

# 20. INITIALIZATION INSTRUCTIONS FOR A NEW AI SESSION

When starting a new session:

1. Read `AGENTS.md`, if present.
2. Read `PROJECT_MASTER.md`, if present.
3. Read `README.md`.
4. Read relevant requirements and architecture documents.
5. Read `docs/PROJECT_STATUS.md`, if present.
6. Inspect the repository and Git status.
7. Identify the current development phase.
8. Confirm which features are actually implemented.
9. Identify the next approved task.
10. Continue from the verified project state.

If the repository has not been created yet, help establish the project foundation before implementing advanced functionality.

Do not assume that code, files, credentials, integrations, or infrastructure exist merely because they were discussed in a previous conversation.

# 21. THE MOST IMPORTANT RULE

Always optimize for the long-term success of JamiiTek AI Marketing Studio.

The objective is not simply to generate code quickly or create a visually impressive demonstration.

The objective is to build a reliable, secure, flexible, maintainable, and commercially valuable product that can compete internationally.

Think beyond the immediate task, but implement in disciplined, testable increments.

Protect the project's consistency, preserve working functionality, question weak assumptions, measure quality, and continuously improve the product based on evidence.

**Build toward a world-class product. Never confuse ambition with completed implementation, and never confuse a successful demonstration with a production-ready system.**