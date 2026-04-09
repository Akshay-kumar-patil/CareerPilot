"""
Prompt templates for all AI features.
Each prompt is designed for structured JSON output where possible.
"""

RESUME_GENERATION_PROMPT = """You are an expert resume writer specializing in ATS-optimized developer resumes.

Given the following job description and user information, generate a professional, ATS-optimized resume. 
Your goal is to create a resume that looks like a top-tier developer resume with strong formatting.

**Job Description:**
{job_description}

**User's Existing Resume / Information:**
{existing_resume}

**Additional Context:**
{additional_context}

Generate a complete resume in the following JSON format.
STRICT RULES — failure to follow will break the parser:
- Return ONLY valid JSON. No text before or after.
- Every bullet point: MAX 20 words.
- Every array (experience, projects, etc.): MAX 3 items.
- Summary: MAX 50 words.
- Do NOT truncate — if you are running out of space, shorten values further.
- Close ALL brackets and quotes.
- Preserve the user's ACTUAL NAME and contact details from the input.

{{
    "full_name": "First Last",
    "contact": {{
        "email": "email@example.com",
        "phone": "+91-XXXXXXXXXX",
        "linkedin": "linkedin.com/in/username",
        "github": "github.com/username",
        "portfolio": "portfolio-url.com",
        "location": "City, State",
        "leetcode": "leetcode.com/username"
    }},
    "summary": "A 2-3 sentence professional summary focused on key strengths.",
    "education": [
        {{
            "degree": "Degree Name",
            "school": "University Name",
            "location": "City, State",
            "dates": "Year-Year",
            "grade": "CGPA/Percentage",
            "highlights": []
        }}
    ],
    "skills": {{
        "Programming & Databases": "Python, JavaScript, SQL",
        "Frameworks & Libraries": "React.js, Node.js, FastAPI",
        "Cloud & Tools": "AWS, Docker, Git"
    }},
    "experience": [
        {{
            "title": "Role Name",
            "company": "Company Name",
            "location": "City",
            "dates": "Month Year — Present",
            "bullets": [
                "Developed X feature using Y technology, improving Z by N%",
                "Built scalable APIs serving thousands of users daily"
            ]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "tech_stack": "Tech A, Tech B",
            "live_url": "url.com",
            "repo_url": "github.com/user/repo",
            "bullets": [
                "Built full-stack application with real-time features",
                "Optimized performance reducing latency by 40%"
            ]
        }}
    ],
    "certifications": [
        {{
            "name": "Cert Name",
            "issuer": "Issuer",
            "date": "Year"
        }}
    ],
    "achievements": [
        "Concise achievement point",
        "Another key achievement"
    ]
}}

CRITICAL RULES:
1. Use strong action verbs (Led, Developed, Implemented, Optimized, Engineered, Built).
2. Include quantifiable metrics wherever possible (%, numbers, scale).
3. Match keywords from the job description naturally into experience and skills.
4. Return ONLY valid JSON — no markdown fences, no explanation text.
5. Preserve the user's actual data (name, contact, education, etc.) — do NOT invent personal details.
"""


# ROOT FIX: Prompt rewritten to produce SHORT, bounded output.
# The previous prompt had no length constraints, so Gemini would write
# paragraph-length feedback strings that pushed the response over the
# max_output_tokens limit and truncated mid-JSON.
# Solution: strict per-field word/item limits so total output stays well
# under 4096 tokens even for a detailed resume.
RESUME_ANALYSIS_PROMPT = """You are an expert ATS analyzer and career coach.

Analyze the resume below and return ONLY a valid JSON object — no markdown, no explanation.

**Resume:**
{resume_text}

**Target Job Description:**
{job_description}

STRICT RULES — failure to follow will break the parser:
- Return ONLY valid JSON. No text before or after.
- Every string value: MAX 20 words.
- Every array: MAX 3 items.
- Do NOT truncate — if you are running out of space, shorten values further.
- Close ALL brackets and quotes.

Required JSON structure (fill every field, use empty array [] if nothing to add):
{{
    "ats_score": <integer 0-100>,
    "overall_feedback": "<max 20 words>",
    "strengths": ["<max 10 words>", "<max 10 words>", "<max 10 words>"],
    "formatting_issues": ["<max 10 words>"],
    "section_feedback": [
        {{
            "section": "<name>",
            "score": <integer 0-100>,
            "feedback": "<max 15 words>",
            "suggestions": ["<max 10 words>"]
        }}
    ],
    "keyword_analysis": {{
        "present_keywords": ["keyword1", "keyword2", "keyword3"],
        "missing_keywords": ["keyword1", "keyword2", "keyword3"],
        "keyword_density_score": <integer 0-100>
    }},
    "improvement_suggestions": ["<max 15 words>", "<max 15 words>", "<max 15 words>"]
}}
"""

