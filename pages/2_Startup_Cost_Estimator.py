import altair as alt
import pandas as pd
import streamlit as st
from helper_functions.ui import setup_page, safe_call, parse_steps, render_chat, show_verification_warning
from logics.business_query_handler import (
    compute_startup_costs,
    generate_cost_explanation,
    handle_followup_question,
    find_unverified_amounts,
    reference_text_for_costs,
)

setup_page("Cost Estimator", "💰")

st.title("💰 Startup Cost Estimator")
st.markdown("Estimate the costs involved in starting your business in Singapore.")
st.caption("For educational purposes only. Please verify all figures with official sources.")

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

STEP_TITLES = [
    "Cost Summary",
    "Cost Categories Explained",
    "Tax Benefits & Exemptions",
    "Practical Recommendations",
]

with st.form(key="cost_estimator_form"):
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

    col3, col4 = st.columns(2)
    with col3:
        num_local_employees = st.number_input(
            "Number of Local Employees", min_value=0, max_value=100, value=1,
            help="Singapore Citizens and Permanent Residents you plan to hire.",
        )
    with col4:
        num_foreign_employees = st.number_input(
            "Number of Foreign Employees", min_value=0, max_value=100, value=0,
            help="Foreign workers you plan to hire.",
        )

    col5, col6 = st.columns(2)
    with col5:
        avg_monthly_salary = st.number_input(
            "Average Monthly Salary per Employee ($)", min_value=0, max_value=50000,
            value=4000, step=500,
            help="Estimated average monthly salary for your employees.",
        )
    with col6:
        estimated_annual_revenue = st.number_input(
            "Estimated Annual Revenue ($)", min_value=0, max_value=50000000,
            value=200000, step=50000,
            help="Your expected annual revenue in the first year.",
        )

    submitted = st.form_submit_button(
        "Estimate my startup costs", type="primary", width="stretch"
    )

if submitted:
    structure_key = STRUCTURE_OPTIONS[structure_display]
    industry_key = INDUSTRY_OPTIONS[industry_display]

    # Costs are computed in plain Python (no LLM)
    costs = compute_startup_costs(
        structure_key=structure_key,
        industry_key=industry_key,
        num_local_employees=num_local_employees,
        num_foreign_employees=num_foreign_employees,
        avg_monthly_salary=avg_monthly_salary,
        estimated_annual_revenue=estimated_annual_revenue,
    )

    with st.spinner("Generating your cost analysis... this can take 10-20 seconds"):
        explanation = safe_call(
            generate_cost_explanation,
            costs=costs,
            structure_key=structure_key,
            industry_key=industry_key,
            num_local_employees=num_local_employees,
            num_foreign_employees=num_foreign_employees,
            avg_monthly_salary=avg_monthly_salary,
            estimated_annual_revenue=estimated_annual_revenue,
        )

    inputs = {
        "avg_monthly_salary": avg_monthly_salary,
        "num_local_employees": num_local_employees,
        "num_foreign_employees": num_foreign_employees,
        "estimated_annual_revenue": estimated_annual_revenue,
    }
    st.session_state["cost_result"] = {
        "costs": costs,
        "unverified": (
            find_unverified_amounts(explanation, reference_text_for_costs(costs, inputs))
            if explanation else []
        ),
        # The numbers still display if the AI explanation failed
        "explanation": explanation,
        "structure_key": structure_key,
        "industry_key": industry_key,
        "structure_display": structure_display,
        "industry_display": industry_display,
        "inputs": inputs,
    }
    st.session_state["cost_chat"] = []

