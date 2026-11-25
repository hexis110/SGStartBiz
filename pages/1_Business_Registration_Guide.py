import streamlit as st
from helper_functions.ui import setup_page, safe_call, parse_steps, render_chat, show_verification_warning
from logics.business_query_handler import (
    generate_registration_guide,
    run_safety_checks,
    handle_followup_question,
    get_structure_data,
    get_licensing_data,
    find_unverified_amounts,
    reference_text_for_guide,
)

setup_page("Registration Guide", "📋")

st.title("📋 Business Registration Guide")
st.markdown("Get a personalised step-by-step guide for registering your business in Singapore.")
st.caption("For educational purposes only. Please verify all information with official sources.")

STRUCTURE_OPTIONS = {
    "Sole Proprietorship": "sole_proprietorship",
    "Partnership": "partnership",
    "Limited Partnership (LP)": "limited_partnership",
    "Limited Liability Partnership (LLP)": "limited_liability_partnership",
    "Private Limited Company (Pte Ltd)": "private_limited_company",
}

INDUSTRY_OPTIONS = {
    "Food & Beverage": "food_and_beverage",
    "Retail": "retail",
    "Professional Services": "professional_services",
    "Technology / IT": "technology",
    "Education & Training": "education",
    "Healthcare": "healthcare",
    "Construction": "construction",
    "Others": "others",
}

EXAMPLES = [
    "Cafe serving coffee and pastries",
    "Online shop selling handmade jewellery",
    "Freelance web design and IT consulting",
]

STEP_TITLES = [
    "Business Structure Overview",
    "Step-by-Step Registration Process",
    "Licences & Permits Required",
    "Ongoing Compliance Requirements",
    "Summary & Useful Tips",
]

MAX_DESCRIPTION_CHARS = 500

# Example buttons fill the text area (set before the widget is created)
st.caption("Try an example:")
ex_cols = st.columns(len(EXAMPLES))
for col, ex in zip(ex_cols, EXAMPLES):
    if col.button(ex, key=f"ex_{ex}", width="stretch"):
        st.session_state["guide_description"] = ex

with st.form(key="registration_guide_form"):
    st.subheader("Tell us about your business")
    col1, col2 = st.columns(2)
    with col1:
        structure_display = st.selectbox(
            "Business Structure",
            options=list(STRUCTURE_OPTIONS.keys()),
            help="Choose the type of business entity you plan to register.",
        )
    with col2:
        industry_display = st.selectbox(
            "Industry",
            options=list(INDUSTRY_OPTIONS.keys()),
            help="Select the industry closest to your business activities.",
        )

    business_description = st.text_area(
        "Describe your business activities",
        key="guide_description",
        height=100,
        max_chars=MAX_DESCRIPTION_CHARS,
        placeholder="e.g., Online retail selling handmade jewellery",
        help="Do not include personal or sensitive information.",
    )

    col3, col4 = st.columns(2)
    with col3:
        hiring_employees = st.checkbox("I plan to hire employees")
    with col4:
        high_revenue = st.checkbox("I expect annual revenue above $1M")

    submitted = st.form_submit_button(
        "Generate my registration guide", type="primary", width="stretch"
    )

if submitted:
    if not business_description.strip():
        st.error("Please describe your business activities to get a personalised guide.")
        st.stop()

    structure_key = STRUCTURE_OPTIONS[structure_display]
    industry_key = INDUSTRY_OPTIONS[industry_display]

    with st.spinner("Checking your input..."):
        safety = safe_call(run_safety_checks, business_description)
    if safety is None:
        st.stop()
    is_safe, safety_msg = safety
    if not is_safe:
        st.error(safety_msg)
        st.stop()

    with st.spinner("Generating your personalised guide... this can take 10-20 seconds"):
        guide = safe_call(
            generate_registration_guide,
            structure_key=structure_key,
            industry_key=industry_key,
            business_description=business_description,
            hiring_employees=hiring_employees,
            high_revenue=high_revenue,
        )
    if guide is None:
        st.stop()

    # Persist results so they survive reruns (e.g. when chatting)
    st.session_state["guide_result"] = {
        "text": guide,
        "unverified": find_unverified_amounts(
            guide, reference_text_for_guide(structure_key, industry_key)
        ),
        "structure_key": structure_key,
        "industry_key": industry_key,
        "structure_display": structure_display,
        "industry_display": industry_display,
    }
    st.session_state["guide_chat"] = []  # fresh conversation for the new guide

result = st.session_state.get("guide_result")
if result:
    structure_data = get_structure_data(result["structure_key"])
    licensing_data = get_licensing_data(result["industry_key"])

    st.divider()
    st.subheader(f"{result['structure_display']} · {result['industry_display']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Registration Fee", f"${structure_data.get('registration_fee', 0):,}")
    m2.metric(
        "Separate Legal Entity",
        "Yes" if structure_data.get("separate_legal_entity") else "No",
    )
    num_licenses = len([l for l in licensing_data.get("licenses", []) if l.get("estimated_cost", 0) > 0])
    m3.metric("Industry Licences", f"{num_licenses}")

    tab_guide, tab_docs, tab_links = st.tabs(
        ["🧭 Your guide", "📄 Documents checklist", "🔗 Official resources"]
    )

    with tab_guide:
        show_verification_warning(result.get("unverified"))
        sections = parse_steps(result["text"], STEP_TITLES)
        if not sections:
            st.write(result["text"])
        for i, (title, text) in enumerate(sections):
            with st.expander(f"{i + 1}. {title}", expanded=(i < 2)):
                st.write(text)

    with tab_docs:
        docs = structure_data.get("documents_needed", [])
        if docs:
            st.caption("Tick items off as you prepare them.")
            for doc in docs:
                st.checkbox(doc, key=f"doc_{result['structure_key']}_{doc}")
        else:
            st.info("No document list is available for this structure.")

    with tab_links:
        st.markdown("""
- **ACRA Bizfile+**: [www.bizfile.gov.sg](https://www.bizfile.gov.sg) — Register your business online
- **GoBusiness**: [www.gobusiness.gov.sg](https://www.gobusiness.gov.sg) — Find licences, permits and grants
- **IRAS**: [www.iras.gov.sg](https://www.iras.gov.sg) — Tax registration and filing
- **MOM**: [www.mom.gov.sg](https://www.mom.gov.sg) — Employment regulations and work passes
- **CPF Board**: [www.cpf.gov.sg](https://www.cpf.gov.sg) — CPF contribution information
""")

    st.divider()
    render_chat(
        history_key="guide_chat",
        answer_fn=lambda q, ctx: handle_followup_question(
            question=q,
            context=ctx,
            structure_key=result["structure_key"],
            industry_key=result["industry_key"],
        ),
        base_context=result["text"][:2000],
        placeholder="e.g., What happens if I want to change my business structure later?",
    )
