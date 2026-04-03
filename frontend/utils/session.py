"""Session state management utilities with persistence across page reloads."""
import streamlit as st
import logging

logger = logging.getLogger(__name__)


def init_session():
    """Initialize session state, restoring auth from query params if available."""
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

    # Restore session from query params on reload
    if not st.session_state.get("authenticated") and not st.session_state.get("token"):
        _restore_from_query_params()


def _restore_from_query_params():
    """Try to restore auth state from query params (survives page reload)."""
    try:
        params = st.query_params
        saved_token = params.get("auth_token")
        if saved_token:
            # Validate the token by calling /api/auth/me
            from frontend.utils import api_client as api
            st.session_state["token"] = saved_token
            user = api.get_me()
            if user:
                st.session_state["user"] = user
                st.session_state["authenticated"] = True
                logger.info("Session restored from query params")
            else:
                # Token is invalid/expired — clear it
                st.session_state["token"] = None
                st.session_state["authenticated"] = False
                st.query_params.clear()
                logger.info("Saved token was invalid, cleared")
    except Exception as e:
        logger.warning(f"Failed to restore session: {e}")


def set_auth(token: str, user: dict):
    """Set authentication state and persist token in query params."""
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.authenticated = True
    # Persist token in query params so it survives page reload
    try:
        st.query_params["auth_token"] = token
    except Exception:
        pass


def clear_auth():
    """Clear authentication state and remove persisted token."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.authenticated = False
    try:
        st.query_params.clear()
    except Exception:
        pass


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False) and st.session_state.get("token") is not None
