"""Shared UI helpers: page setup, sidebar, safe LLM calls, step parsing, chat widget."""
import re
import openai
import streamlit as st
from helper_functions.utility import check_password

APP_NAME = "SGStartBiz"
DELIMITER = "####"
GENERIC_ERROR = (
    "Sorry, something went wrong while contacting the AI service. "
    "Please try again in a moment. If it keeps happening, check the API key and your connection."
)


def friendly_error(exc):
    """Map an exception to a message a non-technical user can act on."""
    if isinstance(exc, openai.AuthenticationError) or (
        isinstance(exc, RuntimeError) and "OPENAI_API_KEY" in str(exc)
    ):
        return "The AI service rejected the API key, or no key is configured. Please check the OPENAI_API_KEY setting."
    if isinstance(exc, openai.RateLimitError):
        return "The AI service is busy or the usage quota is used up. Please wait a moment and try again."
    if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
        return "Could not reach the AI service. Please check your internet connection and try again."
    return GENERIC_ERROR


def show_verification_warning(unverified):
    """Warn when the AI text cites dollar figures that are not in the source data."""
    if unverified:
        st.warning(
            "Some figures in the AI-generated text could not be matched to the app's data: "
            + ", ".join(unverified)
            + ". Please verify them with the official sources before relying on them."
        )


def setup_page(title, icon):
    """Common page config, CSS, password gate and sidebar. Call first on every page."""
    st.set_page_config(page_title=f"{title} | {APP_NAME}", page_icon=icon, layout="wide")
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; max-width: 1100px;}
        [data-testid="stMetric"] {background: #F0F4F9; border-radius: 10px; padding: 12px 16px;}
        [data-testid="stMetricLabel"] {color: #52606d;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if not check_password():
        st.stop()
    with st.sidebar:
        st.markdown(f"## {icon} {APP_NAME}")
        st.caption("AI-powered guide to starting a business in Singapore")
        st.divider()
        st.caption(
            "Prototype for educational purposes only. Not for real-world decisions. "
            "AI output may be inaccurate."
        )


def safe_call(fn, *args, **kwargs):
    """Run an LLM-backed function; show a friendly error and return None on failure."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - surface any API/network failure politely
        st.error(friendly_error(exc))
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return None


def parse_steps(response, titles):
    """Split a '####'-delimited LLM response into (title, text) pairs."""
    sections = []
    for part in response.split(DELIMITER):
        # Remove the trailing 'Step N:' label that precedes each delimiter
        cleaned = re.sub(r"(?is)(^\s*step\s*\d+\s*:?\s*$)|(\s*step\s*\d+\s*:?\s*$)", "", part).strip()
        if cleaned:
            sections.append(cleaned)
    out = []
    for i, text in enumerate(sections):
        title = titles[i] if i < len(titles) else f"Additional notes {i - len(titles) + 1}"
        out.append((title, text))
    return out


def render_chat(history_key, answer_fn, base_context, placeholder):
    """Chat-style follow-up Q&A with persistent history.

    answer_fn(question, context) -> str. Safety checks run before answering.
    """
    from logics.business_query_handler import run_safety_checks

    st.subheader("Ask a follow-up question")
    history = st.session_state.setdefault(history_key, [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input(placeholder, key=f"{history_key}_input")
    if not question:
        return

    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                is_safe, safety_msg = run_safety_checks(question)
            except Exception as exc:  # noqa: BLE001
                is_safe, safety_msg = False, friendly_error(exc)
            if not is_safe:
                answer = safety_msg
            else:
                recent = "\n".join(
                    f"{m['role'].title()}: {m['content']}" for m in history[-7:-1]
                )
                context = f"{base_context}\n\nRecent conversation:\n{recent}" if recent else base_context
                try:
                    answer = answer_fn(question, context[:3000])
                except Exception as exc:  # noqa: BLE001
                    answer = friendly_error(exc)
        st.markdown(answer)
    history.append({"role": "assistant", "content": answer})