COVER_LETTER_PROMPT = """You are an expert cover letter writer.

Write a personalized cover letter for the following position.

**Company:** {company_name}
**Role:** {role}
**Job Description:** {job_description}
**Key Skills to Highlight:** {key_skills}
**Tone:** {tone}
**Additional Context:** {additional_context}

**User Profile:**
{user_profile}

Write a compelling cover letter that returns the following JSON structure:

{{
    "recipient_name": "<Hiring Manager Name if known, or blank>",
    "recipient_title": "<Hiring Manager Title if known, or Human Resources>",
    "company_name": "<Company Name from the prompt>",
    "company_address": "<Company Address if known, or City/State if known, or blank>",
    "company_phone": "<Company Phone if known, or blank>",
    "company_email": "<Company Email if known, or blank>",
    "salutation": "<Opening salutation e.g. Dear Hiring Manager,>",
    "body_paragraphs": [
        "<Paragraph 1: Hook showing genuine interest>",
        "<Paragraph 2: Highlight 2-3 most relevant experiences/skills>",
        "<Paragraph 3: Connects past achievements to the role's requirements>",
        "<Paragraph 4: Closes with a confident call to action>"
    ],
    "sign_off": "<Sign-off e.g. Best regards,>"
}}

Rules:
- Tone guide:
  * formal: Professional, traditional structure
  * concise: Short, direct, impact-focused (under 250 words total)
  * creative: Shows personality while remaining professional
- Return ONLY valid JSON, completely filled in. Do not use markdown wrappers unless it is ```json...``` around the whole thing.
"""

RECRUITER_SIM_PROMPT = """You are a senior technical recruiter reviewing an application.

**Resume:**
{resume_text}

**Job Description:**
{job_description}

Return ONLY valid JSON, no other text:
{{
    "decision": "shortlisted" or "rejected",
    "confidence": <float 0.0-1.0>,
    "reasoning": ["<reason 1>", "<reason 2>"],
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"],
    "suggestions": ["<suggestion 1>", "<suggestion 2>"],
    "comparison_notes": "<max 20 words>"
}}
"""

INTERVIEW_QUESTION_PROMPT = """You are an expert interviewer for the role of {role} at {company}.

Generate {num_questions} interview questions for a {difficulty} difficulty {interview_type} interview.

Return ONLY valid JSON:
{{
    "questions": [
        {{
            "id": 1,
            "question": "The interview question",
            "type": "hr or technical",
            "difficulty": "easy/medium/hard",
            "category": "behavioral/technical/situational/system_design",
            "tips": "Brief tip under 10 words",
            "expected_duration_minutes": 5
        }}
    ]
}}
"""

INTERVIEW_EVAL_PROMPT = """You are an expert interviewer evaluating a candidate's answer.

**Question:** {question}
**Answer:** {answer}
**Role:** {role}

Return ONLY valid JSON:
{{
    "score": <integer 0-10>,
    "feedback": "<max 30 words>",
    "strengths": ["<max 10 words>", "<max 10 words>"],
    "improvements": ["<max 10 words>", "<max 10 words>"],
    "sample_answer": "<max 50 words>"
}}
"""

SKILL_GAP_PROMPT = """You are a career development advisor.

Compare the user's skills against the job requirements.

**Job Description:**
{job_description}

**User's Current Skills:**
{user_skills}

Return ONLY valid JSON:
{{
    "missing_skills": [
        {{
            "skill": "<skill name>",
            "importance": "critical/important/nice_to_have",
            "estimated_learning_time": "<e.g. 2 weeks>",
            "resources": ["<platform/course name>"]
        }}
    ],
    "matched_skills": ["<skill>", "<skill>"],
    "skill_score": <integer 0-100>,
    "learning_roadmap": [
        {{
            "phase": 1,
            "title": "<phase title>",
            "duration": "<e.g. 2 weeks>",
            "skills": ["<skill>"],
            "resources": ["<resource>"]
        }}
    ],
    "suggested_projects": ["<project idea under 15 words>"]
}}
"""

EMAIL_GENERATION_PROMPT = """You are an expert at writing professional job search emails.

**Email Type:** {email_type}
**Recipient:** {recipient_name}
**Company:** {company}
**Role:** {role}
**Context:** {context}
**Tone:** {tone}

Return ONLY valid JSON:
{{
    "subject": "<email subject line>",
    "body": "<full email body>"
}}

Rules: concise (under 200 words for cold emails), respectful, clear ask, human tone.
"""

