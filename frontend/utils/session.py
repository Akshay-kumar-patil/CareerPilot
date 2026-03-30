"""Session state management utilities."""
import streamlit as st


def init_session():
    """Initialize all session state variables."""
    defaults = {
        "token": None,
        "user": None,
        "authenticated": False,
        "ai_status": None,
        "current_page": "🏠 Dashboard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_auth(token: str, user: dict):
    """Set authentication state."""
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.authenticated = True


def clear_auth():
    """Clear authentication state."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.authenticated = False


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False) and st.session_state.get("token") is not None