result = st.session_state.get("cost_result")
if result:
    costs = result["costs"]
    inputs = result["inputs"]

    st.divider()
    st.subheader(f"{result['structure_display']} · {result['industry_display']}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total first-year", f"${costs['total_first_year']:,.0f}")
    m2.metric("One-time costs", f"${costs['total_one_time']:,.0f}")
    m3.metric("Annual recurring", f"${costs['total_annual_recurring']:,.0f}")
    m4.metric("GST registration", "Required" if costs["gst_required"] else "Not required")

    tab_chart, tab_table, tab_ai = st.tabs(
        ["📊 Cost distribution", "🧾 Breakdown table", "🤖 AI analysis"]
    )

    with tab_chart:
        chart_df = pd.DataFrame(
            {
                "Category": ["Registration", "Licensing", "CPF (annual)", "Corporate tax"],
                "Amount": [
                    costs["registration_fee"],
                    costs["licensing_total"],
                    costs["annual_cpf_employer"],
                    costs["corporate_tax"],
                ],
            }
        )
        chart_df = chart_df[chart_df["Amount"] > 0]
        if chart_df.empty:
            st.info("No costs to chart for these inputs.")
        else:
            total = chart_df["Amount"].sum()
            chart_df["Share"] = (chart_df["Amount"] / total * 100).round(1)
            base = alt.Chart(chart_df).encode(
                theta=alt.Theta("Amount:Q", stack=True),
                color=alt.Color("Category:N", legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    "Category",
                    alt.Tooltip("Amount:Q", format=",.0f", title="Amount ($)"),
                    alt.Tooltip("Share:Q", title="Share (%)"),
                ],
            )
            donut = base.mark_arc(innerRadius=70, outerRadius=130)
            st.altair_chart(donut, use_container_width=True)
            st.caption(f"Total of charted items: ${total:,.0f}. Hover a slice for details.")

    with tab_table:
        rows = [
            {
                "Category": "Registration fee",
                "Amount ($)": float(costs["registration_fee"]),
                "Frequency": "One-time",
                "Notes": costs["registration_fee_label"],
            }
        ]
        for lic in costs.get("license_details", []):
            rows.append(
                {
                    "Category": f"Licence: {lic['name']}",
                    "Amount ($)": float(lic["cost"]),
                    "Frequency": lic["renewal"],
                    "Notes": f"Issued by {lic['authority']}",
                }
            )
        if costs["annual_cpf_employer"] > 0:
            rows.append(
                {
                    "Category": "CPF (employer contribution)",
                    "Amount ($)": float(costs["annual_cpf_employer"]),
                    "Frequency": "Annual",
                    "Notes": (
                        f"{costs['cpf_employer_rate'] * 100:.0f}% x "
                        f"${inputs['avg_monthly_salary']:,} x "
                        f"{inputs['num_local_employees']} employees x 12 months"
                    ),
                }
            )
        if costs["corporate_tax"] > 0:
            rows.append(
                {
                    "Category": "Corporate tax (estimated)",
                    "Amount ($)": float(costs["corporate_tax"]),
                    "Frequency": "Annual",
                    "Notes": f"On estimated profit of ${costs['estimated_profit']:,.0f} (with startup exemption)",
                }
            )
        gst_note = (
            "Required"
            if costs["gst_required"]
            else f"Not required (revenue below ${costs['gst_threshold']:,} threshold)"
        )
        rows.append(
            {"Category": "GST registration", "Amount ($)": None, "Frequency": "Ongoing", "Notes": gst_note}
        )
        st.dataframe(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True,
            column_config={"Amount ($)": st.column_config.NumberColumn(format="$%,.2f")},
        )

    with tab_ai:
        if result["explanation"] is None:
            st.warning("The AI analysis is unavailable right now. Your figures above are still correct.")
        else:
            show_verification_warning(result.get("unverified"))
            sections = parse_steps(result["explanation"], STEP_TITLES)
            if not sections:
                st.write(result["explanation"])
            for i, (title, text) in enumerate(sections):
                with st.expander(f"{i + 1}. {title}", expanded=(i == 0)):
                    st.write(text)

    st.divider()
    render_chat(
        history_key="cost_chat",
        answer_fn=lambda q, ctx: handle_followup_question(
            question=q,
            context=ctx,
            structure_key=result["structure_key"],
            industry_key=result["industry_key"],
        ),
        base_context=(
            f"User estimated startup costs. Total first-year: ${costs['total_first_year']:,.2f}. "
            f"One-time: ${costs['total_one_time']:,.2f}. "
            f"Annual recurring: ${costs['total_annual_recurring']:,.2f}."
        ),
        placeholder="e.g., What other grants are available for startups?",
    )
