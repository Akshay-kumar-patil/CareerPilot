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

Generate a complete resume in the following JSON format. Every field must be present.
If a field has no data, use an empty string "" or empty array [].
Do NOT omit any field. Do NOT add extra text outside the JSON.

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
    "summary": "A 2-3 sentence professional summary. Mention expertise areas, years of experience, and key strengths relevant to the target role.",
    "education": [
        {{
            "degree": "Bachelor of Technology — Computer Science",
            "school": "University Name",
            "location": "City, State",
            "dates": "2020-2024",
            "grade": "CGPA: 8.5",
            "highlights": []
        }}
    ],
    "skills": {{
        "Programming & Databases": "Python, JavaScript, Java, C/C++, SQL, MySQL, PostgreSQL, MongoDB, Firebase, Redis",
        "Frameworks & Libraries": "React.js, React Native, Node.js, Express.js, FastAPI, HTML5, CSS3, Three.js",
        "Cloud, DevOps & Tools": "AWS, Google Cloud Platform, Docker, Git, CI/CD, VS Code, Socket.io, MQTT"
    }},
    "experience": [
        {{
            "title": "Full Stack Developer",
            "company": "Company Name",
            "location": "Remote",
            "dates": "Jan 2024 — Present",
            "bullets": [
                "Developed X feature using Y technology, resulting in Z% improvement",
                "Built customer-facing APIs serving 10K+ requests/day",
                "Led team of N engineers implementing agile processes"
            ]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "tech_stack": "React, Node.js, MongoDB",
            "live_url": "project-live-url.com",
            "repo_url": "github.com/user/repo",
            "bullets": [
                "Built full-stack application with real-time features",
                "Reduced latency by 40% through optimization"
            ]
        }}
    ],
    "certifications": [
        {{
            "name": "AWS Cloud Practitioner",
            "issuer": "Amazon Web Services",
            "date": "2024"
        }}
    ],
    "achievements": [
        "Won 1st place in XYZ Hackathon 2024",
        "3-Time College Topper on Code360 Leaderboard"
    ]
}}

CRITICAL RULES:
1. Use strong action verbs (Led, Developed, Implemented, Optimized, Engineered, Built)
2. Include quantifiable metrics wherever possible (%, numbers, scale)
3. Match keywords from the job description naturally into experience and skills
4. Keep bullet points concise (1-2 lines each, under 20 words)
5. For skills, use comma-separated strings grouped by category
6. Return ONLY valid JSON — no markdown fences, no explanation text before or after
7. Preserve the user's actual data (name, contact, education, etc.) — do NOT invent personal details
8. Enhance and optimize bullet points for ATS but keep them truthful
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

Write a compelling cover letter that:
1. Opens with a hook that shows genuine interest
2. Highlights 2-3 most relevant experiences/skills
3. Connects past achievements to the role's requirements
4. Shows knowledge of the company
5. Closes with a confident call to action

Tone guide:
- formal: Professional, traditional structure
- concise: Short, direct, impact-focused (under 250 words)
- creative: Shows personality while remaining professional

Return ONLY the cover letter text, properly formatted with paragraphs.
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
