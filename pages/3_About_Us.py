import streamlit as st
import pandas as pd
from helper_functions.utility import check_password

st.set_page_config(
    layout="wide",
    page_title="About Us"
)

if not check_password():
    st.stop()

st.title("About Us")

st.markdown("---")

# --- Project Scope ---
st.header("Project Scope")
st.markdown("""
**SGStartBiz** is a web application developed as a capstone project for the AI Champions Bootcamp.
It consolidates information from multiple Singapore government agencies to provide a one-stop platform
for aspiring entrepreneurs navigating the process of starting a business in Singapore.

The application is designed to help users understand the business registration process, estimate
startup costs, and receive personalised guidance — all powered by Large Language Models (LLMs).
""")

# --- Objectives ---
st.header("Objectives")
st.markdown("""
1. **Consolidate Information** — Aggregate data from various official and trustworthy sources
   (ACRA, GoBusiness, IRAS, MOM, CPF Board) into a unified platform.

2. **Personalise User Experience** — Allow users to input generic, non-personally identifiable
   information to receive tailored guidance relevant to their specific business scenario.

3. **Enhance Understanding** — Generate interactive content including explanations, elaborations,
   and responses to follow-up questions to help users understand the business registration process.

4. **Present Information Effectively** — Present information through a combination of text,
   data tables, charts, and interactive forms to enhance user engagement.
""")

# --- Data Sources ---
st.header("Data Sources")
st.markdown("The following official and trustworthy sources were used to curate the knowledge base:")

data_sources = pd.DataFrame([
    {
        "Source": "ACRA (Accounting and Corporate Regulatory Authority)",
        "URL": "https://www.acra.gov.sg",
        "Information Used": "Business structures, registration steps, fees, compliance requirements",
        "Last Accessed": "September 2026"
    },
    {
        "Source": "GoBusiness",
        "URL": "https://www.gobusiness.gov.sg",
        "Information Used": "Industry-specific licences and permits, e-Adviser tools",
        "Last Accessed": "September 2026"
    },
    {
        "Source": "IRAS (Inland Revenue Authority of Singapore)",
        "URL": "https://www.iras.gov.sg",
        "Information Used": "Corporate tax rates, GST thresholds, startup tax exemptions, filing requirements",
        "Last Accessed": "September 2026"
    },
    {
        "Source": "MOM (Ministry of Manpower)",
        "URL": "https://www.mom.gov.sg",
        "Information Used": "Employment Act, work pass types and salary thresholds, fair hiring requirements",
        "Last Accessed": "September 2026"
    },
    {
        "Source": "CPF Board (Central Provident Fund)",
        "URL": "https://www.cpf.gov.sg",
        "Information Used": "Employer and employee CPF contribution rates by age, wage ceilings",
        "Last Accessed": "September 2026"
    }
])

st.dataframe(data_sources, use_container_width=True, hide_index=True)

# --- Features ---
st.header("Features")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Business Registration Guide")
    st.markdown("""
    - Select your business structure and industry
    - Describe your business activities
    - Receive a personalised step-by-step guide
    - View required documents and licences
    - Ask follow-up questions
    """)

with col2:
    st.subheader("Startup Cost Estimator")
    st.markdown("""
    - Input your business parameters
    - Get an algorithmic cost breakdown
    - View costs as tables and charts
    - Receive AI-powered cost explanations
    - Understand tax exemptions and benefits
    """)

st.markdown("---")

st.header("Technical Overview")
st.markdown("""
- **Frontend**: Streamlit (multi-page application)
- **LLM**: OpenAI GPT-4o-mini
- **Data Layer**: Curated JSON knowledge base from official sources
- **Safety**: Prompt injection detection (few-shot classification) + OpenAI Content Moderation API
- **Cost Computation**: Algorithmic (Python) — LLM explains but does not generate numbers
- **Deployment**: Streamlit Community Cloud
""")
