# JamiiTek AI Marketing Studio
## PROJECT MASTER SPECIFICATION

**Document:** `PROJECT_MASTER.md`  
**Product:** JamiiTek AI Marketing Studio  
**Owner/Brand:** JamiiTek  
**Status:** Product Vision and Planning  
**Budget constraint:** Zero budget (see `docs/DECISIONS.md`, DEC-016)  
**Primary Objective:** Build a flexible, intelligent, reliable, and globally competitive AI-powered marketing creation platform.

---

# 1. Executive Summary

JamiiTek AI Marketing Studio is an ambitious AI-powered platform designed to help businesses transform their websites and business information into professional marketing content.

The long-term objective is to build a product capable of understanding diverse websites, identifying relevant business information, developing appropriate marketing concepts, generating creative assets, producing promotional videos, and allowing users to customize the final results.

The platform must not be limited to one website platform, business category, AI provider, video template, language, or advertising channel.

It should be designed for global use, with an architecture that supports continuous improvement, new AI technologies, additional content formats, and evolving marketing needs.

The product must be developed incrementally, tested against real requirements, and improved using measurable evidence.

**Important:** This document describes the intended product and its direction. A feature must not be considered implemented until it exists in the codebase and has been appropriately verified.

# 2. Product Vision

Build an AI marketing studio that makes high-quality marketing creation accessible to businesses of different sizes, industries, and technical skill levels.

A user should eventually be able to provide a website URL, review the information the system discovers, choose a marketing objective, and receive customized marketing content with minimal manual effort.

Experienced users should also be able to exercise detailed creative control.

The platform should aim to compete internationally through a combination of:

- Broad website compatibility.
- Intelligent business and brand understanding.
- Adaptive creative generation.
- High-quality video and marketing asset production.
- Flexible editing and customization.
- Multilingual capabilities.
- Reliable processing.
- Transparent costs.
- A simple user experience.
- Continuous, evidence-based improvement.

The goal is not merely to generate content. The goal is to help users produce useful, accurate, appealing, and commercially relevant marketing materials.

# 3. Target Users

The platform should be designed to support:

- Small and medium-sized businesses.
- E-commerce sellers.
- Hotels and tourism operators.
- Travel agencies.
- Real estate businesses.
- Restaurants.
- Educational institutions.
- Professional service providers.
- Software and technology companies.
- Marketing agencies.
- Freelancers and content creators.
- Nonprofit organizations.
- Larger businesses and enterprises.

These are target groups, not a fixed list of supported industries.

The architecture must allow the platform to support additional business categories without requiring major structural changes.

# 4. Core Product Workflow

The intended end-to-end workflow is:

1. The user submits a website URL or provides business information manually.
2. The system safely inspects the accessible website.
3. The system identifies relevant pages, products, services, images, branding, and business information.
4. The system builds a structured business profile.
5. The user reviews the findings and corrects missing or inaccurate information.
6. The user selects a marketing objective, audience, language, format, duration, and creative preferences.
7. The AI generates one or more marketing concepts.
8. The user reviews and edits the script or concept.
9. The system generates or assembles suitable visual assets, narration, subtitles, music, and graphics.
10. The video production engine renders the selected composition.
11. The system validates the output and reports any detected issues.
12. The user previews, edits, approves, saves, and exports the final content.

The workflow should support partial recovery when a step fails.

Where practical, users should not have to restart the entire process because one image, voice-over, or scene failed to generate.

# 5. Universal Website Understanding

Website compatibility is one of the product's most important goals.

The system must not assume that every website uses the same HTML structure, JavaScript framework, content management system, navigation pattern, or page layout.

The intended analysis capabilities include:

- URL validation and safe access checks.
- Page discovery and navigation analysis.
- HTML and metadata extraction.
- JavaScript-rendered page inspection where appropriate.
- Structured-data extraction.
- Image and brand-asset discovery.
- Product and service identification.
- Business classification.
- Relevant-page selection.
- Language detection.
- Information confidence assessment.
- Source tracking for factual claims.
- Identification of missing or conflicting information.

