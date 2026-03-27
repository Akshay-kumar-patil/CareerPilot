"""
Career Automation & Job Intelligence Platform — Streamlit Frontend
Main application entry point with authentication and navigation.
"""
import streamlit as st
import sys, os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils.session import init_session, set_auth, clear_auth, is_authenticated
from frontend.utils import api_client as api

# Page config
st.set_page_config(
    page_title="Career AI Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for premium look
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    /* Main header gradient */
    .main-header {
        background: linear-gradient(135deg, #6C63FF 0%, #4ECDC4 50%, #45B7D1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        text-align: center;
        color: #8892B0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        border: 1px solid rgba(108, 99, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(108, 99, 255, 0.15);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #6C63FF;
    }
    .metric-label {
        color: #8892B0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Status badges */
    .status-online { color: #4ECDC4; }
    .status-offline { color: #FF6B6B; }

    /* Auth form */
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: #1A1F2E;
        border-radius: 16px;
        border: 1px solid rgba(108, 99, 255, 0.2);
    }

    /* Button overrides */
    .stButton > button {
        background: linear-gradient(135deg, #6C63FF, #5A54E0);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5A54E0, #4845C7);
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1A1F2E;
        border-radius: 8px;
        padding: 8px 16px;
    }

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: #0E1117;
    }

    /* Feature card */
    .feature-card {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(108, 99, 255, 0.15);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .feature-card:hover {
        border-color: rgba(108, 99, 255, 0.5);
    }

    .score-gauge {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
    }
    .score-good { color: #4ECDC4; }
    .score-mid { color: #FFD93D; }
    .score-low { color: #FF6B6B; }
</style>
""", unsafe_allow_html=True)

# Initialize session
init_session()


def show_auth_page():
    """Display login/register form."""
    st.markdown('<h1 class="main-header">🚀 Career AI Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Career Operating System</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted and email and password:
                    result = api.login(email, password)
                    if result:
                        set_auth(result["access_token"], result["user"])
                        st.rerun()

        with tab2:
            with st.form("register_form"):
                full_name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_pass")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted and full_name and email and password:
                    result = api.register(email, password, full_name)
                    if result:
                        set_auth(result["access_token"], result["user"])
                        st.rerun()

    # Features preview
    st.markdown("---")
    st.markdown("### ✨ Platform Features")
    cols = st.columns(4)
    features = [
        ("📄", "Resume Builder", "AI-generated, ATS-optimized resumes"),
        ("🔍", "Resume Analyzer", "ATS scoring & improvement insights"),
        ("🎯", "Job Tracker", "Track all your applications"),
        ("🎤", "Mock Interview", "AI-powered practice sessions"),
        ("📊", "Skill Gap Analysis", "Identify & bridge skill gaps"),
        ("✉️", "Cover Letters", "Personalized & tone-matched"),
        ("📧", "Email Generator", "Cold emails & follow-ups"),
        ("📈", "Analytics", "Data-driven job search insights"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="feature-card">
                <div style="font-size:2rem; margin-bottom:0.5rem">{icon}</div>
                <div style="font-weight:600; margin-bottom:0.3rem">{title}</div>
                <div style="color:#8892B0; font-size:0.85rem">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


def show_sidebar():
    """Display sidebar with user info and navigation."""
    with st.sidebar:
        user = st.session_state.get("user", {})
        st.markdown(f"""
        <div style="text-align:center; padding:1rem 0;">
            <div style="font-size:2.5rem">👤</div>
            <div style="font-weight:600; font-size:1.1rem; margin-top:0.3rem">{user.get('full_name', 'User')}</div>
            <div style="color:#8892B0; font-size:0.85rem">{user.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # AI Status indicator
        ai_status = api.get_ai_status()
        if ai_status:
            gemini = ai_status.get("gemini_configured", False)
            online = ai_status.get("internet_available", False)
            ollama = ai_status.get("ollama_available", False)
            if gemini and online:
                status_text = "🟢 Gemini Online"
            elif online:
                status_text = "🟢 Online"
            elif ollama:
                status_text = "🟡 Offline (Ollama)"
            else:
                status_text = "🔴 No AI"
            st.markdown(f"**AI Status:** {status_text}")
            if gemini:
                st.caption(f"Model: {ai_status.get('gemini_model', 'gemini-2.0-flash')}")
            if ai_status.get("estimated_cost_usd", 0) > 0:
                st.caption(f"Cost: ${ai_status['estimated_cost_usd']:.4f}")

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            clear_auth()
            st.rerun()


def main():
    """Main app routing."""
    if not is_authenticated():
        show_auth_page()
        return

    show_sidebar()

    # Page navigation using Streamlit's built-in system
    pages = {
        "🏠 Dashboard": "pages/1_🏠_Dashboard.py",
        "📄 Resume Builder": "pages/2_📄_Resume_Builder.py",
        "🔍 Resume Analyzer": "pages/3_🔍_Resume_Analyzer.py",
        "✉️ Cover Letter": "pages/4_✉️_Cover_Letter.py",
        "🎯 Job Tracker": "pages/5_🎯_Job_Tracker.py",
        "👥 Referrals": "pages/6_👥_Referrals.py",
        "🎤 Mock Interview": "pages/7_🎤_Mock_Interview.py",
        "📊 Skill Gap": "pages/8_📊_Skill_Gap.py",
        "📈 Analytics": "pages/9_📈_Analytics.py",
        "📧 Email Generator": "pages/10_📧_Email_Generator.py",
        "🐙 GitHub Analyzer": "pages/11_🐙_GitHub_Analyzer.py",
        "🤖 AI Recruiter": "pages/12_🤖_AI_Recruiter.py",
        "🧪 A/B Testing": "pages/13_🧪_AB_Testing.py",
        "⚙️ Settings": "pages/14_⚙️_Settings.py",
    }

    # Using sidebar selectbox for navigation (works with single-page approach)
    with st.sidebar:
        selected = st.selectbox("Navigate", list(pages.keys()), label_visibility="collapsed")

    # Import and run the selected page module
    page_funcs = {
        "🏠 Dashboard": show_dashboard,
        "📄 Resume Builder": show_resume_builder,
        "🔍 Resume Analyzer": show_resume_analyzer,
        "✉️ Cover Letter": show_cover_letter,
        "🎯 Job Tracker": show_job_tracker,
        "👥 Referrals": show_referrals,
        "🎤 Mock Interview": show_mock_interview,
        "📊 Skill Gap": show_skill_gap,
        "📈 Analytics": show_analytics,
        "📧 Email Generator": show_email_generator,
        "🐙 GitHub Analyzer": show_github_analyzer,
        "🤖 AI Recruiter": show_ai_recruiter,
        "🧪 A/B Testing": show_ab_testing,
        "⚙️ Settings": show_settings,
    }

    page_funcs[selected]()


# ===================== PAGE FUNCTIONS =====================

def show_dashboard():
    st.markdown('<h1 class="main-header">🏠 Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Welcome back! Here\'s your career overview.</p>', unsafe_allow_html=True)

    # Quick stats
    analytics = api.get_analytics()
    if analytics:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{analytics.get('total_applications', 0)}</div>
                <div class="metric-label">Total Applications</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{analytics.get('response_rate', 0)}%</div>
                <div class="metric-label">Response Rate</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{analytics.get('interview_rate', 0)}%</div>
                <div class="metric-label">Interview Rate</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{analytics.get('offer_rate', 0)}%</div>
                <div class="metric-label">Offer Rate</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("🎉 Welcome! Start by building your first resume or adding a job application.")

    st.markdown("---")

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    cols = st.columns(4)
    actions = [
        ("📄", "Build Resume", "Generate an ATS-optimized resume"),
        ("🔍", "Analyze Resume", "Get your ATS score"),
        ("🎯", "Track Application", "Add a new job application"),
        ("🎤", "Practice Interview", "Start a mock interview"),
    ]
    for i, (icon, title, desc) in enumerate(actions):
        with cols[i]:
            st.markdown(f"""<div class="feature-card">
                <div style="font-size:1.5rem">{icon}</div>
                <div style="font-weight:600">{title}</div>
                <div style="color:#8892B0; font-size:0.8rem">{desc}</div>
            </div>""", unsafe_allow_html=True)

    # AI Status Card
    st.markdown("---")
    st.markdown("### 🧠 AI System Status")
    ai_status = api.get_ai_status()
    if ai_status:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            online = ai_status.get("internet_available", False)
            st.markdown(f"**Internet:** {'🟢 Connected' if online else '🔴 Offline'}")
            st.markdown(f"**Provider:** {ai_status.get('default_provider', 'gemini').title()}")
        with c2:
            gemini_ok = ai_status.get("gemini_configured", False)
            st.markdown(f"**Gemini:** {'🟢 Configured' if gemini_ok else '⚪ Not set'}")
            st.markdown(f"**Model:** {ai_status.get('gemini_model', 'N/A')}")
        with c3:
            ollama = ai_status.get("ollama_available", False)
            st.markdown(f"**Ollama:** {'🟢 Running' if ollama else '⚪ Not detected'}")
            st.markdown(f"**OpenAI:** {'🟢 Configured' if ai_status.get('openai_configured') else '⚪ Not set'}")
        with c4:
            st.markdown(f"**Cost:** ${ai_status.get('estimated_cost_usd', 0):.4f}")
            st.markdown(f"**Tokens:** {ai_status.get('tokens_used', 0):,}")


def show_resume_builder():
    st.markdown('<h1 class="main-header">📄 Resume Builder</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate ATS-optimized resumes tailored to any job description</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["✨ Generate New", "📋 My Resumes"])

    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            jd = st.text_area("📋 Job Description", height=250, placeholder="Paste the job description here...")
            existing = st.text_area("📄 Existing Resume (optional)", height=150, placeholder="Paste your current resume text...")
            context = st.text_input("💡 Additional Context", placeholder="e.g., Focus on leadership, 5 years experience...")

        with col2:
            st.markdown("### Preview")
            if st.button("🚀 Generate Resume", use_container_width=True, type="primary"):
                if not jd:
                    st.warning("Please enter a job description")
                else:
                    with st.spinner("🧠 AI is crafting your resume..."):
                        result = api.generate_resume(jd, existing, additional_context=context)
                        if result:
                            st.success(f"✅ Resume generated! ATS Score: {result.get('ats_score', 'N/A')}")
                            st.session_state["last_resume"] = result

            if "last_resume" in st.session_state:
                r = st.session_state["last_resume"]
                content = r.get("content", {})

                # ATS Score
                score = r.get("ats_score", 0)
                score_class = "score-good" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
                st.markdown(f'<div class="score-gauge {score_class}">{score}%</div>', unsafe_allow_html=True)
                st.caption("ATS Keyword Match Score")

                # Keywords
                if r.get("keywords_matched"):
                    st.markdown("**✅ Matched Keywords:**")
                    st.write(", ".join(r["keywords_matched"][:15]))
                if r.get("keywords_missing"):
                    st.markdown("**❌ Missing Keywords:**")
                    st.write(", ".join(r["keywords_missing"][:10]))

                # Resume content preview
                if isinstance(content, dict):
                    st.markdown("---")
                    st.markdown(f"### {content.get('full_name', 'Your Name')}")
                    st.write(content.get("summary", ""))
                    for exp in content.get("experience", []):
                        st.markdown(f"**{exp.get('title', '')}** — {exp.get('company', '')}")
                        for bullet in exp.get("bullets", []):
                            st.markdown(f"• {bullet}")

                # Download buttons
                st.markdown("---")
                dc1, dc2, dc3 = st.columns(3)
                resume_id = r.get("id")
                if resume_id:
                    with dc1:
                        if st.button("📥 PDF"):
                            data = api.download_resume(resume_id, "pdf")
                            if data:
                                st.download_button("Download PDF", data, "resume.pdf", "application/pdf")
                    with dc2:
                        if st.button("📥 DOCX"):
                            data = api.download_resume(resume_id, "docx")
                            if data:
                                st.download_button("Download DOCX", data, "resume.docx")
                    with dc3:
                        if st.button("📥 TXT"):
                            data = api.download_resume(resume_id, "txt")
                            if data:
                                st.download_button("Download TXT", data, "resume.txt")

    with tab2:
        resumes = api.list_resumes()
        if resumes:
            for r in resumes:
                with st.expander(f"📄 {r.get('title', 'Resume')} | ATS: {r.get('ats_score', 'N/A')} | v{r.get('version', 1)}"):
                    full = api.get_resume(r["id"])
                    if full:
                        st.json(full.get("content", {}))
        else:
            st.info("No resumes yet. Generate your first one!")


def show_resume_analyzer():
    st.markdown('<h1 class="main-header">🔍 Resume Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Get ATS scoring, keyword analysis, and improvement suggestions</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        input_method = st.radio("Input Method", ["📝 Paste Text", "📁 Upload File"], horizontal=True)

        resume_text = ""
        if input_method == "📝 Paste Text":
            resume_text = st.text_area("Resume Text", height=300, placeholder="Paste your resume here...")
        else:
            uploaded = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
            if uploaded:
                resume_text = f"[File uploaded: {uploaded.name}]"
                st.success(f"✅ {uploaded.name} uploaded")

        jd = st.text_area("Target Job Description (optional)", height=150, placeholder="Paste JD for targeted analysis...")

        if st.button("🔍 Analyze Resume", use_container_width=True, type="primary"):
            if not resume_text or resume_text.startswith("[File"):
                st.warning("Please provide resume text")
            else:
                with st.spinner("🧠 Analyzing your resume..."):
                    result = api.analyze_resume(resume_text, jd)
                    if result:
                        st.session_state["analysis_result"] = result

    with col2:
        if "analysis_result" in st.session_state:
            result = st.session_state["analysis_result"]

            # ATS Score
            score = result.get("ats_score", 0)
            if isinstance(score, (int, float)):
                score_class = "score-good" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
                st.markdown(f'<div class="score-gauge {score_class}">{score}</div>', unsafe_allow_html=True)
                st.caption("ATS Score (0-100)")

            # Section feedback
            sections = result.get("section_feedback", [])
            if sections:
                st.markdown("### 📋 Section-by-Section Feedback")
                for section in sections:
                    with st.expander(f"{section.get('section', 'Section')} — Score: {section.get('score', 'N/A')}"):
                        st.write(section.get("feedback", ""))
                        for sug in section.get("suggestions", []):
                            st.markdown(f"💡 {sug}")

            # Improvement suggestions
            suggestions = result.get("improvement_suggestions", [])
            if suggestions:
                st.markdown("### 💡 Improvement Suggestions")
                for s in suggestions:
                    st.markdown(f"• {s}")

            # Overall feedback
            if result.get("overall_feedback"):
                st.markdown("### 📝 Overall Feedback")
                st.info(result["overall_feedback"])


def show_cover_letter():
    st.markdown('<h1 class="main-header">✉️ Cover Letter Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate personalized cover letters with the perfect tone</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        company = st.text_input("🏢 Company Name", placeholder="Google")
        role = st.text_input("💼 Role", placeholder="Senior Software Engineer")
        jd = st.text_area("📋 Job Description", height=150, placeholder="Paste the JD...")
        tone = st.selectbox("🎭 Tone", ["formal", "concise", "creative"])
        skills = st.text_input("🔧 Key Skills to Highlight", placeholder="Python, Leadership, ML")
        context = st.text_input("💡 Additional Context", placeholder="Met at conference...")

        if st.button("✨ Generate Cover Letter", use_container_width=True, type="primary"):
            if not company or not role:
                st.warning("Company and role are required")
            else:
                with st.spinner("🧠 Crafting your cover letter..."):
                    skills_list = [s.strip() for s in skills.split(",")] if skills else []
                    result = api.generate_cover_letter(company, role, jd, skills_list, tone, context)
                    if result:
                        st.session_state["cover_letter"] = result

    with col2:
        st.markdown("### Preview")
        if "cover_letter" in st.session_state:
            cl = st.session_state["cover_letter"]
            st.markdown(f"**Tone:** {cl.get('tone', '')} | **Words:** {cl.get('word_count', 0)}")
            st.markdown("---")
            st.markdown(cl.get("content", ""))

            # Copy button
            st.code(cl.get("content", ""), language=None)


def show_job_tracker():
    st.markdown('<h1 class="main-header">🎯 Job Application Tracker</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Track every application from saved to offer</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 All Applications", "➕ Add New"])

    with tab2:
        with st.form("add_app"):
            c1, c2 = st.columns(2)
            with c1:
                company = st.text_input("Company")
                role = st.text_input("Role")
                status = st.selectbox("Status", ["saved", "applied", "screening", "interview", "technical", "final_round", "offer", "accepted", "rejected", "withdrawn"])
                location = st.text_input("Location")
            with c2:
                job_type = st.selectbox("Job Type", ["remote", "hybrid", "onsite"])
                source = st.selectbox("Source", ["linkedin", "indeed", "company_site", "referral", "other"])
                salary = st.text_input("Salary Range")
                excitement = st.slider("Excitement Level", 1, 5, 3)
            notes = st.text_area("Notes")
            jd = st.text_area("Job Description", height=100)

            if st.form_submit_button("Add Application", use_container_width=True):
                if company and role:
                    result = api.create_application({
                        "company": company, "role": role, "status": status,
                        "location": location, "job_type": job_type, "source": source,
                        "salary_range": salary, "excitement_level": excitement,
                        "notes": notes, "jd_text": jd,
                    })
                    if result:
                        st.success("✅ Application added!")
                        st.rerun()

    with tab1:
        # Status filter
        filter_status = st.selectbox("Filter by Status", ["All", "saved", "applied", "screening", "interview", "technical", "final_round", "offer", "accepted", "rejected"])
        apps = api.list_applications(filter_status if filter_status != "All" else None)

        if apps:
            # Status emoji mapping
            status_emoji = {
                "saved": "📌", "applied": "📤", "screening": "🔍",
                "interview": "🎤", "technical": "💻", "final_round": "🏆",
                "offer": "🎉", "accepted": "✅", "rejected": "❌", "withdrawn": "🚫",
            }

            for app in apps:
                emoji = status_emoji.get(app.get("status", ""), "📋")
                with st.expander(f"{emoji} {app.get('company', '')} — {app.get('role', '')} [{app.get('status', '').upper()}]"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Location:** {app.get('location', 'N/A')}")
                        st.write(f"**Type:** {app.get('job_type', 'N/A')}")
                        st.write(f"**Source:** {app.get('source', 'N/A')}")
                        st.write(f"**Salary:** {app.get('salary_range', 'N/A')}")
                    with c2:
                        st.write(f"**Excitement:** {'⭐' * app.get('excitement_level', 3)}")
                        st.write(f"**Applied:** {app.get('applied_date', 'N/A')}")
                        if app.get("notes"):
                            st.write(f"**Notes:** {app['notes']}")

                    # Status update
                    new_status = st.selectbox(
                        "Update Status", 
                        ["saved", "applied", "screening", "interview", "technical", "final_round", "offer", "accepted", "rejected", "withdrawn"],
                        index=["saved", "applied", "screening", "interview", "technical", "final_round", "offer", "accepted", "rejected", "withdrawn"].index(app.get("status", "saved")),
                        key=f"status_{app['id']}"
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Update", key=f"update_{app['id']}"):
                            api.update_application(app["id"], {"status": new_status})
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Delete", key=f"del_{app['id']}"):
                            api.delete_application(app["id"])
                            st.rerun()
        else:
            st.info("No applications yet. Add your first one!")


def show_referrals():
    st.markdown('<h1 class="main-header">👥 Referral Management</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Track your referral network and contacts</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 My Referrals", "➕ Add Contact"])

    with tab2:
        with st.form("add_ref"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Contact Name")
                company = st.text_input("Company")
                role = st.text_input("Role/Title")
            with c2:
                email = st.text_input("Email")
                linkedin = st.text_input("LinkedIn URL")
                relationship = st.selectbox("Relationship", ["colleague", "friend", "alumni", "mentor", "recruiter", "other"])
            notes = st.text_area("Notes")

            if st.form_submit_button("Add Referral Contact", use_container_width=True):
                if name and company:
                    result = api.create_referral({
                        "contact_name": name, "company": company, "role": role,
                        "email": email, "linkedin_url": linkedin,
                        "relationship": relationship, "notes": notes,
                    })
                    if result:
                        st.success("✅ Contact added!")
                        st.rerun()

    with tab1:
        refs = api.list_referrals()
        if refs:
            for ref in refs:
                status_color = {"pending": "🟡", "contacted": "🔵", "referred": "🟢", "declined": "🔴"}.get(ref.get("status", ""), "⚪")
                with st.expander(f"{status_color} {ref.get('contact_name', '')} — {ref.get('company', '')}"):
                    st.write(f"**Role:** {ref.get('role', 'N/A')}")
                    st.write(f"**Email:** {ref.get('email', 'N/A')}")
                    st.write(f"**Relationship:** {ref.get('relationship', 'N/A')}")
                    st.write(f"**Status:** {ref.get('status', 'pending')}")
                    if ref.get("notes"):
                        st.write(f"**Notes:** {ref['notes']}")

                    new_st = st.selectbox("Update Status", ["pending", "contacted", "referred", "declined"], key=f"ref_st_{ref['id']}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Update", key=f"ref_upd_{ref['id']}"):
                            api.update_referral(ref["id"], {"status": new_st})
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Delete", key=f"ref_del_{ref['id']}"):
                            api.delete_referral(ref["id"])
                            st.rerun()
        else:
            st.info("No referral contacts yet.")


def show_mock_interview():
    st.markdown('<h1 class="main-header">🎤 AI Mock Interview</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Practice with AI-generated questions and get instant feedback</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        role = st.text_input("🎯 Target Role", placeholder="Senior Software Engineer")
        company = st.text_input("🏢 Company (optional)", placeholder="Google")
        c1, c2 = st.columns(2)
        with c1:
            itype = st.selectbox("Interview Type", ["mixed", "hr", "technical"])
        with c2:
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        num_q = st.slider("Number of Questions", 3, 10, 5)

        if st.button("🎤 Generate Questions", use_container_width=True, type="primary"):
            if role:
                with st.spinner("🧠 Generating interview questions..."):
                    result = api.generate_interview(role, company, itype, difficulty, num_q)
                    if result:
                        st.session_state["interview_questions"] = result.get("questions", [])
                        st.session_state["interview_role"] = role
                        st.session_state["current_q"] = 0

    with col2:
        if "interview_questions" in st.session_state:
            questions = st.session_state["interview_questions"]
            if questions:
                st.markdown(f"### 📝 Questions ({len(questions)} total)")
                for i, q in enumerate(questions):
                    question_text = q.get("question", q) if isinstance(q, dict) else str(q)
                    q_type = q.get("type", "general") if isinstance(q, dict) else "general"

                    with st.expander(f"Q{i+1}: {question_text[:80]}..."):
                        st.markdown(f"**Question:** {question_text}")
                        st.markdown(f"**Type:** {q_type}")

                        answer = st.text_area("Your Answer", key=f"ans_{i}", height=100)
                        if st.button("✅ Evaluate", key=f"eval_{i}"):
                            if answer:
                                with st.spinner("Evaluating..."):
                                    evaluation = api.evaluate_interview(
                                        question_text, answer,
                                        st.session_state.get("interview_role", "Engineer"),
                                    )
                                    if evaluation:
                                        score = evaluation.get("score", 0)
                                        color = "score-good" if score >= 7 else ("score-mid" if score >= 5 else "score-low")
                                        st.markdown(f"**Score:** <span class='{color}'>{score}/10</span>", unsafe_allow_html=True)
                                        st.write(evaluation.get("feedback", ""))
                                        if evaluation.get("sample_answer"):
                                            st.markdown("**💡 Sample Answer:**")
                                            st.write(evaluation["sample_answer"])


def show_skill_gap():
    st.markdown('<h1 class="main-header">📊 Skill Gap Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Compare your skills against job requirements</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        jd = st.text_area("📋 Job Description", height=250, placeholder="Paste the target JD...")
        skills = st.text_input("🔧 Your Skills (comma-separated)", placeholder="Python, React, AWS, Docker...")

        if st.button("🔍 Analyze Gap", use_container_width=True, type="primary"):
            if jd:
                with st.spinner("🧠 Analyzing skill gaps..."):
                    skills_list = [s.strip() for s in skills.split(",")] if skills else None
                    result = api.analyze_skill_gap(jd, skills_list)
                    if result:
                        st.session_state["skill_gap"] = result

    with col2:
        if "skill_gap" in st.session_state:
            result = st.session_state["skill_gap"]

            # Score
            score = result.get("skill_score", 0)
            score_class = "score-good" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
            st.markdown(f'<div class="score-gauge {score_class}">{score}%</div>', unsafe_allow_html=True)
            st.caption("Skill Match Score")

            # Matched skills
            matched = result.get("matched_skills", [])
            if matched:
                st.markdown("### ✅ Matched Skills")
                st.write(", ".join(matched))

            # Missing skills
            missing = result.get("missing_skills", [])
            if missing:
                st.markdown("### ❌ Missing Skills")
                for skill in missing:
                    if isinstance(skill, dict):
                        importance = skill.get("importance", "unknown")
                        emoji = "🔴" if importance == "critical" else ("🟡" if importance == "important" else "🟢")
                        st.markdown(f"{emoji} **{skill.get('skill', '')}** — {importance} — {skill.get('estimated_learning_time', '')}")
                    else:
                        st.markdown(f"• {skill}")

            # Learning roadmap
            roadmap = result.get("learning_roadmap", [])
            if roadmap:
                st.markdown("### 🗺️ Learning Roadmap")
                for phase in roadmap:
                    if isinstance(phase, dict):
                        st.markdown(f"**Phase {phase.get('phase', '?')}: {phase.get('title', '')}** ({phase.get('duration', '')})")
                        for s in phase.get("skills", []):
                            st.markdown(f"  • {s}")

            # Projects
            projects = result.get("suggested_projects", [])
            if projects:
                st.markdown("### 💡 Suggested Projects")
                for p in projects:
                    st.markdown(f"• {p}")


def show_analytics():
    st.markdown('<h1 class="main-header">📈 Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Data-driven insights to optimize your job search</p>', unsafe_allow_html=True)

    analytics = api.get_analytics()
    if not analytics:
        st.info("Add some applications to see analytics!")
        return

    # Top metrics row
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "Applications", analytics.get("total_applications", 0), "📋"),
        (c2, "Response Rate", f"{analytics.get('response_rate', 0)}%", "📬"),
        (c3, "Interview Rate", f"{analytics.get('interview_rate', 0)}%", "🎤"),
        (c4, "Offer Rate", f"{analytics.get('offer_rate', 0)}%", "🎉"),
        (c5, "This Month", analytics.get("applications_this_month", 0), "📅"),
    ]
    for col, label, value, icon in metrics:
        with col:
            st.metric(f"{icon} {label}", value)

    st.markdown("---")

    # Charts
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd

    col1, col2 = st.columns(2)

    with col1:
        # Applications by status
        status_data = analytics.get("applications_by_status", {})
        if status_data:
            fig = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Applications by Status",
                color_discrete_sequence=px.colors.sequential.Purp,
                hole=0.4,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Application trend
        trend = analytics.get("application_trend", [])
        if trend:
            df = pd.DataFrame(trend)
            fig = px.line(
                df, x="month", y="count",
                title="Application Trend",
                markers=True,
                color_discrete_sequence=["#6C63FF"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis_title="Month",
                yaxis_title="Applications",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Source distribution
    col1, col2 = st.columns(2)
    with col1:
        source_data = analytics.get("source_distribution", {})
        if source_data:
            fig = px.bar(
                x=list(source_data.keys()),
                y=list(source_data.values()),
                title="Sources",
                color_discrete_sequence=["#4ECDC4"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top companies
        companies = analytics.get("top_companies", [])
        if companies:
            st.markdown("### 🏢 Top Companies")
            for c in companies[:5]:
                st.markdown(f"**{c.get('company', '')}** — {c.get('count', 0)} applications")

    # Resume performance
    resume_perf = analytics.get("resume_performance", [])
    if resume_perf:
        st.markdown("### 📄 Resume Performance")
        for rp in resume_perf:
            st.markdown(f"""<div class="feature-card">
                <strong>{rp.get('title', 'Resume')}</strong> | 
                ATS: {rp.get('ats_score', 'N/A')} | 
                Apps: {rp.get('applications', 0)} | 
                Responses: {rp.get('responses', 0)} |
                Rate: {rp.get('response_rate', 0)}%
            </div>""", unsafe_allow_html=True)


def show_email_generator():
    st.markdown('<h1 class="main-header">📧 Email Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Craft professional emails for your job search</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        email_type = st.selectbox("Email Type", ["cold_email", "referral_request", "follow_up", "thank_you"])
        recipient = st.text_input("Recipient Name", placeholder="John Smith")
        company = st.text_input("Company", placeholder="Google")
        role = st.text_input("Role", placeholder="Software Engineer")
        context = st.text_area("Additional Context", placeholder="Met at PyCon 2025...", height=100)
        tone = st.selectbox("Tone", ["professional", "friendly", "concise"])

        if st.button("✨ Generate Email", use_container_width=True, type="primary"):
            with st.spinner("🧠 Crafting your email..."):
                result = api.generate_email(email_type, recipient, company, role, context, tone)
                if result:
                    st.session_state["generated_email"] = result

    with col2:
        if "generated_email" in st.session_state:
            email = st.session_state["generated_email"]
            st.markdown("### 📬 Generated Email")
            st.markdown(f"**Subject:** {email.get('subject', '')}")
            st.markdown("---")
            st.markdown(email.get("body", ""))
            st.code(f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}", language=None)


def show_github_analyzer():
    st.markdown('<h1 class="main-header">🐙 GitHub Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Extract resume-ready bullet points from your GitHub projects</p>', unsafe_allow_html=True)

    username = st.text_input("GitHub Username", placeholder="octocat")
    max_repos = st.slider("Max Repos to Analyze", 5, 20, 10)

    if st.button("🔍 Analyze GitHub", use_container_width=True, type="primary"):
        if username:
            with st.spinner("🧠 Analyzing GitHub profile..."):
                result = api.analyze_github(username, max_repos)
                if result:
                    st.session_state["github_result"] = result

    if "github_result" in st.session_state:
        result = st.session_state["github_result"]

        # Tech stack
        tech = result.get("tech_stack", [])
        if tech:
            st.markdown("### 🔧 Tech Stack")
            st.write(", ".join(tech))

        # Resume bullet points
        points = result.get("resume_points", [])
        if points:
            st.markdown("### 📄 Resume-Ready Bullet Points")
            for p in points:
                st.markdown(f"• {p}")

        # Repository details
        repos = result.get("repos", [])
        if repos:
            st.markdown("### 📦 Repositories")
            for repo in repos:
                with st.expander(f"⭐ {repo.get('stars', 0)} | {repo.get('name', '')} ({repo.get('language', '')})"):
                    st.write(repo.get("description", ""))
                    st.write(f"🔗 {repo.get('url', '')}")


def show_ai_recruiter():
    st.markdown('<h1 class="main-header">🤖 AI Recruiter Simulator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Predict if a recruiter would shortlist or reject your application</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        resume_text = st.text_area("📄 Resume Text", height=250, placeholder="Paste your resume...")
        jd = st.text_area("📋 Job Description", height=200, placeholder="Paste the JD...")

        if st.button("🤖 Simulate Recruiter Review", use_container_width=True, type="primary"):
            if resume_text and jd:
                with st.spinner("🧠 Simulating recruiter review..."):
                    # Use the analyze endpoint for recruiter sim
                    from frontend.utils import api_client
                    import requests
                    try:
                        headers = api_client._headers()
                        resp = requests.post(
                            f"{api_client.BASE_URL}/api/analyzer/analyze",
                            json={"resume_text": resume_text, "job_description": jd},
                            headers=headers, timeout=120,
                        )
                        if resp.status_code == 200:
                            st.session_state["recruiter_result"] = resp.json()
                    except Exception as e:
                        st.error(str(e))

    with col2:
        if "recruiter_result" in st.session_state:
            result = st.session_state["recruiter_result"]
            score = result.get("ats_score", 0)
            if isinstance(score, (int, float)):
                decision = "SHORTLISTED ✅" if score >= 60 else "NEEDS IMPROVEMENT ⚠️"
                st.markdown(f"### Decision: {decision}")
                score_class = "score-good" if score >= 60 else "score-low"
                st.markdown(f'<div class="score-gauge {score_class}">{score}</div>', unsafe_allow_html=True)

            if result.get("strengths"):
                st.markdown("### 💪 Strengths")
                for s in result["strengths"]:
                    st.markdown(f"✅ {s}")

            if result.get("improvement_suggestions"):
                st.markdown("### 📝 Suggestions")
                for s in result["improvement_suggestions"]:
                    st.markdown(f"💡 {s}")


def show_ab_testing():
    st.markdown('<h1 class="main-header">🧪 Resume A/B Testing</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Compare resume versions and track which performs better</p>', unsafe_allow_html=True)

    resumes = api.list_resumes()
    if not resumes or len(resumes) < 2:
        st.info("You need at least 2 resumes to run A/B testing. Generate more resume variants!")
        if st.button("📄 Go to Resume Builder"):
            st.session_state["current_page"] = "📄 Resume Builder"
            st.rerun()
        return

    col1, col2 = st.columns(2)

    resume_titles = {f"{r['title']} (v{r['version']})": r for r in resumes}
    titles = list(resume_titles.keys())

    with col1:
        st.markdown("### Version A")
        sel_a = st.selectbox("Select Resume A", titles, key="ab_a")
        r_a = resume_titles[sel_a]
        st.metric("ATS Score", r_a.get("ats_score", "N/A"))

    with col2:
        st.markdown("### Version B")
        sel_b = st.selectbox("Select Resume B", titles, key="ab_b")
        r_b = resume_titles[sel_b]
        st.metric("ATS Score", r_b.get("ats_score", "N/A"))

    st.markdown("---")
    st.markdown("### 📊 Comparison")

    # Score comparison
    score_a = r_a.get("ats_score", 0) or 0
    score_b = r_b.get("ats_score", 0) or 0

    if score_a > score_b:
        st.success(f"🏆 Version A has a higher ATS score ({score_a} vs {score_b})")
    elif score_b > score_a:
        st.success(f"🏆 Version B has a higher ATS score ({score_b} vs {score_a})")
    else:
        st.info("Both versions have the same ATS score")

    st.markdown("Track application outcomes for each version to determine real-world performance!")


def show_settings():
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Configure your AI preferences and profile</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🧠 AI Configuration", "👤 Profile"])

    with tab1:
        st.markdown("### AI Model Settings")
        ai_status = api.get_ai_status()
        if ai_status:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Internet:** {'🟢 Available' if ai_status.get('internet_available') else '🔴 Offline'}")
                st.markdown(f"**Default Provider:** {ai_status.get('default_provider', 'gemini')}")
            with c2:
                st.markdown(f"**Gemini:** {'🟢 Configured' if ai_status.get('gemini_configured') else '⚪ Not set'}")
                st.markdown(f"**Gemini Model:** {ai_status.get('gemini_model', 'N/A')}")
            with c3:
                st.markdown(f"**Ollama:** {'🟢 Running' if ai_status.get('ollama_available') else '⚪ Not detected'}")
                st.markdown(f"**OpenAI:** {'🟢 Configured' if ai_status.get('openai_configured') else '⚪ Not set'}")

            st.markdown("---")
            st.markdown(f"**Total Tokens Used:** {ai_status.get('tokens_used', 0):,}")
            st.markdown(f"**Estimated Cost:** ${ai_status.get('estimated_cost_usd', 0):.4f}")

        st.markdown("---")
        st.markdown("### ⚠️ Configuration")
        st.info("To change AI settings, edit the `.env` file in the project root and restart the backend.")
        st.code("""# .env configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash
OPENAI_API_KEY=sk-your-key-here  # optional fallback
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
DEFAULT_MODEL_PROVIDER=gemini  # gemini, openai, ollama, auto
""", language="bash")

    with tab2:
        st.markdown("### Update Profile")
        user = st.session_state.get("user", {})

        with st.form("profile_form"):
            full_name = st.text_input("Full Name", value=user.get("full_name", ""))
            current_role = st.text_input("Current Role", value=user.get("current_role", "") or "")
            target_role = st.text_input("Target Role", value=user.get("target_role", "") or "")
            skills_str = st.text_input("Skills (comma-separated)", value=", ".join(user.get("skills", [])))
            exp_years = st.number_input("Years of Experience", value=user.get("experience_years", 0), min_value=0, max_value=50)

            if st.form_submit_button("Save Profile", use_container_width=True):
                skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
                result = api.update_profile({
                    "full_name": full_name,
                    "current_role": current_role,
                    "target_role": target_role,
                    "skills": skills_list,
                    "experience_years": exp_years,
                })
                if result:
                    st.success("✅ Profile updated!")
                    # Refresh user data
                    me = api.get_me()
                    if me:
                        st.session_state["user"] = me


if __name__ == "__main__":
    main()
