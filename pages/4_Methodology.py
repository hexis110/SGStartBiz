import streamlit as st
from helper_functions.utility import check_password

st.set_page_config(
    layout="wide",
    page_title="Methodology"
)

if not check_password():
    st.stop()

st.title("Methodology")
st.markdown("This page explains the technical approach, data flows, and implementation details of SGStartBiz.")

st.markdown("---")

# --- Overall Approach ---
st.header("Overall Approach")
st.markdown("""
SGStartBiz uses a **hybrid approach** combining structured data (context injection) with
LLM-powered natural language generation:

1. **Structured Data (Primary):** Curated knowledge from official government sources is stored
   in JSON files. This data is used for factual lookups, cost computations, and as context
   injected into LLM prompts.

2. **LLM Generation (Secondary):** OpenAI's GPT-4o-mini is used to generate personalised
   explanations, step-by-step guides, and answers to follow-up questions. The LLM receives
   the curated data as context and is instructed to only use the provided information.

3. **Algorithmic Computation:** All numerical calculations (costs, taxes, CPF contributions)
   are performed by Python code — the LLM is never asked to generate or calculate numbers.
""")

# --- Use Case 1 Flowchart ---
st.header("Use Case 1: Business Registration Guide")

st.subheader("Data Flow")
st.markdown("""
1. **User Input** — User selects business structure, industry, and describes business activities
2. **Safety Check** — Free-text input is checked for prompt injection (few-shot LLM classifier)
   and content moderation (OpenAI Moderation API)
3. **Data Assembly** — Relevant data is loaded from JSON files based on user selections
4. **Prompt Construction** — System message is built with curated data enclosed in XML-style
   delimiter tags, along with the user's profile information
5. **LLM Generation** — GPT-4o-mini generates a personalised guide using prompt chaining with
   step delimiters (####)
6. **Response Parsing** — The response is split on delimiters and displayed in expandable sections
7. **Follow-up Q&A** — User can ask additional questions; context from the guide is maintained
   in session state and passed to subsequent LLM calls
""")

st.subheader("Flowchart — Use Case 1")

st.markdown("""
```
┌──────────────────────┐
│     User Inputs      │
│ (Structure, Industry,│
│  Business Activities)│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐     ┌────────────────────┐
│   Safety Checks      │────►│  Block & Show Error │
│ (Prompt Injection +  │ NO  │                    │
│  Content Moderation) │     └────────────────────┘
└──────────┬───────────┘
           │ PASS
           ▼
┌──────────────────────┐
│   Load JSON Data     │
│ (business_structures │
│  + licensing_info)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Build System Message│
│ (Context Injection   │
│  with XML delimiters)│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LLM Generation      │
│ (GPT-4o-mini with    │
│  #### step delimiters│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Parse & Display     │
│ (Split on ####,      │
│  show in expanders)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Follow-up Q&A       │
│ (Session state +     │
│  context injection)  │
└──────────────────────┘
```
""")

# --- Use Case 2 Flowchart ---
st.header("Use Case 2: Startup Cost Estimator")

st.subheader("Data Flow")
st.markdown("""
1. **User Input** — User provides business structure, industry, employee counts, salary, and revenue
2. **Safety Check** — Any free-text input is validated (same safety pipeline as UC1)
3. **Algorithmic Computation** — Python code computes all costs using data from JSON files:
   - Registration fee from `business_structures.json`
   - Licensing costs from `licensing_info.json`
   - CPF employer contributions from `cpf_info.json`
   - Corporate tax (with startup exemption) from `tax_info.json`
   - GST determination based on revenue threshold
4. **Result Display** — Costs shown as metric cards, data table, and bar chart
5. **LLM Explanation** — The computed costs are injected as context into the system message;
   the LLM explains (but does not recalculate) the results using prompt chaining
6. **Follow-up Q&A** — Same mechanism as UC1
""")

st.subheader("Flowchart — Use Case 2")

st.markdown("""
```
┌──────────────────────┐
│     User Inputs      │
│ (Structure, Industry,│
│  Employees, Salary,  │
│  Revenue)            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Algorithmic Cost    │
│  Computation         │
│  (Pure Python math)  │
│  ┌────────────────┐  │
│  │ Registration   │  │
│  │ Licensing      │  │
│  │ CPF            │  │
│  │ Corporate Tax  │  │
│  │ GST Check      │  │
│  └────────────────┘  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Display Results     │
│ (Metrics, Table,     │
│  Bar Chart)          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LLM Explanation     │
│ (Computed costs as   │
│  context injection;  │
│  LLM explains only)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Follow-up Q&A       │
│ (Session state +     │
│  context injection)  │
└──────────────────────┘
```
""")

# --- Safety Pipeline ---
st.header("Safety & Guardrails")
st.markdown("""
The application implements multiple safety layers:

| Layer | Method | Purpose |
|-------|--------|---------|
| Input Validation | Streamlit widgets (selectbox, number_input) | Constrain most inputs to valid choices |
| Prompt Injection Detection | Few-shot LLM classifier (Y/N) | Detect attempts to override system instructions |
| Content Moderation | OpenAI Moderation API | Flag harmful or inappropriate content |
| Output Guardrails | System message instructions | Instruct LLM to only use provided data |
| Output Verification | Python check of every `$` figure in the AI text against the app's data | Flag invented or mismatched amounts to the user |
| Error Handling | `try/except` around every API call, with timeouts and retries | Show a friendly message instead of a crash; cost figures still display if the AI is unavailable |
| Disclaimers | Required disclaimer on home page | Inform users this is an educational prototype |
""")

# --- Implementation Details ---
st.header("Implementation Details")
st.markdown("""
**Key Technical Decisions:**

- **Context Injection over RAG:** Given the relatively small and well-structured knowledge base,
  curated data is injected directly into LLM prompts rather than using a vector store. This
  provides more reliable and deterministic responses.

- **Algorithmic Cost Computation:** All financial calculations are performed by Python code
  using data from JSON files. The LLM is only used to explain the pre-computed results.
  This ensures numerical accuracy.

- **Prompt Chaining with Delimiters:** Following the course methodology, system messages use
  `####` delimiters to structure multi-step reasoning. The final step is extracted and displayed
  to the user.

- **Session State for Context:** Streamlit's `st.session_state` keeps the generated guide or
  estimate on screen and maintains a chat-style conversation history for follow-up questions.

- **Data-Driven Tax Rules:** Tax brackets, exemption rates, the GST threshold and the profit-margin
  assumption are read from `tax_info.json`, so they can be updated without changing code.

- **Automated Tests:** An offline test suite (`python -m unittest discover -s tests -t .`) checks the
  tax and cost calculations, the output-verification check, the safety pipeline (with the API
  mocked) and the integrity of the data files.
""")