GITHUB_ANALYSIS_PROMPT = """You are a technical resume writer analyzing GitHub projects.

**GitHub Repositories:**
{repos_data}

Return ONLY valid JSON:
{{
    "resume_points": [
        "Built a [project type] using [technologies] that [achievement/impact]"
    ],
    "tech_stack": ["Technology 1", "Technology 2"],
    "project_highlights": [
        {{
            "repo_name": "<name>",
            "description": "<max 20 words>",
            "technologies": ["<tech>"],
            "suggested_bullet": "<resume bullet under 20 words>"
        }}
    ]
}}
"""

JD_EXTRACTION_PROMPT = """You are an expert at parsing job descriptions.

**Job Description Text:**
{jd_text}

Return ONLY valid JSON:
{{
    "company": "<company name or null>",
    "role": "<job title>",
    "skills": ["<skill>"],
    "responsibilities": ["<responsibility>"],
    "requirements": ["<requirement>"],
    "tools": ["<tool>"],
    "experience_required": "<e.g. 3-5 years or null>",
    "education_required": "<e.g. Bachelor's in CS or null>",
    "nice_to_haves": ["<nice to have>"],
    "benefits": ["<benefit>"],
    "salary_range": "<if mentioned or null>",
    "location": "<if mentioned or null>",
    "job_type": "<remote/hybrid/onsite or null>"
}}
"""

JD_FORM_PARSE_PROMPT = """You are an expert job application assistant. Parse the following job description and extract everything needed to fill a job application form.

**Job Description:**
{jd_text}

Return ONLY valid JSON (no markdown, no explanation):
{{
    "company": "<company name>",
    "role": "<exact job title>",
    "location": "<city/state/country or Remote>",
    "job_type": "<Full-time/Part-time/Contract/Internship>",
    "experience_required": "<e.g. 2-4 years>",
    "salary_range": "<e.g. 8-15 LPA or null>",
    "apply_platform": "<LinkedIn/Naukri/Indeed/Company Website/AngelList/Other>",
    "apply_url": "<direct application URL if found, else null>",
    "required_skills": ["<required skill>"],
    "preferred_skills": ["<preferred/nice-to-have skill>"],
    "responsibilities": ["<key responsibility in 10 words max>"],
    "key_highlights": ["<standout perk or highlight>"],
    "application_fields": [
        {{"field": "full_name", "label": "Full Name", "type": "text", "required": true}},
        {{"field": "email", "label": "Email Address", "type": "email", "required": true}},
        {{"field": "phone", "label": "Phone Number", "type": "text", "required": true}},
        {{"field": "linkedin", "label": "LinkedIn Profile", "type": "url", "required": false}},
        {{"field": "cover_note", "label": "Cover Note", "type": "textarea", "required": true}},
        {{"field": "experience_years", "label": "Years of Experience", "type": "number", "required": true}},
        {{"field": "expected_salary", "label": "Expected CTC (LPA)", "type": "text", "required": false}},
        {{"field": "notice_period", "label": "Notice Period", "type": "text", "required": false}},
        {{"field": "why_company", "label": "Why join us?", "type": "textarea", "required": false}},
        {{"field": "portfolio", "label": "Portfolio / GitHub", "type": "url", "required": false}},
        {{"field": "resume", "label": "Resume Upload", "type": "file", "required": true}}
    ]
}}
"""

APPLICATION_ANSWERS_PROMPT = """You are a professional job application coach. Generate personalized, ATS-optimized answers for a job application form.

**Applying to:** {company} — {role}
**Key Requirements:** {requirements}

**Candidate Resume Summary:**
{resume_summary}

**Candidate Details:**
- Name: {full_name}
- Email: {email}
- Phone: {phone}
- LinkedIn: {linkedin}
- GitHub/Portfolio: {github}
- Years of Experience: {experience_years}

Generate highly compelling, genuine answers for the application. Return ONLY valid JSON:
{{
    "full_name": "{full_name}",
    "email": "{email}",
    "phone": "{phone}",
    "linkedin": "{linkedin}",
    "portfolio": "{github}",
    "headline": "<professional headline: Role | Key Skills | Years exp>",
    "experience_years": "{experience_years}",
    "current_salary": "<reasonable estimate based on exp, say 'Prefer not to disclose' if unsure>",
    "expected_salary": "<reasonable ask, e.g. '10-12 LPA' based on role & market>",
    "notice_period": "<e.g. '30 days' or 'Immediately available'>",
    "availability": "<e.g. 'Immediately available' or '2 weeks notice period'>",
    "cover_note": "<3-4 compelling sentences tailored to {company} and {role}. Mention 1-2 specific skills matching the requirements. End with enthusiasm.>",
    "why_company": "<2-3 genuine sentences about why {company} specifically. Research-style — mention their product/mission/growth angle.>",
    "additional_info": "<Any strong differentiator: open source contributions, side projects, certifications relevant to this role>",
    "referral": ""
}}
"""