Potential website types include e-commerce stores, corporate sites, blogs, news portals, tourism sites, portfolios, institutional sites, and other legitimate website categories.

The system should use multiple analysis strategies rather than relying on a single extraction method.

It must respect access restrictions, website terms, privacy, copyright, and applicable law.

If access is blocked or information cannot be retrieved, the system must explain the limitation and offer reasonable alternatives.

The product must not claim compatibility with every website until extensive testing supports that claim.

# 6. Business Intelligence and Brand Understanding

The platform should create a structured representation of the business being promoted.

Where information is available, the business profile may include:

- Business name.
- Business category.
- Main products and services.
- Product attributes.
- Supported customer benefits.
- Brand colors and visual identity.
- Logo and approved media assets.
- Publicly listed contact information.
- Relevant website pages.
- Target audience suggestions.
- Advertising opportunities.
- Missing or uncertain information.

Each factual claim used in a generated advertisement should be traceable to an available source or explicitly provided by the user.

The system must not invent business information, testimonials, prices, reviews, certifications, guarantees, statistics, or product capabilities.

AI-generated supplementary scenes must not be misrepresented as authentic business locations, products, facilities, or customer experiences.

# 7. Adaptive Creative Intelligence

The system should adapt its creative decisions to the specific business and advertising objective.

Creative decisions may consider:

- Business type.
- Product or service.
- Target audience.
- Advertising objective.
- Marketing platform.
- Available assets.
- Brand identity.
- Language and regional context.
- Desired duration.
- User preferences.
- Production budget.

The system should eventually generate alternative concepts and explain how they differ.

For example, an advertisement may focus on a customer problem, a product demonstration, a key benefit, a brand story, or a visual experience.

These are possible creative strategies rather than mandatory templates.

The platform should avoid producing nearly identical advertisements for unrelated businesses.

# 8. Marketing Content Capabilities

The long-term product may support multiple types of marketing content.

## 8.1 Video Content

- Promotional videos.
- Product advertisements.
- Service advertisements.
- Brand introduction videos.
- Explainer videos.
- Social media advertisements.
- Short-form promotional content.
- Campaign variations.
- Website promotional videos.

## 8.2 Visual Assets

- Promotional images.
- Posters.
- Product graphics.
- Social media creatives.
- Campaign visuals.
- Brand-aligned layouts.

## 8.3 Written Content

- Advertising scripts.
- Headlines.
- Captions.
- Calls to action.
- Product descriptions.
- Promotional copy.
- Campaign messaging.

## 8.4 Audio and Localization

- Voice-over narration.
- Subtitles.
- Background music.
- Multiple supported languages.
- Localized advertising messages.

These capabilities should be introduced in a planned order. The initial implementation scope must be confirmed before substantial development begins.

# 9. Video Production and Rendering

The video engine should be designed to combine appropriate resources such as:

- Authentic website imagery.
- User-approved media.
- AI-generated supplementary visuals.
- Video clips.
- Motion graphics.
- Animated text.
- Brand logos.
- Voice-over narration.
- Subtitles.
- Music and sound effects.
- Calls to action.

The system should support suitable portrait, square, and landscape output formats.

Rendering must account for:

- Aspect ratios.
- Resolution.
- Scene timing.
- Audio synchronization.
- Subtitle timing.
- Text readability.
- Media availability.
- Brand consistency.
- Output validation.

Use FFmpeg or another appropriate rendering technology where justified.

Generated output should be validated for common technical failures before being presented as complete.

# 10. Editing and Customization

The platform should offer a simple automated workflow and an advanced editing workflow.

The intended editing capabilities include:

- Script modification.
- Scene replacement.
- Scene reordering.
- Image and video selection.
- Voice selection.
- Narration adjustment.
- Subtitle editing.
- Text and logo placement.
- Color and font customization.
- Scene timing.
- Music controls.
- Transition settings.
- Project saving.
- Previewing.
- Selective regeneration.
- Exporting.

The system should preserve approved user edits when content is regenerated.

A full professional timeline editor is a possible future direction, not a requirement to implement immediately.

