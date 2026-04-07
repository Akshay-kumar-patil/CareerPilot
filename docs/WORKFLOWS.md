# Product Workflows

This document explains the main user journeys supported by the platform so a new contributor can understand how the pieces fit together beyond the route list.

## 1. User onboarding and authentication

The journey starts in the Streamlit authentication view.

- A user registers or logs in through the frontend
- the frontend calls `/api/auth/register` or `/api/auth/login`
- JWT-backed auth state is stored in the session
- the authenticated user is then taken into the main workspace

This matters because nearly every downstream feature depends on the current user profile and token-authenticated API requests.

## 2. Resume generation flow

- The user fills in profile, skills, experience, and target-role information in the Resume Builder
- the frontend sends generation input to `/api/resume/generate`
- the resume service calls the AI layer to create structured resume content
- keyword matching is calculated against the target job description
- the generated resume is stored in SQLite
- a version record is created for comparison/history
- an embedding is written to ChromaDB for semantic retrieval support

This is one of the core flows because many later features reuse or reference the generated resume content.

## 3. Resume analysis flow

- The user uploads or selects resume content
- analysis routes score the resume, inspect sections, and identify keyword gaps
- the results are shown back in the frontend as ATS-style guidance

The analyzer is meant to turn resume generation into an iterative loop rather than a one-time action.

## 4. Cover letter and email generation flow

- The user provides job and company context
- the frontend sends requests to `/api/cover-letter/generate` or `/api/email/generate`
- the relevant service calls the AI layer with structured prompt input
- the user receives editable output that can later be downloaded or reused

These flows extend the platform from resume tooling into broader application communication support.

## 5. Job tracking and referral management

- Users create and update application records through `/api/applications`
- users manage networking and referral entries through `/api/referrals`
- analytics summarize the resulting pipeline status across saved, applied, interview, and offer-style stages

This turns the app into an operating system for job search activity rather than just a document generator.

## 6. Skill-gap analysis

- A job description is submitted to the extraction or skills flow
- required and preferred skills are identified
- the user’s current profile or resume skills are compared to the job needs
- the UI highlights matches, misses, and likely improvement areas

This workflow is especially helpful before tailoring a resume or preparing interview answers.

## 7. GitHub analysis

- The user provides repository information
- the backend analyzes project details and converts them into career-relevant summaries
- the frontend presents content that can be reused in resumes or applications

This helps bridge the gap between technical work and professional storytelling.

## 8. Mock interview workflow

- The user provides role or topic context
- `/api/interview/generate` creates question sets
- the user responds to questions
- `/api/interview/evaluate` returns feedback on the answer quality

This makes the project useful after the application stage, not just before it.

## 9. Auto-apply workflow

This is one of the more advanced flows in the repository.

- The user pastes a job description or job URL
- `/api/auto-apply/parse-jd` extracts structured details and computes skill match
- `/api/auto-apply/generate-answers` prepares tailored application answers using the user profile and resume content
- the user reviews and edits the generated responses in the frontend
- `/api/auto-apply/submit` either:
  - returns an AI-prepared package for manual use
  - or uses Playwright-based browser automation when the environment supports it
- the workflow also creates a job tracker entry for continuity

This is where the project feels most like a career copilot rather than a set of disconnected tools.

## 10. Analytics workflow

- Dashboard metrics are loaded from `/api/analytics/summary`
- response, interview, and offer trends are displayed in the frontend
- resume comparisons and application outcomes support iterative improvement

The analytics layer closes the loop by helping users learn from the results of earlier actions.
