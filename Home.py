import streamlit as st
from helper_functions.ui import setup_page

setup_page("Home", "🏢")

st.title("SGStartBiz")
st.subheader("Your AI-Powered Guide to Starting a Business in Singapore")

with st.expander("IMPORTANT NOTICE - Please Read Before Proceeding"):
    st.write("""
**IMPORTANT NOTICE:** This web application is a prototype developed for **educational purposes only.** The information provided here is **NOT intended for real-world usage** and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

**Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.**

Always consult with qualified professionals for accurate and personalised advice.
""")

st.markdown(
    "SGStartBiz consolidates information from **ACRA**, **GoBusiness**, **IRAS**, **MOM** and "
    "**CPF Board** to give aspiring entrepreneurs personalised guidance on starting a business "
    "in Singapore."
)

st.markdown("### What you can do here")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("#### 📋 Business Registration Guide")
        st.write(
            "Get a personalised step-by-step guide for registering your business based on your "
            "chosen structure, industry and activities."
        )
        st.page_link("pages/1_Business_Registration_Guide.py", label="Open the guide", icon="➡️")

with col2:
    with st.container(border=True):
        st.markdown("#### 💰 Startup Cost Estimator")
        st.write(
            "Estimate your startup costs, including registration fees, licensing, CPF "
            "obligations and tax."
        )
        st.page_link("pages/2_Startup_Cost_Estimator.py", label="Open the estimator", icon="➡️")

st.markdown("### How it works")
c1, c2, c3 = st.columns(3)
c1.metric("1. Tell us", "Your situation")
c2.metric("2. We combine", "Official data + AI")
c3.metric("3. You get", "Tailored guidance")

st.caption(
    "Want the technical details? See **About Us** and **Methodology** in the sidebar."
)
