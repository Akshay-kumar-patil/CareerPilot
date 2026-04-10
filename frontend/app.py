"""
Career Automation & Job Intelligence Platform — Streamlit Frontend
Main application entry point with authentication and navigation.
"""
import base64
import json
import os
import sys

import requests
import streamlit as st

# FIX #6: Move all imports to top level so they don't re-execute on every rerun
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils.session import init_session, set_auth, clear_auth, is_authenticated
from frontend.utils import api_client as api

st.set_page_config(
    page_title="Career AI Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }

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
    .metric-value { font-size: 2rem; font-weight: 700; color: #6C63FF; }
    .metric-label { color: #8892B0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }
    .status-online { color: #4ECDC4; }
    .status-offline { color: #FF6B6B; }
    .auth-container {
        max-width: 400px; margin: 2rem auto; padding: 2rem;
        background: #1A1F2E; border-radius: 16px;
        border: 1px solid rgba(108, 99, 255, 0.2);
    }
    .stButton > button {
        background: linear-gradient(135deg, #6C63FF, #5A54E0);
        color: white; border: none; border-radius: 8px;
        padding: 0.5rem 2rem; font-weight: 600; transition: all 0.3s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5A54E0, #4845C7);
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: #1A1F2E; border-radius: 8px; padding: 8px 16px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] { background: #0E1117; }
    .feature-card {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(108, 99, 255, 0.15);
        border-radius: 12px; padding: 1.2rem; margin: 0.5rem 0; transition: all 0.3s;
    }
    .feature-card:hover { border-color: rgba(108, 99, 255, 0.5); }
    .score-gauge { font-size: 3rem; font-weight: 700; text-align: center; }
    .score-good { color: #4ECDC4; }
    .score-mid { color: #FFD93D; }
    .score-low { color: #FF6B6B; }
</style>
""", unsafe_allow_html=True)

init_session()

# FIX #12: Single source of truth for navigation — use only nav_selectbox
_PAGES = [
    "🏠 Dashboard", "📄 Resume Builder", "🔍 Resume Analyzer",
    "✉️ Cover Letter", "🎯 Job Tracker", "👥 Referrals",
    "🎤 Mock Interview", "📊 Skill Gap", "📈 Analytics",
    "📧 Email Generator", "🐙 GitHub Analyzer", "🤖 AI Recruiter",
    "🧪 A/B Testing", "⚙️ Settings",
]


def _navigate(page: str):
    """Navigate to a page via session state to be processed before the next run."""
    if page in _PAGES:
        st.session_state["_nav_target"] = page


def show_auth_page():
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
                # FIX #4: Show explicit error when fields are empty
                if submitted:
                    if not email or not password:
                        st.warning("Please fill in both email and password.")
                    else:
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
                # FIX #4: Explicit validation
                if submitted:
                    if not full_name or not email or not password:
                        st.warning("Please fill in all fields.")
                    else:
                        result = api.register(email, password, full_name)
                        if result:
                            set_auth(result["access_token"], result["user"])
                            st.rerun()

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

        ai_status = api.get_ai_status()
        if ai_status:
            gemini = ai_status.get("gemini_configured", False)
            online = ai_status.get("internet_available", False)
            groq_ok = ai_status.get("groq_configured", False)
            groq_avail = ai_status.get("groq_available", False)
            if gemini and online:
                status_text = "🟢 Gemini Online"
            elif groq_avail:
                status_text = "🟢 Groq Online (Llama 3.3)"
            elif online:
                status_text = "🟢 Online"
            else:
                status_text = "🔴 No AI"
            st.markdown(f"**AI Status:** {status_text}")
            if gemini:
                st.caption(f"Model: {ai_status.get('gemini_model', 'gemini-2.5-flash')}")
            elif groq_ok:
                st.caption(f"Fallback: {ai_status.get('groq_model', 'llama-3.3-70b-versatile')}")
            if ai_status.get("estimated_cost_usd", 0) > 0:
                st.caption(f"Cost: ${ai_status['estimated_cost_usd']:.4f}")

        st.markdown("---")

        # FIX #12: Single selectbox — nav_selectbox IS the current page
        st.selectbox(
            "Navigate",
            _PAGES,
            key="nav_selectbox",
            label_visibility="collapsed",
        )

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            clear_auth()
            st.rerun()


def delete_resume_local(resume_id: int):
    """Local fallback to bypass module caching issues."""
    import requests
    from frontend.utils.api_client import BASE_URL, _headers
    resp = requests.delete(
        f"{BASE_URL}/api/resume/{resume_id}",
        headers=_headers(),
        timeout=10,
    )
    return resp.status_code == 200


def _render_generated_resume_display(key_suffix: str = ""):
    """Helper to render the generated resume preview and download buttons."""
    if "last_resume" in st.session_state:
        r = st.session_state["last_resume"]
        resume_id = r.get("id")
        ats_score = r.get("ats_score") or 0

        # ── ATS Score Display ──
        st.markdown("---")
        st.markdown("### 📊 ATS Score")
        score_color = "#4ECDC4" if ats_score >= 70 else ("#FFD93D" if ats_score >= 40 else "#FF6B6B")
        score_label = "Excellent" if ats_score >= 70 else ("Good" if ats_score >= 50 else ("Needs Work" if ats_score >= 30 else "Low"))
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%); border-radius: 16px; border: 1px solid rgba(108, 99, 255, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 3.5rem; font-weight: 700; color: {score_color}; line-height: 1;">{ats_score}</div>
            <div style="font-size: 0.85rem; color: #8892B0; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">ATS Score</div>
            <div style="font-size: 1rem; font-weight: 600; color: {score_color}; margin-top: 4px;">{score_label}</div>
            <div style="margin-top: 8px; background: #0E1117; border-radius: 8px; height: 8px; overflow: hidden;">
                <div style="width: {ats_score}%; height: 100%; background: {score_color}; border-radius: 8px; transition: width 0.5s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show keyword analysis
        kw_matched = r.get("keywords_matched", [])
        kw_missing = r.get("keywords_missing", [])
        if kw_matched:
            with st.expander(f"✅ Matched Keywords ({len(kw_matched)})"):
                st.write(", ".join(kw_matched[:20]))
        if kw_missing:
            with st.expander(f"❌ Missing Keywords ({len(kw_missing)})"):
                st.write(", ".join(kw_missing[:15]))

        # ── PDF Preview ──
        st.markdown("### 📄 Resume Preview")
        pdf_cache_key = f"pdf_{resume_id}"
        if resume_id and pdf_cache_key not in st.session_state:
            with st.spinner("Rendering PDF preview..."):
                st.session_state[pdf_cache_key] = api.download_resume(resume_id, "pdf")

        pdf_data = st.session_state.get(pdf_cache_key) if resume_id else None

        if pdf_data:
            try:
                # Check if it's actually HTML (common fallback)
                is_html = pdf_data.strip().startswith(b"<!DOCTYPE") or pdf_data.strip().startswith(b"<html")
                if is_html:
                    st.info("ℹ️ PDF engine (WeasyPrint) requires system libraries. Showing high-fidelity HTML preview instead.")
                    b64_html = base64.b64encode(pdf_data).decode("utf-8")
                    st.markdown(
                        f'<iframe src="data:text/html;base64,{b64_html}" width="100%" height="600px" style="border: 1px solid rgba(108, 99, 255, 0.3); border-radius: 8px; background: white;"></iframe>',
                        unsafe_allow_html=True,
                    )
                else:
                    b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" style="border: 1px solid rgba(108, 99, 255, 0.3); border-radius: 8px;"></iframe>',
                        unsafe_allow_html=True,
                    )
            except Exception as e:
                st.error(f"Error rendering preview: {e}")
        else:
            # Fallback: Show resume content as formatted text
            content = r.get("content", {})
            if content:
                st.markdown(f"**{content.get('full_name', '')}**")
                # Summary stabilization
                raw_summary = content.get("summary", "")
                if isinstance(raw_summary, list):
                    summary_text = " ".join(raw_summary)
                else:
                    summary_text = str(raw_summary)
                if summary_text:
                    st.write(summary_text)
                st.caption("⚠️ PDF preview not available. Download the resume to view the full formatted version.")

        # ── Download Buttons ──
        st.markdown("### 📥 Download Resume")
        dc1, dc2 = st.columns(2)
        if resume_id:
            with dc1:
                if pdf_data:
                    is_html = pdf_data.strip().startswith(b"<!DOCTYPE") or pdf_data.strip().startswith(b"<html")
                    ext = "html" if is_html else "pdf"
                    mime = "text/html" if is_html else "application/pdf"
                    st.download_button(
                        f"📥 Download {ext.upper()}", pdf_data,
                        f"Resume_{resume_id}.{ext}", mime,
                        key=f"dl_pdf_gen_helper_{resume_id}_{key_suffix}", type="primary", use_container_width=True
                    )
            with dc2:
                docx_key = f"docx_{resume_id}"
                if docx_key not in st.session_state:
                    st.session_state[docx_key] = api.download_resume(resume_id, "docx")
                data_docx = st.session_state.get(docx_key)
                if data_docx:
                    st.download_button(
                        "📥 Download DOCX", data_docx,
                        f"Resume_{resume_id}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_docx_gen_helper_{resume_id}_{key_suffix}", use_container_width=True
                    )

        st.success(f"✅ Resume generated successfully! ATS Score: {ats_score}/100")


def main():
    if not is_authenticated():
        show_auth_page()
        return

    # Ensure nav is initialized
    if "nav_selectbox" not in st.session_state:
        st.session_state["nav_selectbox"] = "🏠 Dashboard"
    # Apply any pending navigation target (from quick actions, etc.)
    if "_nav_target" in st.session_state:
        target = st.session_state.pop("_nav_target")
        if target in _PAGES:
            st.session_state["nav_selectbox"] = target

    show_sidebar()

    selected = st.session_state["nav_selectbox"]

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

    page_funcs.get(selected, show_dashboard)()


# ===================== PAGE FUNCTIONS =====================

def show_dashboard():
    st.markdown('<h1 class="main-header">🏠 Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Welcome back! Here\'s your career overview.</p>', unsafe_allow_html=True)

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
    st.markdown("### ⚡ Quick Actions")
    cols = st.columns(4)
    actions = [
        ("📄", "Build Resume", "Generate an ATS-optimized resume", "📄 Resume Builder"),
        ("🔍", "Analyze Resume", "Get your ATS score", "🔍 Resume Analyzer"),
        ("🎯", "Track Application", "Add a new job application", "🎯 Job Tracker"),
        ("🎤", "Practice Interview", "Start a mock interview", "🎤 Mock Interview"),
    ]
    for i, (icon, title, desc, target) in enumerate(actions):
        with cols[i]:
            st.markdown(f"""<div class="feature-card" style="text-align:center; padding-bottom:0.5rem;">
                <div style="font-size:2rem; margin-bottom:0.5rem">{icon}</div>
                <div style="font-weight:600; margin-bottom:0.3rem">{title}</div>
                <div style="color:#8892B0; font-size:0.85rem; height:3em;">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Go to {title}", key=f"quick_action_{i}", use_container_width=True):
                _navigate(target)
                st.rerun()

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
            groq_ok = ai_status.get("groq_configured", False)
            groq_avail = ai_status.get("groq_available", False)
            st.markdown(f"**Groq:** {'🟢 Ready' if groq_avail else ('🟡 Key set' if groq_ok else '⚪ Not set')}")
            st.markdown(f"**Model:** {ai_status.get('groq_model', 'llama-3.3-70b-versatile')}")
        with c4:
            st.markdown(f"**Cost:** ${ai_status.get('estimated_cost_usd', 0):.4f}")
            st.markdown(f"**Tokens:** {ai_status.get('tokens_used', 0):,}")


def show_resume_builder():
    st.markdown('<h1 class="main-header">📄 Resume Builder</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate ATS-optimized developer resumes powered by AI</p>', unsafe_allow_html=True)

    tab1, tab_smart, tab2 = st.tabs(["✨ Generate New", "🔄 Smart Import", "📋 My Resumes"])

    # ──────────────────────────────────────────────────────────────
    # TAB: Smart Import
    # ──────────────────────────────────────────────────────────────
    with tab_smart:
        st.info(
            "📤 Upload your existing resume + paste a Job Description + add your GitHub username. "
            "The AI will extract your experience, enrich it with real GitHub project data, and "
            "tailor everything to the JD automatically."
        )

        si_col1, si_col2 = st.columns([1, 1])

        with si_col1:
            st.markdown("#### Step 1 — Upload Existing Resume")
            uploaded_resume = st.file_uploader(
                "Upload Resume (PDF / DOCX / TXT)",
                type=["pdf", "docx", "txt"],
                key="smart_import_resume",
            )

            extracted_text = st.session_state.get("si_extracted_text", "")
            if uploaded_resume:
                if st.button("📥 Extract Text", key="si_extract_btn"):
                    with st.spinner("Extracting text from your resume…"):
                        result = api.upload_resume_file(
                            uploaded_resume.read(),
                            uploaded_resume.name,
                            uploaded_resume.type or "application/octet-stream",
                        )
                    if result and result.get("extracted_text"):
                        extracted_text = result["extracted_text"]
                        st.session_state["si_extracted_text"] = extracted_text
                        st.success(f"✅ Extracted {len(extracted_text):,} characters from **{uploaded_resume.name}**")
                    else:
                        st.error("❌ Could not extract text. Try a different file format.")

            if extracted_text:
                with st.expander("📄 Preview extracted text", expanded=False):
                    st.text(extracted_text[:2000] + ("…" if len(extracted_text) > 2000 else ""))

            st.markdown("#### Step 2 — GitHub Username (Optional)")
            user = st.session_state.get("user", {})
            si_github = st.text_input(
                "GitHub Username",
                value=user.get("github_username", ""),
                placeholder="octocat",
                key="si_github_username",
            )
            si_max_repos = st.slider("Max repos to import", 3, 15, 8, key="si_max_repos")

            if si_github and st.button("🐙 Fetch GitHub Data", key="si_fetch_github"):
                with st.spinner(f"Fetching GitHub repos for **{si_github}**…"):
                    gh_result = api.analyze_github(si_github, si_max_repos)
                if gh_result and not gh_result.get("error"):
                    st.session_state["si_github_data"] = gh_result
                    repos = gh_result.get("repos", [])
                    st.success(f"✅ Fetched **{len(repos)}** repos · Tech: {', '.join(gh_result.get('tech_stack', [])[:6])}")
                else:
                    st.warning("⚠️ Could not fetch GitHub data — continuing without it.")
                    st.session_state.pop("si_github_data", None)

            if "si_github_data" in st.session_state:
                gh = st.session_state["si_github_data"]
                with st.expander("🐙 GitHub repos preview", expanded=False):
                    for r in gh.get("repos", [])[:5]:
                        st.markdown(f"- **{r['name']}** ({r.get('language','')}) — {r.get('description','')}")

        with si_col2:
            st.markdown("#### Step 3 — Target Job Description")
            si_jd = st.text_area(
                "Paste the Job Description",
                height=200,
                placeholder="We are looking for a Senior Software Engineer with expertise in Python, FastAPI, and cloud platforms…",
                key="si_jd",
            )

            st.markdown("#### Step 4 — Additional Context (Optional)")
            si_context = st.text_area(
                "Any extra info for the AI",
                height=80,
                placeholder="Highlight my open-source contributions. Prefer STAR format bullet points.",
                key="si_context",
            )

            st.markdown("---")
            ready = bool(extracted_text)
            if not ready:
                st.caption("⬅️ Upload and extract a resume first to enable generation.")

            if st.button(
                "🚀 Generate Tailored Resume",
                type="primary",
                use_container_width=True,
                key="si_generate_btn",
                disabled=not ready,
            ):
                if not si_jd.strip():
                    st.warning("Please paste a Job Description so the AI can tailor the resume.")
                else:
                    # Build enriched context string for the AI
                    gh_data = st.session_state.get("si_github_data", {})
                    github_context = ""
                    if gh_data:
                        repos_summary = "\n".join(
                            f"- {r['name']} ({r.get('language','')}, ⭐{r.get('stars',0)}): {r.get('description','')}"
                            for r in gh_data.get("repos", [])
                        )
                        points = "\n".join(f"- {p}" for p in gh_data.get("resume_points", []))
                        tech = ", ".join(gh_data.get("tech_stack", []))
                        github_context = (
                            f"\n\n=== GITHUB PROFILE DATA ===\n"
                            f"Tech Stack: {tech}\n\n"
                            f"Repositories:\n{repos_summary}\n\n"
                            f"AI-Generated Resume Points from GitHub:\n{points}"
                        )

                    enriched_context = (
                        f"=== EXISTING RESUME (extracted text) ===\n{extracted_text}"
                        + github_context
                        + (f"\n\n=== USER INSTRUCTIONS ===\n{si_context}" if si_context.strip() else "")
                    )

                    with st.spinner("🧠 AI is reading your resume, GitHub projects, and the JD… (this may take 2–3 minutes)"):
                        try:
                            result = api.generate_resume(
                                si_jd,
                                existing_resume=enriched_context,
                                additional_context=si_context or "",
                            )
                        except requests.exceptions.ReadTimeout:
                            st.error(
                                "⏱️ **Request timed out.** The AI is taking longer than expected. "
                                "Please wait 30 seconds and try again."
                            )
                            result = None
                        except requests.exceptions.ConnectionError:
                            st.error(
                                "🔌 **Connection error.** Could not reach the backend. "
                                "Please check your connection and try again."
                            )
                            result = None

                    if result:
                        st.session_state["last_resume"] = result
                        st.session_state.pop("si_extracted_text", None)
                        st.session_state.pop("si_github_data", None)
                        resume_id = result.get("id")
                        if resume_id:
                            for k in [f"pdf_{resume_id}", f"docx_{resume_id}"]:
                                st.session_state.pop(k, None)
                        st.balloons()

            # ── Display Result in Smart Import ──
            _render_generated_resume_display(key_suffix="smart")

    with tab1:
        st.info("💡 Fill in your details below. The AI agent will analyze your data and generate a professional developer resume matching top-tier formats.")

        c1, c2 = st.columns([1.5, 1])

        with c1:
            user = st.session_state.get("user", {})

            # ── Personal Information ──
            with st.expander("👤 Personal Information", expanded=True):
                fname = st.text_input("Full Name *", value=user.get("full_name", ""))
                st.markdown("**Contact Information**")
                cc1, cc2 = st.columns(2)
                email = cc1.text_input("Email *", value=user.get("email", ""))
                phone = cc2.text_input("Phone", "")
                cc3, cc4 = st.columns(2)
                loc = cc3.text_input("Location", "", placeholder="Mumbai, Maharashtra")
                port = cc4.text_input("Portfolio Website", value=user.get("portfolio_url", "") or "", placeholder="your-portfolio.com")

                st.markdown("**Social & Coding Profiles**")
                cc5, cc6 = st.columns(2)
                linked = cc5.text_input("LinkedIn URL", "", placeholder="linkedin.com/in/username")
                github = cc6.text_input("GitHub URL", value=f"github.com/{user.get('github_username', '')}" if user.get("github_username") else "", placeholder="github.com/username")
                cc7, cc8 = st.columns(2)
                leetcode = cc7.text_input("LeetCode URL", "", placeholder="leetcode.com/username")
                codechef = cc8.text_input("Other Coding Profile", "", placeholder="codechef.com/username")

            # ── Summary ──
            with st.expander("📝 Professional Summary"):
                summary_text = st.text_area(
                    "Write a brief professional summary (2-3 sentences). AI will optimize it.",
                    height=80,
                    placeholder="Computer Science student with expertise in full-stack development, IoT systems, and cloud computing. Experienced in developing scalable solutions and leading technical teams.",
                )

            # ── Education ──
            with st.expander("🎓 Education"):
                st.caption("Format: `Degree | School | Location | Dates | Grade`")
                edu_text = st.text_area(
                    "Education entries (one per line)",
                    height=100,
                    placeholder="Bachelor of Technology — Computer Science | Gyan Ganga Institute | Bhopal, MP | 2022-2026 | CGPA: 8.02\nHigher Secondary Education (12th - PCM) | Board of Secondary Education | MP | 2020-2021 | Percentage: 91%",
                )

            # ── Technical Skills ──
            with st.expander("🔧 Technical Skills"):
                st.caption("Format: `Category: Skill1, Skill2, Skill3`")
                existing_skills = ", ".join(user.get("skills", []))
                skills_text = st.text_area(
                    "Skills by category (one category per line)",
                    value=f"Skills: {existing_skills}" if existing_skills else "",
                    height=100,
                    placeholder="Programming & Databases: Python, JavaScript, Java, C/C++, SQL, MySQL, PostgreSQL, MongoDB\nFrameworks & Libraries: React.js, React Native, Node.js, Express.js, FastAPI, HTML5, CSS3\nCloud, DevOps & Tools: AWS, Google Cloud, Docker, Git, CI/CD, VS Code, Socket.io",
                )

            # ── Experience ──
            with st.expander("💼 Experience"):
                st.caption("Format: `Role | Company | Location | Dates`\nThen bullet points starting with `-`")
                exp_text = st.text_area(
                    "Experience entries",
                    height=180,
                    placeholder="Frappe Developer Intern | Alfastack Solutions Pvt Ltd | Remote | Sep 2025 – Dec 2025\n- Developed supplier portal using Frappe framework and React Frappe SDK\n- Built customer experience portal with Frappe REST APIs\n- Developed computer vision defect detection system using YOLOv8 and OpenCV\n\nFull Stack Developer & Development Team Lead | Ouranos Robotics Private Limited | Remote | Aug 2024 – Sep 2025\n- Led development team of 5+ members, establishing agile processes\n- Engineered real-time IoT monitoring platform using React, Node.js, and MQTT",
                )

            # ── Projects ──
            with st.expander("🚀 Projects"):
                st.caption("Format: `Name | Tech Stack | Live URL | Repo URL`\nThen bullet points starting with `-`")
                proj_text = st.text_area(
                    "Project entries",
                    height=180,
                    placeholder="PostgreSQL Cloud RDBMS Management System | PERN Stack, NeonDB | postgresstore-step.onrender.com | github.com/user/repo\n- Built secure cloud-based database system with role-based access control\n\nRoomieQ India - Roommate Finder | MERN Stack | | github.com/user/roomieq\n- Built full-stack application with real-time chat and filtering algorithms\n- Reduced application latency by 40% through optimization",
                )

            # ── Certifications ──
            with st.expander("📜 Certifications"):
                st.caption("Format: `Name | Issuer | Date`")
                cert_text = st.text_area(
                    "Certifications (one per line)",
                    height=80,
                    placeholder="AWS Cloud Practitioner | Amazon Web Services | 2024\nCisco CCNA (ITN, SRWE, ENSA) | Cisco | 2024\nJava Programming | Oracle Certified Associate | 2023",
                )

            # ── Achievements ──
            with st.expander("🏆 Achievements"):
                achiev_text = st.text_area(
                    "Achievements (one per line)",
                    height=80,
                    placeholder="TCS CodeVita 2025: AIR 4905 in Round 2 of TCS CodeVita Season 13\nSecond Place in TechSynergy IoT Showcase at Gyanostsav 2025\n3-Time College Topper on Code360 Leaderboard",
                )

            # ── Target JD ──
            with st.expander("🎯 Target Job Description", expanded=True):
                st.caption("Optional: Provide a Job Description to help the AI optimize your resume for a specific role.")
                jd = st.text_area("Job Description", height=150, placeholder="Paste JD or leave blank for a general professional resume...")
                context = st.text_input("Additional Instructions for AI", placeholder="e.g. Focus on backend skills, keep it to 1 page")

        # ── Right Column: Generate & Preview ──
        with c2:
            st.markdown("### 🚀 Generate & Preview")
            if st.button("🧠 Generate Resume with AI", use_container_width=True, type="primary"):
                if not fname:
                    st.warning("Full name is required!")
                else:
                    def parse_edus(text):
                        res = []
                        for line in text.strip().split("\n"):
                            if not line.strip():
                                continue
                            p = [x.strip() for x in line.split("|")]
                            while len(p) < 5:
                                p.append("")
                            res.append({"degree": p[0], "school": p[1], "location": p[2], "dates": p[3], "grade": p[4]})
                        return res

                    def parse_exp(text):
                        res = []
                        curr = None
                        bullets = []
                        for line in text.split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("-") or line.startswith("•"):
                                bullets.append(line.lstrip("-• "))
                            else:
                                if curr:
                                    curr["bullets"] = bullets
                                    res.append(curr)
                                    bullets = []
                                p = [x.strip() for x in line.split("|")]
                                while len(p) < 4:
                                    p.append("")
                                curr = {"title": p[0], "company": p[1], "location": p[2], "dates": p[3]}
                        if curr:
                            curr["bullets"] = bullets
                            res.append(curr)
                        return res

                    def parse_projects(text):
                        res = []
                        curr = None
                        bullets = []
                        for line in text.split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("-") or line.startswith("•"):
                                bullets.append(line.lstrip("-• "))
                            else:
                                if curr:
                                    curr["bullets"] = bullets
                                    res.append(curr)
                                    bullets = []
                                p = [x.strip() for x in line.split("|")]
                                while len(p) < 4:
                                    p.append("")
                                curr = {
                                    "name": p[0],
                                    "tech_stack": p[1],
                                    "live_url": p[2] if p[2] else "",
                                    "repo_url": p[3] if p[3] else "",
                                }
                        if curr:
                            curr["bullets"] = bullets
                            res.append(curr)
                        return res

                    def parse_skills(text):
                        res = {}
                        for line in text.split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                res[k.strip()] = v.strip()
                        return res

                    def parse_certs(text):
                        res = []
                        for line in text.split("\n"):
                            if not line.strip():
                                continue
                            p = [x.strip() for x in line.split("|")]
                            while len(p) < 3:
                                p.append("")
                            res.append({"name": p[0], "issuer": p[1], "date": p[2]})
                        return res

                    achievs = [l.strip() for l in achiev_text.split("\n") if l.strip()]

                    # Build contact with all links
                    contact_data = {
                        "location": loc, "email": email, "phone": phone,
                        "linkedin": linked, "github": github,
                        "portfolio": port, "leetcode": leetcode,
                    }
                    # Add other coding profile if provided
                    if codechef:
                        contact_data["codechef"] = codechef

                    resume_data = {
                        "full_name": fname,
                        "contact": contact_data,
                        "summary": summary_text,
                        "education": parse_edus(edu_text),
                        "experience": parse_exp(exp_text),
                        "projects": parse_projects(proj_text),
                        "skills": parse_skills(skills_text),
                        "certifications": parse_certs(cert_text),
                        "achievements": achievs,
                    }

                    with st.spinner("🧠 AI Agent is analyzing your data and building your resume... (this may take 2-3 minutes)"):
                        try:
                            result = api.generate_resume(
                                jd or "",
                                existing_resume=json.dumps(resume_data, indent=2),
                                additional_context=context,
                                resume_data=resume_data,
                            )
                        except requests.exceptions.ReadTimeout:
                            st.error(
                                "⏱️ **Request timed out.** The AI is taking longer than expected "
                                "(possibly due to a Render cold start). Please wait 30 seconds and try again."
                            )
                            result = None
                        except requests.exceptions.ConnectionError:
                            st.error(
                                "🔌 **Connection error.** Could not reach the backend server. "
                                "Please check your internet connection and try again."
                            )
                            result = None
                        if result:
                            st.session_state["last_resume"] = result
                            # Clear cached PDF/DOCX when a new resume is generated
                            resume_id = result.get("id")
                            if resume_id:
                                for k in [f"pdf_{resume_id}", f"docx_{resume_id}"]:
                                    st.session_state.pop(k, None)

            # ── Display Generated Resume ──
            _render_generated_resume_display(key_suffix="new")

    with tab2:
        resumes = api.list_resumes()
        if resumes:
            for r in resumes:
                with st.expander(f"📄 {r.get('title', 'Resume')} | ATS: {r.get('ats_score', 'N/A')} | v{r.get('version', 1)}"):
                    rid = r["id"]
                    c1, c2 = st.columns(2)
                    
                    # Store data in session state to avoid multiple API calls
                    pdf_key = f"list_pdf_{rid}"
                    docx_key = f"list_docx_{rid}"
                    
                    if pdf_key not in st.session_state:
                        with st.spinner("Loading PDF..."):
                            st.session_state[pdf_key] = api.download_resume(rid, "pdf")
                    if docx_key not in st.session_state:
                        with st.spinner("Loading DOCX..."):
                            st.session_state[docx_key] = api.download_resume(rid, "docx")
                            
                    with c1:
                        p_data = st.session_state.get(pdf_key)
                        if p_data:
                            is_html_list = p_data.strip().startswith(b"<!DOCTYPE") or p_data.strip().startswith(b"<html")
                            ext_list = "html" if is_html_list else "pdf"
                            mime_list = "text/html" if is_html_list else "application/pdf"
                            st.download_button(
                                f"📥 Download {ext_list.upper()}", p_data,
                                f"Resume_{rid}.{ext_list}", mime_list,
                                key=f"dl_pdf_list_{rid}", use_container_width=True
                            )
                    with c2:
                        d_data = st.session_state.get(docx_key)
                        if d_data:
                            st.download_button(
                                "📥 Download DOCX", d_data,
                                f"Resume_{rid}.docx",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"dl_docx_list_{rid}", use_container_width=True
                            )
                    
                    if st.button("🗑️ Delete", key=f"del_{rid}"):
                        if delete_resume_local(rid):
                            st.success("Deleted!")
                            st.rerun()
                    
                    # --- Text Preview ---
                    st.markdown("---")
                    detail_key = f"detail_{rid}"
                    if detail_key not in st.session_state:
                        with st.spinner("Fetching details..."):
                            st.session_state[detail_key] = api.get_resume(rid)
                    
                    full = st.session_state.get(detail_key)
                    if full:
                        content = full.get("content", {})
                        if isinstance(content, dict):
                            st.markdown(f"**Name:** {content.get('full_name', 'N/A')}")
                            
                            # Summary stabilization
                            raw_summary = content.get("summary", "")
                            if isinstance(raw_summary, list):
                                summary_text = " ".join(raw_summary)
                            else:
                                summary_text = str(raw_summary)
                            if summary_text:
                                st.markdown(f"**Summary:** {summary_text[:200]}...")
                                
                            # Skills stabilization
                            skills_data = content.get("skills", {})
                            if isinstance(skills_data, dict) and skills_data:
                                st.markdown("**Skills:**")
                                for cat, skills_val in skills_data.items():
                                    if isinstance(skills_val, list):
                                        st.markdown(f"  • **{cat}:** {', '.join(skills_val)}")
                                    elif isinstance(skills_val, str):
                                        st.markdown(f"  • **{cat}:** {skills_val}")
                        else:
                            st.json(content)
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
                with st.spinner("Extracting text from file..."):
                    result = api.upload_resume_file(
                        uploaded.read(),
                        uploaded.name,
                        uploaded.type or "application/octet-stream",
                    )
                    if result:
                        resume_text = result.get("extracted_text", "")
                        st.success(f"✅ {uploaded.name} — {len(resume_text)} characters extracted")
                    else:
                        st.error("Failed to extract text from file.")

        jd = st.text_area("Target Job Description (optional)", height=150, placeholder="Paste JD for targeted analysis...")

        if st.button("🔍 Analyze Resume", use_container_width=True, type="primary"):
            if not resume_text:
                st.warning("Please provide resume text or upload a file.")
            else:
                with st.spinner("🧠 Analyzing your resume..."):
                    result = api.analyze_resume(resume_text, jd)
                    # FIX: Only store if result is a valid analysis dict (not an error dict)
                    # api_client._handle_response returns None on HTTP errors,
                    # and the backend returns {"error": "..."} on AI failures.
                    # We must check for both cases before storing.
                    if result and "error" not in result:
                        st.session_state["analysis_result"] = result
                        st.session_state.pop("analysis_error", None)
                    elif result and "error" in result:
                        # Backend returned 200 but AI failed internally
                        st.session_state["analysis_error"] = result.get("error", "Unknown error")
                        st.session_state.pop("analysis_result", None)
                    # If result is None, _handle_response already showed st.error()

    with col2:
        # Show error state if analysis failed
        if "analysis_error" in st.session_state:
            st.error(f"🚨 Analysis failed: {st.session_state['analysis_error']}")
            st.info("Try again — if Gemini quota is exhausted, the system will auto-switch to Ollama.")

        if "analysis_result" in st.session_state:
            result = st.session_state["analysis_result"]

            # Show which model ran the analysis
            model_used = result.get("model_used", "")
            quota_fallback = result.get("quota_fallback", False)
            if model_used:
                if quota_fallback:
                    st.warning(f"⚡ Gemini quota exhausted — analysis ran on **Ollama** ({model_used})")
                else:
                    st.success(f"✅ Analysis powered by **{model_used.title()}**")

            # ATS Score gauge
            score = result.get("ats_score", 0)
            if isinstance(score, (int, float)):
                score_class = "score-good" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
                st.markdown(f'<div class="score-gauge {score_class}">{score}</div>', unsafe_allow_html=True)
                st.caption("ATS Score (0-100)")

            st.markdown("---")

            # Strengths
            strengths = result.get("strengths", [])
            if strengths:
                st.markdown("### 💪 Strengths")
                for s in strengths:
                    st.markdown(f"✅ {s}")

            # Section feedback
            sections = result.get("section_feedback", [])
            if sections:
                st.markdown("### 📋 Section-by-Section Feedback")
                for section in sections:
                    with st.expander(f"{section.get('section', 'Section')} — Score: {section.get('score', 'N/A')}"):
                        st.write(section.get("feedback", ""))
                        for sug in section.get("suggestions", []):
                            st.markdown(f"💡 {sug}")

            # Keyword analysis
            kw = result.get("keyword_analysis", {})
            if kw:
                st.markdown("### 🔑 Keyword Analysis")
                kw_score = kw.get("keyword_density_score", 0)
                c1, c2 = st.columns(2)
                with c1:
                    present = kw.get("present_keywords", [])
                    if present:
                        st.markdown("**✅ Present Keywords**")
                        st.write(", ".join(present))
                with c2:
                    missing = kw.get("missing_keywords", [])
                    if missing:
                        st.markdown("**❌ Missing Keywords**")
                        st.write(", ".join(missing))
                st.caption(f"Keyword density score: {kw_score}/100")

            # Fast keyword match (always shown when JD provided)
            kw_fast = result.get("keyword_match", {})
            if kw_fast:
                st.markdown("### ⚡ Fast Keyword Match")
                c1, c2, c3 = st.columns(3)
                c1.metric("Match Score", f"{kw_fast.get('score', 0)}%")
                c2.metric("Matched", kw_fast.get("total_matched", 0))
                c3.metric("JD Keywords", kw_fast.get("total_jd_keywords", 0))

            # Improvement suggestions
            suggestions = result.get("improvement_suggestions", [])
            if suggestions:
                st.markdown("### 💡 Improvement Suggestions")
                for s in suggestions:
                    st.markdown(f"• {s}")

            # Formatting issues
            fmt_issues = result.get("formatting_issues", [])
            if fmt_issues:
                st.markdown("### ⚠️ Formatting Issues")
                for f in fmt_issues:
                    st.markdown(f"• {f}")

            # Overall feedback
            overall = result.get("overall_feedback", "")
            if overall:
                st.markdown("### 📝 Overall Feedback")
                st.info(overall)


            if result.get("overall_feedback"):
                st.markdown("### 📝 Overall Feedback")
                st.info(result["overall_feedback"])


def download_cover_letter_local(content: dict, fmt: str):
    """Local fallback to bypass module caching issues."""
    import requests
    from frontend.utils.api_client import BASE_URL, _headers
    resp = requests.post(
        f"{BASE_URL}/api/cover-letter/download/{fmt}",
        json={"content": content},
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.content
    return None


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
                st.warning("Company and role are required.")
            else:
                with st.spinner("🧠 Crafting your cover letter..."):
                    skills_list = [s.strip() for s in skills.split(",")] if skills else []
                    result = api.generate_cover_letter(company, role, jd, skills_list, tone, context)
                    if result:
                        st.session_state["cover_letter"] = result
                        st.session_state.pop("cl_pdf", None)
                        st.session_state.pop("cl_docx", None)

    with col2:
        st.markdown("### Preview")
        if "cover_letter" in st.session_state:
            cl = st.session_state["cover_letter"]
            st.markdown(f"**Tone:** {cl.get('tone', '')} | **Words:** {cl.get('word_count', 0)}")
            st.markdown("---")
            
            content = cl.get("content", {})
            if isinstance(content, str):
                st.markdown(content)
            else:
                if "cl_pdf" not in st.session_state:
                    with st.spinner("Rendering PDF preview..."):
                        res = download_cover_letter_local(content, "pdf")
                        if res:
                            st.session_state["cl_pdf"] = res
                        
                pdf_data = st.session_state.get("cl_pdf")
                
                if pdf_data:
                    import base64
                    is_html = pdf_data.strip().startswith(b"<!DOCTYPE") or pdf_data.strip().startswith(b"<html")
                    if is_html:
                        st.info("ℹ️ Showing high-fidelity HTML preview.")
                        b64_html = base64.b64encode(pdf_data).decode("utf-8")
                        st.markdown(
                            f'<iframe src="data:text/html;base64,{b64_html}" width="100%" height="600px" style="border: 1px solid rgba(108, 99, 255, 0.3); border-radius: 8px; background: white;"></iframe>',
                            unsafe_allow_html=True,
                        )
                    else:
                        b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" style="border: 1px solid rgba(108, 99, 255, 0.3); border-radius: 8px;"></iframe>',
                            unsafe_allow_html=True,
                        )
                
                st.markdown("### 📥 Download Cover Letter")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if pdf_data:
                        ext = "html" if is_html else "pdf"
                        mime = "text/html" if is_html else "application/pdf"
                        st.download_button(
                            f"📥 Download {ext.upper()}", pdf_data,
                            f"CoverLetter.{ext}", mime,
                            key="dl_cl_pdf", type="primary", use_container_width=True
                        )
                with dc2:
                    if "cl_docx" not in st.session_state:
                        st.session_state["cl_docx"] = download_cover_letter_local(content, "docx")
                    docx_data = st.session_state.get("cl_docx")
                    if docx_data:
                        st.download_button(
                            "📥 Download DOCX", docx_data,
                            "CoverLetter.docx",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="dl_cl_docx", use_container_width=True
                        )


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
                else:
                    st.warning("Company and role are required.")

    with tab1:
        filter_status = st.selectbox("Filter by Status", ["All", "saved", "applied", "screening", "interview", "technical", "final_round", "offer", "accepted", "rejected"])
        apps = api.list_applications(filter_status if filter_status != "All" else None)

        if apps:
            status_emoji = {
                "saved": "📌", "applied": "📤", "screening": "🔍",
                "interview": "🎤", "technical": "💻", "final_round": "🏆",
                "offer": "🎉", "accepted": "✅", "rejected": "❌", "withdrawn": "🚫",
            }
            statuses = ["saved", "applied", "screening", "interview", "technical", "final_round", "offer", "accepted", "rejected", "withdrawn"]

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
                        st.write(f"**Excitement:** {'⭐' * (app.get('excitement_level') or 3)}")
                        st.write(f"**Applied:** {app.get('applied_date', 'N/A')}")
                        if app.get("notes"):
                            st.write(f"**Notes:** {app['notes']}")

                    current_status = app.get("status", "saved")
                    try:
                        current_index = statuses.index(current_status)
                    except ValueError:
                        current_index = 0

                    new_status = st.selectbox(
                        "Update Status", statuses,
                        index=current_index,
                        key=f"status_{app['id']}",
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
                else:
                    st.warning("Contact name and company are required.")

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
            if not role:
                st.warning("Please enter a target role.")
            else:
                with st.spinner("🧠 Generating interview questions..."):
                    result = api.generate_interview(role, company, itype, difficulty, num_q)
                    if result:
                        st.session_state["interview_questions"] = result.get("questions", [])
                        st.session_state["interview_role"] = role

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
                            else:
                                st.warning("Please write your answer first.")


def show_skill_gap():
    st.markdown('<h1 class="main-header">📊 Skill Gap Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Compare your skills against job requirements</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        jd = st.text_area("📋 Job Description", height=250, placeholder="Paste the target JD...")
        skills = st.text_input("🔧 Your Skills (comma-separated)", placeholder="Python, React, AWS, Docker...")

        if st.button("🔍 Analyze Gap", use_container_width=True, type="primary"):
            if not jd:
                st.warning("Please provide a job description.")
            else:
                with st.spinner("🧠 Analyzing skill gaps..."):
                    skills_list = [s.strip() for s in skills.split(",")] if skills else None
                    result = api.analyze_skill_gap(jd, skills_list)
                    if result:
                        st.session_state["skill_gap"] = result

    with col2:
        if "skill_gap" in st.session_state:
            result = st.session_state["skill_gap"]

            score = result.get("skill_score", 0)
            score_class = "score-good" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
            st.markdown(f'<div class="score-gauge {score_class}">{score}%</div>', unsafe_allow_html=True)
            st.caption("Skill Match Score")

            matched = result.get("matched_skills", [])
            if matched:
                st.markdown("### ✅ Matched Skills")
                st.write(", ".join(matched))

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

            roadmap = result.get("learning_roadmap", [])
            if roadmap:
                st.markdown("### 🗺️ Learning Roadmap")
                for phase in roadmap:
                    if isinstance(phase, dict):
                        st.markdown(f"**Phase {phase.get('phase', '?')}: {phase.get('title', '')}** ({phase.get('duration', '')})")
                        for s in phase.get("skills", []):
                            st.markdown(f"  • {s}")

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

    # FIX #6: plotly already imported at top of file
    col1, col2 = st.columns(2)

    with col1:
        status_data = analytics.get("applications_by_status", {})
        if status_data:
            fig = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Applications by Status",
                color_discrete_sequence=px.colors.sequential.Purp,
                hole=0.4,
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        trend = analytics.get("application_trend", [])
        if trend:
            df = pd.DataFrame(trend)
            fig = px.line(df, x="month", y="count", title="Application Trend", markers=True, color_discrete_sequence=["#6C63FF"])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA", xaxis_title="Month", yaxis_title="Applications",
            )
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        source_data = analytics.get("source_distribution", {})
        if source_data:
            fig = px.bar(x=list(source_data.keys()), y=list(source_data.values()), title="Sources", color_discrete_sequence=["#4ECDC4"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        companies = analytics.get("top_companies", [])
        if companies:
            st.markdown("### 🏢 Top Companies")
            for c in companies[:5]:
                st.markdown(f"**{c.get('company', '')}** — {c.get('count', 0)} applications")

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

    user = st.session_state.get("user", {})
    # FIX #7: Pre-fill from user profile instead of hardcoded value
    username = st.text_input("GitHub Username", value=user.get("github_username", ""), placeholder="octocat")
    max_repos = st.slider("Max Repos to Analyze", 5, 20, 10)

    if st.button("🔍 Analyze GitHub", use_container_width=True, type="primary"):
        if not username:
            st.warning("Please enter a GitHub username.")
        else:
            with st.spinner("🧠 Analyzing GitHub profile..."):
                result = api.analyze_github(username, max_repos)
                if result:
                    st.session_state["github_result"] = result

    if "github_result" in st.session_state:
        result = st.session_state["github_result"]

        tech = result.get("tech_stack", [])
        if tech:
            st.markdown("### 🔧 Tech Stack")
            st.write(", ".join(tech))

        points = result.get("resume_points", [])
        if points:
            st.markdown("### 📄 Resume-Ready Bullet Points")
            for p in points:
                st.markdown(f"• {p}")

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
        # NEW: Input method selection similar to Analyzer
        input_method = st.radio("Resume Input", ["📝 Paste Text", "📁 Upload File", "✨ Use Generated Resume"], horizontal=True)

        resume_text = ""
        
        if input_method == "📝 Paste Text":
            resume_text = st.text_area("📄 Resume Text", height=250, placeholder="Paste your resume...")
        elif input_method == "📁 Upload File":
            uploaded = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"], key="recruiter_upload")
            if uploaded:
                with st.spinner("Extracting text from file..."):
                    result = api.upload_resume_file(
                        uploaded.read(),
                        uploaded.name,
                        uploaded.type or "application/octet-stream",
                    )
                    if result:
                        resume_text = result.get("extracted_text", "")
                        st.success(f"✅ {uploaded.name} extracted")
                    else:
                        st.error("Failed to extract text.")
        else: # Use Generated Resume
            last_resume = st.session_state.get("last_resume")
            if last_resume:
                # Extract text from the generated resume structure
                content = last_resume.get("content", {})
                raw = last_resume.get("raw_text", "")
                if raw:
                    resume_text = raw
                    st.success("✅ Using your most recently generated resume")
                else:
                    st.info("Converting structured resume to text...")
                    resume_text = json.dumps(content, indent=2)
            else:
                st.warning("No generated resume found. Please build one first or use another input method.")

        jd = st.text_area("📋 Job Description", height=200, placeholder="Paste the JD...")

        if st.button("🤖 Simulate Recruiter Review", use_container_width=True, type="primary"):
            if not resume_text:
                st.warning("Please provide a resume using one of the input methods.")
            elif not jd:
                st.warning("Please provide a job description.")
            else:
                with st.spinner("🧠 Simulating recruiter review..."):
                    result = api.simulate_recruiter(resume_text, jd)
                    if result:
                        st.session_state["recruiter_result"] = result

    with col2:
        if "recruiter_result" in st.session_state:
            result = st.session_state["recruiter_result"]
            
            decision = result.get("decision", "rejected").upper()
            confidence = result.get("confidence", 0.0)
            
            if decision == "SHORTLISTED":
                st.success(f"### Decision: {decision} ✅")
            else:
                st.error(f"### Decision: REJECTED ❌")
                
            st.metric("Recruiter Confidence", f"{confidence*100:.0f}%")
            
            st.markdown("#### 🧠 Recruiter Reasoning")
            for r in result.get("reasoning", []):
                st.write(f"• {r}")
                
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ✅ Strengths")
                for s in result.get("strengths", []):
                    st.write(f"• {s}")
            with c2:
                st.markdown("#### ⚠️ Weaknesses")
                for w in result.get("weaknesses", []):
                    st.write(f"• {w}")
                    
            st.markdown("#### 💡 Suggestions to get Shortlisted")
            for sug in result.get("suggestions", []):
                st.info(sug)
                
            if result.get("comparison_notes"):
                st.caption(f"📝 *Comparison Note: {result['comparison_notes']}*")
            
            # Show which model was used
            model = result.get("model_used", "unknown")
            st.caption(f"Simulator powered by: {model.capitalize()}")


def show_ab_testing():
    st.markdown('<h1 class="main-header">🧪 Resume A/B Testing</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Compare resume versions and track which performs better</p>', unsafe_allow_html=True)

    resumes = api.list_resumes()
    if not resumes or len(resumes) < 2:
        st.info("You need at least 2 resumes to run A/B testing. Generate more resume variants!")
        if st.button("📄 Go to Resume Builder"):
            # FIX #12: Use _navigate helper
            _navigate("📄 Resume Builder")
            st.rerun()
        return

    resume_titles = {f"{r['title']} (v{r['version']})": r for r in resumes}
    titles = list(resume_titles.keys())

    col1, col2 = st.columns(2)
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
GEMINI_MODEL=gemini-2.5-flash
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
            skills_str = st.text_input("Skills (comma-separated)", value=", ".join(user.get("skills", []) or []))
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
                    me = api.get_me()
                    if me:
                        st.session_state["user"] = me


if __name__ == "__main__":
    main()