# 11. AI Provider Strategy

The system should not be unnecessarily coupled to one AI provider.

Where appropriate, use modular interfaces for:

- Website analysis.
- Business classification.
- Text and script generation.
- Image generation.
- Video generation.
- Speech generation.
- Music generation.
- Content evaluation.

Providers should be selected according to quality, reliability, language support, pricing, latency, privacy, licensing, and commercial availability.

The project starts with zero budget (DEC-016). Use only free and open-source tools and free service tiers until that decision is revised. Paid providers may be added later through a recorded decision, when they deliver sufficient value and funding exists.

Do not assume that a provider is free, commercially usable, or available without verifying its current terms and capabilities. Free tiers can change or close at any time, and some free models and voices are licensed for non-commercial use only.

Provider replacement should not require rewriting the entire application.

# 12. Technical Direction

The initial technology direction is:

- **Backend:** Python and Django.
- **Frontend:** HTML, CSS, and vanilla JavaScript.
- **Initial database:** SQLite for local development.
- **Potential production database:** PostgreSQL.
- **Browser inspection:** Playwright where appropriate.
- **HTML parsing:** Beautiful Soup where useful.
- **Video rendering:** FFmpeg where appropriate.
- **Version control:** Git and GitHub.
- **Configuration:** Environment variables and a safe example configuration file.

This is the initial direction, not a requirement to use every technology in every component.

The implementation should remain modular, testable, maintainable, and suitable for gradual expansion.

# 13. Processing Architecture

Website analysis and video generation may require substantial processing time.

The system should eventually support:

- Background jobs.
- Job status tracking.
- Progress reporting based on actual processing.
- Retry mechanisms.
- Timeouts.
- Cancellation where appropriate.
- Duplicate-work prevention.
- Resource limits.
- Failure recovery.
- Media storage management.
- Cost tracking.

Do not block ordinary web requests while long-running video generation is taking place.

Do not show simulated progress or claim completion without evidence.

# 14. Security and Privacy

Security must be considered from the beginning.

Website inspection must include protection against server-side request forgery and unsafe destinations.

Appropriate safeguards should include:

- URL validation.
- Private and internal IP address blocking.
- Cloud metadata endpoint protection.
- DNS and redirect validation.
- Request timeouts and response limits.
- Browser isolation.
- Safe file handling.
- Authentication and authorization where required.
- Secure media access.
- Upload validation.
- CSRF protection.
- Secret management.
- Appropriate logging.
- Privacy-aware data retention.

Do not execute untrusted website code on the host system.

Never commit API keys, passwords, access tokens, or other secrets to the repository.

# 15. Quality and Testing

Quality must be measured rather than assumed.

The project should maintain a representative benchmark of websites and marketing-generation tasks.

Evaluate:

- Website analysis success.
- Factual accuracy.
- Business classification quality.
- Brand consistency.
- Script quality.
- Visual quality.
- Audio quality.
- Rendering reliability.
- Editing flexibility.
- Processing time.
- Operating cost.
- User satisfaction.

Test across different industries, languages, website structures, and technical implementations.

Maintain regression tests so new changes do not silently break existing functionality.

Do not claim that the product is superior to every competitor without credible comparative evidence.

# 16. User Experience

The interface should be modern, professional, responsive, accessible, and easy to learn.

Users should understand:

- What the system has discovered.
- Which information will be used.
- Which decisions AI has made.
- What needs user approval.
- How long a task may take.
- Whether a task has failed.
- What the next action should be.
- What the generated content will cost, when costs can be estimated.

Provide helpful defaults for beginners and meaningful controls for advanced users.

Prioritize usability and actual task completion over decorative complexity.

# 17. Commercial Readiness and Scalability

The architecture should allow the product to evolve toward commercial use.

Future capabilities may include:

- User accounts.
- Project history.
- Usage quotas.
- Subscription plans.
- Payment integrations.
- Team collaboration.
- Brand profiles.
- Asset libraries.
- Organization accounts.
- Usage analytics.
- Provider cost tracking.
- Administrative controls.

Do not implement these features prematurely unless they are part of an approved development phase.

Commercial features must be designed with authentication, authorization, privacy, billing correctness, and operational reliability in mind.

# 18. Development Roadmap

The following is a proposed roadmap. The exact order and scope should be confirmed before implementation.

**Phase 1 — Foundation**

- Inspect and prepare the development environment.
- Create the Django project.
- Establish repository structure.
- Configure settings and environment variables.
- Add basic tests.
- Document setup instructions.

**Phase 2 — Website Analysis**

- Implement safe URL validation.
- Inspect accessible website content.
- Extract useful pages and assets.
- Build the initial structured business profile.
- Add tests using representative websites.

**Phase 3 — Business Intelligence and Script Generation**

- Integrate an appropriate AI provider.
- Generate structured marketing concepts.
- Produce scripts grounded in discovered information.
- Add user review and editing.

**Phase 4 — Creative Configuration**

- Add output formats and duration controls.
- Add language, style, and narration settings.
- Introduce brand customization.

**Phase 5 — Audio and Media**

- Integrate selected voice and media providers.
- Manage assets and generated files.
- Add provider-independent interfaces where justified.

**Phase 6 — Video Rendering**

- Create a rendering pipeline.
- Compose scenes, narration, music, and subtitles.
- Validate generated videos.

**Phase 7 — Preview, Editing, and Export**

- Add preview and editing workflows.
- Support saving and reopening projects.
- Implement export and failure recovery.

**Phase 8 — Reliability and Commercial Features**

- Improve performance and observability.
- Add approved account, quota, billing, and collaboration features.
- Conduct broader quality testing.

**Phase 9 — Deployment and Continuous Improvement**

- Prepare secure deployment.
- Configure production storage and database.
- Establish monitoring and backups.
- Maintain a repeatable evaluation and release process.

Do not treat this roadmap as evidence that any phase has already been implemented.

# 19. Development Rules

Every developer and AI assistant working on the project must:

1. Read the available project instructions.
2. Inspect the repository before making significant changes.
3. Confirm the actual state of the implementation.
4. Preserve existing working functionality.
5. Avoid unnecessary rewrites.
6. Avoid unrelated modifications.
7. Implement features in testable increments.
8. Run relevant tests and report their actual results.
9. Document important decisions.
10. Protect user changes and credentials.
11. Identify assumptions and unresolved risks.
12. Update project status after substantial work.
13. Avoid fake functionality and misleading completion claims.
14. Prefer reliable, maintainable solutions over unnecessary complexity.

The repository and its current documentation are the primary sources of truth for implementation status.

# 20. Definition of Success

The long-term success of JamiiTek AI Marketing Studio should be evaluated through evidence of:

- Broad and continually improving website compatibility.
- Accurate representation of business information.
- High-quality, relevant marketing outputs.
- Meaningful creative flexibility.
- Reliable processing and rendering.
- Good user experience.
- Strong language support.
- Sustainable operating costs.
- Secure handling of websites and user assets.
- Positive user feedback and retention.
- Demonstrated competitive strengths.

The objective is to build a product with a credible opportunity to compete globally.

Ambition must be supported by engineering discipline, real-world testing, user feedback, and continuous improvement.

# 21. Current Project Status

As of 2026-10-27, the planning documentation is complete and no implementation exists.

Do not assume that:

- The Django project already exists.
- Dependencies have been installed.
- Website analysis has been implemented.
- AI providers have been connected.
- Video generation works.
- Deployment infrastructure exists.
- Automated tests have passed.

Verify the repository and development environment before making implementation claims.

The detailed implementation status should be maintained in `docs/PROJECT_STATUS.md`.

# 22. Final Principle

Build JamiiTek AI Marketing Studio as a long-term product, not a temporary demonstration.

Make the architecture flexible enough to evolve, the workflow simple enough to use, the output accurate enough to trust, and the engineering disciplined enough to maintain.

Prioritize measurable quality, real functionality, security, adaptability, and user value.

**The vision is global competitiveness. The method is disciplined, incremental, evidence-based development.**
