import json
import html
import streamlit as st
import google.generativeai as genai

# Page configuration
st.set_page_config(
    page_title="AssumptionGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Exact required system prompt
SYSTEM_PROMPT = """You are an expert project risk analyst. Analyze the project description below and return ONLY valid JSON in this exact structure (no markdown, no extra text):

{
  "missing_assumptions": [
    {
      "assumption": "short statement",
      "impact": "High" | "Medium" | "Low",
      "evidence": "quote or reference from the text",
      "recommendation": "what the user should do or ask next"
    }
  ],
  "overlooked_constraints": [ same structure ],
  "important_questions": [
    {
      "question": "...",
      "impact": "High" | "Medium" | "Low",
      "why_it_matters": "..."
    }
  ]
}

Be specific, critical, and prioritize high-impact items. Generate 4-7 items total across all categories."""

# ── Sample project descriptions (realistic, domain-diverse) ────────────────────────
_SAMPLES = {
    "🏛️  Legal DocEditor — SaaS": """\
Project: Real-Time Collaborative Legal Document Platform
Team: 4 engineers, 1 designer, 1 PM | Timeline: 6 weeks to MVP

We are building a browser-based collaborative document editor aimed at law firms
with 10–500 attorneys. Clients will be able to:
- Upload contract drafts in PDF, DOCX, or scanned image format (up to 50 MB each)
- Edit documents simultaneously using cursor-tracked live collaboration (like Google Docs)
- Leave inline comments and version-controlled annotations
- Digitally sign agreements with a "Sign Now" button
- Search across all firm documents with full-text search

Tech stack: React frontend, FastAPI backend, PostgreSQL for metadata, S3 for document
storage, WebSockets for real-time sync. Hosted on AWS us-east-1.

We plan to charge $29/seat/month. Target launch in North America and the EU simultaneously.
User authentication will use Auth0 with SSO for enterprise clients.
""",
    "🛒  Marketplace — B2C e-commerce": """\
Project: Hyperlocal Grocery Delivery Marketplace
Team: 6 engineers | Timeline: 3 months to public beta

We are building a two-sided marketplace connecting independent grocery stores with
consumers who want same-day delivery within a 5-mile radius. Key features:
- Consumers browse store inventory (synced every 15 minutes from store POS systems)
- Add items to cart, checkout via Stripe, and track delivery in real-time on a map
- Stores receive orders on a tablet app and prepare them within a 30-minute SLA
- Gig-economy drivers pick up orders and are paid per delivery + tip
- Consumers can schedule deliveries up to 3 days in advance

Stack: Next.js PWA, Node.js microservices, MongoDB, Redis for cart/session,
Google Maps API, Firebase for push notifications.

We expect 500 orders/day at launch scaling to 10,000/day within 6 months.
Initially launching in 2 cities; drivers are independent contractors (1099).
""",
    "🤖  AI Copilot — B2B SaaS": """\
Project: AI Customer Support Copilot for SaaS Companies
Team: 3 engineers, 1 AI/ML engineer | Timeline: 8 weeks

We are building an AI-powered copilot that sits inside support agents\u2019 existing
Help Desk tools (Zendesk, Freshdesk) and helps them respond to tickets faster.
The system will:
- Ingest a company\u2019s historical ticket data, knowledge base articles, and product
  documentation via API or file upload
- Suggest AI-drafted replies to incoming tickets in real-time (< 2 seconds)
- Auto-tag and prioritize tickets by sentiment and urgency
- Flag tickets that should be escalated to engineering
- Provide a weekly analytics dashboard showing CSAT, resolution time, and deflection

Our AI layer uses GPT-4o via OpenAI API. Vector search on embeddings stored in
Pinecone. We\u2019ll offer a freemium plan (up to 200 tickets/month) and Pro at $299/month.

Companies will connect their Zendesk via OAuth. Their ticket data will be stored and
used to fine-tune a per-customer retrieval model. GDPR compliance required.
""",
}

# ── CSS Design System ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ─── Typography & Base ─────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2px;
    }
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.03em;
        margin: 0;
        line-height: 1.15;
    }
    .app-subtitle {
        font-size: 0.98rem;
        color: #64748b;
        margin-bottom: 1.5rem;
        margin-top: 2px;
        letter-spacing: 0.01em;
    }

    /* ─── Impact Badges ─────────────────────── */
    .impact-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .badge-high   { background: #fff1f2; color: #be123c; border: 1.5px solid #fca5a5; }
    .badge-medium { background: #fffbeb; color: #92400e; border: 1.5px solid #fcd34d; }
    .badge-low    { background: #f0fdf4; color: #166534; border: 1.5px solid #86efac; }
    .badge-default{ background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; }

    /* ─── Summary Banner ────────────────────── */
    .summary-banner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 1.4rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .summary-label {
        font-size: 0.88rem;
        font-weight: 500;
        color: #64748b;
        margin-right: auto;
    }
    .summary-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 9999px;
        white-space: nowrap;
    }
    .pill-total  { background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }
    .pill-high   { background: #fff1f2; color: #be123c; border: 1px solid #fca5a5; }
    .pill-medium { background: #fffbeb; color: #92400e; border: 1px solid #fcd34d; }
    .pill-low    { background: #f0fdf4; color: #166534; border: 1px solid #86efac; }

    /* ─── Section Headers ───────────────────── */
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 0 0.55rem 0;
        border-bottom: 2px solid #f1f5f9;
        margin-bottom: 1rem;
        margin-top: 0.5rem;
    }
    .section-header-left {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-icon { font-size: 1.15rem; line-height: 1; }
    .section-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.01em;
    }
    .section-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #e2e8f0;
        color: #475569;
        font-size: 0.72rem;
        font-weight: 700;
        border-radius: 9999px;
        padding: 2px 8px;
        letter-spacing: 0.03em;
    }
    .section-desc {
        font-size: 0.82rem;
        color: #94a3b8;
        font-weight: 400;
    }

    /* ─── Analysis Cards ────────────────────── */
    .analysis-card {
        background: #ffffff;
        border: 1px solid #e9eef5;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04), 0 1px 2px rgba(15,23,42,0.03);
        transition: box-shadow 0.18s ease;
    }
    .analysis-card:hover {
        box-shadow: 0 4px 12px rgba(15,23,42,0.08);
        border-color: #c7d4e5;
    }
    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 0.7rem;
    }
    .card-title {
        font-size: 0.97rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.5;
        flex: 1;
    }
    .card-divider {
        height: 1px;
        background: #f1f5f9;
        margin: 0.55rem 0;
    }
    .card-detail-row {
        display: flex;
        gap: 8px;
        align-items: flex-start;
        margin-top: 0.5rem;
        font-size: 0.86rem;
        line-height: 1.5;
    }
    .detail-icon { flex-shrink: 0; margin-top: 1px; }
    .detail-label {
        font-weight: 600;
        margin-right: 4px;
        color: #475569;
    }
    .detail-text-evidence { color: #334155; font-style: italic; }
    .detail-text-rec      { color: #166534; }
    .detail-text-why      { color: #1d4ed8; }
    .detail-bg-evidence {
        background: #f8fafc;
        border-left: 3px solid #94a3b8;
        border-radius: 0 6px 6px 0;
        padding: 6px 10px;
    }
    .detail-bg-rec {
        background: #f0fdf4;
        border-left: 3px solid #4ade80;
        border-radius: 0 6px 6px 0;
        padding: 6px 10px;
    }
    .detail-bg-why {
        background: #eff6ff;
        border-left: 3px solid #60a5fa;
        border-radius: 0 6px 6px 0;
        padding: 6px 10px;
    }

    /* ─── Empty State ───────────────────────── */
    .empty-state {
        background: #f8fafc;
        border: 1.5px dashed #cbd5e1;
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
    }
    .empty-state-icon { font-size: 2.5rem; margin-bottom: 0.6rem; display: block; }
    .empty-state-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.4rem;
    }
    .empty-state-body {
        font-size: 0.9rem;
        color: #64748b;
        max-width: 440px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* ─── Section Empty ─────────────────────── */
    .section-empty {
        background: #f8fafc;
        border: 1px dashed #e2e8f0;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        color: #94a3b8;
        font-size: 0.88rem;
        text-align: center;
        margin-bottom: 0.85rem;
    }

    /* ─── Section Spacer ────────────────────── */
    .section-spacer { height: 1.4rem; }

    /* ─── Action Bar ────────────────────────── */
    .action-note {
        font-size: 0.82rem;
        color: #94a3b8;
        padding-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_api_key() -> str | None:
    """Read the Gemini API key exclusively from Streamlit secrets."""
    try:
        for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if key_name in st.secrets:
                val = st.secrets[key_name]
                if val and str(val).strip():
                    return str(val).strip()
    except Exception:
        pass
    return None


def parse_gemini_json_response(raw_text: str) -> dict:
    """
    Safely parse JSON response from Gemini.
    Strips markdown code fences, leading/trailing commentary, and validates structure.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Received an empty response from Gemini.")

    cleaned = raw_text.strip()

    # Strip markdown backticks if response is wrapped in ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Attempt direct JSON deserialization
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: locate the first '{' and last '}'
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            sub = cleaned[start_idx : end_idx + 1]
            try:
                data = json.loads(sub)
            except json.JSONDecodeError as err:
                raise ValueError(f"Could not parse extracted JSON substring: {err}")
        else:
            raise ValueError("No valid JSON object could be found in the model output.")

    if not isinstance(data, dict):
        raise ValueError("Model response did not evaluate to a JSON object.")

    # Validate or normalize the three required sections
    expected_keys = ["missing_assumptions", "overlooked_constraints", "important_questions"]
    for k in expected_keys:
        if k not in data or not isinstance(data[k], list):
            data[k] = []

    return data


def render_impact_badge(impact: str) -> str:
    """Generate color-coded pill badge HTML: High=red, Medium=amber, Low=green."""
    val = str(impact).strip().capitalize()
    if val == "High":
        return '<span class="impact-badge badge-high">&#9679; High</span>'
    elif val == "Medium":
        return '<span class="impact-badge badge-medium">&#9679; Medium</span>'
    elif val == "Low":
        return '<span class="impact-badge badge-low">&#9679; Low</span>'
    return f'<span class="impact-badge badge-default">&#9675; {html.escape(val)}</span>'


def render_card(
    title: str,
    impact: str,
    evidence: str = "",
    recommendation: str = "",
    why_it_matters: str = "",
) -> None:
    """Render a polished card with title, impact badge, evidence, and recommendation/why-it-matters."""
    safe_title = html.escape(str(title).strip())
    safe_evidence = html.escape(str(evidence).strip()) if evidence else ""
    safe_rec = html.escape(str(recommendation).strip()) if recommendation else ""
    safe_why = html.escape(str(why_it_matters).strip()) if why_it_matters else ""

    badge_html = render_impact_badge(impact)

    details_html = ""
    if safe_evidence:
        details_html += (
            f'<div class="card-divider"></div>'
            f'<div class="card-detail-row">'
            f'  <span class="detail-icon">📌</span>'
            f'  <div class="detail-bg-evidence" style="flex:1">'
            f'    <span class="detail-label">Evidence</span>'
            f'    <span class="detail-text-evidence">&ldquo;{safe_evidence}&rdquo;</span>'
            f'  </div>'
            f'</div>'
        )
    if safe_rec:
        details_html += (
            f'<div class="card-detail-row">'
            f'  <span class="detail-icon">💡</span>'
            f'  <div class="detail-bg-rec" style="flex:1">'
            f'    <span class="detail-label">Recommendation</span>'
            f'    <span class="detail-text-rec">{safe_rec}</span>'
            f'  </div>'
            f'</div>'
        )
    if safe_why:
        details_html += (
            f'<div class="card-detail-row">'
            f'  <span class="detail-icon">🎯</span>'
            f'  <div class="detail-bg-why" style="flex:1">'
            f'    <span class="detail-label">Why it matters</span>'
            f'    <span class="detail-text-why">{safe_why}</span>'
            f'  </div>'
            f'</div>'
        )

    card_html = f"""
    <div class="analysis-card">
        <div class="card-top">
            <div class="card-title">{safe_title}</div>
            {badge_html}
        </div>
        {details_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ---------------- Sidebar Configuration ----------------
current_key = get_api_key()

with st.sidebar:
    st.image(
        "https://api.iconify.design/material-symbols:shield-lock-outline.svg?color=%232563eb",
        width=46,
    )
    st.title("Settings")

    selected_model = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-2.5-pro"],
        index=0,
        help="Choose the Gemini model to use for analysis.",
    )

    st.markdown(
        """
        ---
        **About AssumptionGuard**  
        Surfaces silent assumptions, overlooked constraints, and critical stakeholder questions before writing code.
        """
    )


# ---------------- Main Page ----------------
st.markdown(
    '<div class="app-header">'
    '<div class="app-title">🛡️ AssumptionGuard</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Surface hidden assumptions, overlooked constraints, and critical questions before you build.</div>',
    unsafe_allow_html=True,
)

# Two-column layout for input and file uploader
col_input, col_options = st.columns([3, 1])

# ── Resolve uploaded file content BEFORE rendering the text area ────────────────
with col_options:
    st.markdown("#### \U0001f4c1 File Input")
    uploaded_file = st.file_uploader(
        "Upload spec (.txt or .md)",
        type=["txt", "md"],
        help="Upload any plain-text specification, README, or notes file. Its content will be placed directly into the text area below.",
        key="file_uploader",
    )

    if uploaded_file is not None:
        # Only re-read when a new file is uploaded (track by name+size)
        file_fingerprint = f"{uploaded_file.name}::{uploaded_file.size}"
        if st.session_state.get("_last_file_fingerprint") != file_fingerprint:
            try:
                raw_bytes = uploaded_file.read()
                # Try UTF-8 first, fall back to latin-1 for legacy files
                try:
                    file_content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    file_content = raw_bytes.decode("latin-1")

                # Push into session state so the text area picks it up
                st.session_state["spec_input_area"] = file_content
                st.session_state["_last_file_fingerprint"] = file_fingerprint
                st.session_state["_loaded_filename"] = uploaded_file.name
            except Exception as e:
                st.error(f"\u274c Could not read file: {e}")

        # Show file info badge
        loaded_name = st.session_state.get("_loaded_filename", uploaded_file.name)
        char_count  = len(st.session_state.get("spec_input_area", ""))
        word_count  = len(st.session_state.get("spec_input_area", "").split())
        st.markdown(
            f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:7px;
                        padding:8px 11px; margin-top:4px; font-size:0.83rem; line-height:1.5;">
                <strong style="color:#166534;">\u2714\ufe0f Loaded</strong>
                <code style="font-size:0.8rem;">{html.escape(loaded_name)}</code><br>
                <span style="color:#475569;">{char_count:,} chars &middot; {word_count:,} words</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Button to clear the loaded file
        if st.button("\u2715 Clear file", use_container_width=True, key="clear_file_btn"):
            st.session_state["spec_input_area"] = ""
            st.session_state.pop("_last_file_fingerprint", None)
            st.session_state.pop("_loaded_filename", None)
            st.rerun()
    else:
        # Clear fingerprint when file is removed via the widget's own X button
        if st.session_state.get("_last_file_fingerprint"):
            st.session_state.pop("_last_file_fingerprint", None)
            st.session_state.pop("_loaded_filename", None)
            # Do NOT clear the text area — let the user keep the text if they want

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Sample picker ────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.83rem; font-weight:600; color:#334155; "
        "margin-bottom:4px;'>\U0001f9ea Try a sample</div>",
        unsafe_allow_html=True,
    )
    chosen_sample = st.selectbox(
        "Sample scenario",
        options=list(_SAMPLES.keys()),
        index=0,
        label_visibility="collapsed",
        key="sample_picker",
    )
    if st.button("\u25b6\ufe0f Load Sample", use_container_width=True, key="load_sample_btn"):
        st.session_state["spec_input_area"] = _SAMPLES[chosen_sample].strip()
        st.session_state["_active_sample"] = chosen_sample
        st.session_state.pop("_last_file_fingerprint", None)
        st.session_state.pop("_loaded_filename", None)
        st.rerun()

    st.markdown(
        "<div style='font-size:0.78rem; color:#94a3b8; margin-top:0.6rem;'>Accepted files: .txt &middot; .md</div>",
        unsafe_allow_html=True,
    )

# ── Text area (always reads from session_state via key) ─────────────────────
with col_input:
    # Header row: title + active-sample pill
    active_sample = st.session_state.get("_active_sample", "")
    active_file   = st.session_state.get("_loaded_filename", "")
    if active_sample:
        source_pill = (
            f"<span style='font-size:0.75rem; font-weight:600; background:#eff6ff; "
            f"color:#1d4ed8; border:1px solid #bfdbfe; border-radius:9999px; "
            f"padding:2px 9px; margin-left:8px; white-space:nowrap;'>"
            f"\U0001f9ea Sample: {html.escape(active_sample.split('\u2014')[0].strip())}"
            f"</span>"
        )
    elif active_file:
        source_pill = (
            f"<span style='font-size:0.75rem; font-weight:600; background:#f0fdf4; "
            f"color:#166534; border:1px solid #bbf7d0; border-radius:9999px; "
            f"padding:2px 9px; margin-left:8px; white-space:nowrap;'>"
            f"\U0001f4c4 {html.escape(active_file)}"
            f"</span>"
        )
    else:
        source_pill = ""

    st.markdown(
        f"<div style='display:flex; align-items:center; margin-bottom:6px;'>"
        f"<span style='font-size:1.05rem; font-weight:700; color:#1e293b;'>\U0001f4dd Project Description</span>"
        f"{source_pill}"
        f"</div>",
        unsafe_allow_html=True,
    )

    project_description = st.text_area(
        label="Project description",
        label_visibility="collapsed",
        height=280,
        placeholder=(
            "Paste your project overview, user stories, architecture notes, or requirements here.\n\n"
            "Or pick a sample scenario on the right and click \u25b6\ufe0f Load Sample to try instantly."
        ),
        key="spec_input_area",
    )

    # Character counter below text area
    char_count = len(project_description)
    word_count = len(project_description.split()) if project_description.strip() else 0
    counter_color = "#94a3b8" if char_count < 50 else "#64748b"
    st.markdown(
        f"<div style='font-size:0.76rem; color:{counter_color}; text-align:right; margin-top:-8px;'>"
        f"{char_count:,} characters &middot; {word_count:,} words"
        f"</div>",
        unsafe_allow_html=True,
    )

# Action bar — Analyze + Clear side by side
col_btn, col_clear_btn, col_status = st.columns([2, 1, 3])
with col_btn:
    analyze_clicked = st.button("🚀 Analyze Project", type="primary", use_container_width=True)
with col_clear_btn:
    has_results = bool(st.session_state.get("analysis_data"))
    if st.button(
        "🗑️ Clear",
        use_container_width=True,
        disabled=not has_results,
        help="Clear current analysis results",
    ):
        for key in ["analysis_data", "raw_response", "analyzed_model"]:
            st.session_state.pop(key, None)
        st.rerun()
with col_status:
    if has_results:
        analyzed_model = st.session_state.get("analyzed_model", selected_model)
        st.markdown(
            f'<div class="action-note">Last run with <strong>{analyzed_model}</strong></div>',
            unsafe_allow_html=True,
        )

# ---------------- Execution Logic ----------------
# Text to analyze is whatever is now in the text area (typed, pasted, or file-loaded)
text_to_analyze = project_description.strip()

if analyze_clicked:
    if not text_to_analyze:
        st.warning("⚠️ Please provide a project description or upload a .txt / .md file to analyze.")
    elif not current_key:
        st.error(
            "🔑 API key not configured. Please contact the administrator."
        )
    else:
        with st.spinner("Analyzing project assumptions & constraints with Gemini..."):
            try:
                # Configure API key
                genai.configure(api_key=current_key)

                # Initialize model with required system prompt and JSON enforcement
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.2,
                    },
                )

                user_prompt = f"Project description to analyze:\n\n{text_to_analyze}"
                response = model.generate_content(user_prompt)

                raw_text = response.text if hasattr(response, "text") else ""
                parsed_data = parse_gemini_json_response(raw_text)

                # Persist in session state
                st.session_state["analysis_data"] = parsed_data
                st.session_state["raw_response"] = raw_text
                st.session_state["analyzed_model"] = selected_model
                st.success("Analysis complete!")

            except Exception as e:
                err_str = str(e)
                # Specific error handling for quota and permissions
                if "ResourceExhausted" in err_str or "429" in err_str or "quota" in err_str.lower():
                    st.error(
                        "⚠️ **API Quota Exceeded**: You have reached the rate limit or quota limit for your Gemini API key. Please wait a minute and retry, or use a key with higher quota limits."
                    )
                elif "InvalidArgument" in err_str or "API_KEY_INVALID" in err_str or "PermissionDenied" in err_str or "403" in err_str:
                    st.error(
                        "⚠️ **Authentication/Permission Error**: The provided Gemini API key is invalid or lacks permission for this model. Please verify your API key."
                    )
                elif isinstance(e, ValueError):
                    st.error(f"⚠️ **JSON Format Error**: {err_str}")
                    if "raw_text" in locals() and raw_text:
                        with st.expander("Show Raw Gemini Response"):
                            st.code(raw_text, language="text")
                else:
                    st.error(f"⚠️ **Unexpected Error**: {err_str}")

st.divider()

# ---------------- Results Display ────────────────────────────────────────────
st.markdown("### 📊 Analysis Results")

analysis_data = st.session_state.get("analysis_data", None)

if not analysis_data:
    st.markdown(
        """
        <div class="empty-state">
            <span class="empty-state-icon">🔎</span>
            <div class="empty-state-title">No analysis generated yet</div>
            <div class="empty-state-body">
                Paste your project spec in the text area above — or upload a <code>.txt</code> / <code>.md</code> file —
                then click <strong>Analyze Project</strong> to uncover hidden assumptions,
                overlooked constraints, and must-ask stakeholder questions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    missing_assumptions   = analysis_data.get("missing_assumptions", [])
    overlooked_constraints = analysis_data.get("overlooked_constraints", [])
    important_questions    = analysis_data.get("important_questions", [])

    all_items   = missing_assumptions + overlooked_constraints + important_questions
    total_count = len(all_items)
    high_count  = sum(1 for i in all_items if str(i.get("impact", "")).strip().capitalize() == "High")
    med_count   = sum(1 for i in all_items if str(i.get("impact", "")).strip().capitalize() == "Medium")
    low_count   = sum(1 for i in all_items if str(i.get("impact", "")).strip().capitalize() == "Low")

    # ── Summary Banner ──────────────────────────────────────────────────────
    high_plural   = "finding" if high_count   == 1 else "findings"
    med_plural    = "finding" if med_count    == 1 else "findings"
    low_plural    = "finding" if low_count    == 1 else "findings"
    total_plural  = "item"    if total_count  == 1 else "items"

    summary_parts = []
    if high_count:
        summary_parts.append(f"<strong style='color:#be123c'>{high_count} High impact</strong>")
    if med_count:
        summary_parts.append(f"<strong style='color:#92400e'>{med_count} Medium impact</strong>")
    if low_count:
        summary_parts.append(f"<strong style='color:#166534'>{low_count} Low impact</strong>")
    findings_sentence = " · ".join(summary_parts) if summary_parts else "No findings"

    st.markdown(
        f"""
        <div class="summary-banner">
            <span class="summary-label">&#128269; Gemini found <strong>{total_count} {total_plural}</strong> across 3 categories &mdash;</span>
            <span class="summary-pill pill-high">&#9679; {high_count} High</span>
            <span class="summary-pill pill-medium">&#9679; {med_count} Medium</span>
            <span class="summary-pill pill-low">&#9679; {low_count} Low</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Section 1 : Missing Assumptions ─────────────────────────────────────
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-header-left">
                <span class="section-icon">🔍</span>
                <span class="section-name">Missing Assumptions</span>
                <span class="section-count">{len(missing_assumptions)}</span>
            </div>
            <span class="section-desc">Unstated beliefs about users, data, infrastructure, or behaviour</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not missing_assumptions:
        st.markdown(
            '<div class="section-empty">&#10003;&nbsp; No missing assumptions flagged for this spec.</div>',
            unsafe_allow_html=True,
        )
    else:
        for item in missing_assumptions:
            render_card(
                title=item.get("assumption") or item.get("title") or "Unnamed Assumption",
                impact=item.get("impact", "Medium"),
                evidence=item.get("evidence", ""),
                recommendation=item.get("recommendation", ""),
            )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # ── Section 2 : Overlooked Constraints ──────────────────────────────────
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-header-left">
                <span class="section-icon">⛓️</span>
                <span class="section-name">Overlooked Constraints</span>
                <span class="section-count">{len(overlooked_constraints)}</span>
            </div>
            <span class="section-desc">Regulatory, performance, and architectural boundaries</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not overlooked_constraints:
        st.markdown(
            '<div class="section-empty">&#10003;&nbsp; No overlooked constraints flagged for this spec.</div>',
            unsafe_allow_html=True,
        )
    else:
        for item in overlooked_constraints:
            render_card(
                title=item.get("constraint") or item.get("assumption") or item.get("title") or "Unnamed Constraint",
                impact=item.get("impact", "Medium"),
                evidence=item.get("evidence", ""),
                recommendation=item.get("recommendation", ""),
            )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # ── Section 3 : Important Questions ─────────────────────────────────────
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-header-left">
                <span class="section-icon">❓</span>
                <span class="section-name">Important Questions</span>
                <span class="section-count">{len(important_questions)}</span>
            </div>
            <span class="section-desc">Must-ask questions for stakeholders, clients, and architects</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not important_questions:
        st.markdown(
            '<div class="section-empty">&#10003;&nbsp; No important questions generated for this spec.</div>',
            unsafe_allow_html=True,
        )
    else:
        for item in important_questions:
            render_card(
                title=item.get("question") or item.get("title") or "Unnamed Question",
                impact=item.get("impact", "Medium"),
                evidence=item.get("evidence", ""),
                recommendation=item.get("recommendation", ""),
                why_it_matters=item.get("why_it_matters", ""),
            )

    # ── Export Row ───────────────────────────────────────────────────────────
    st.divider()
    col_dl, col_raw = st.columns([2, 3])
    with col_dl:
        st.download_button(
            label="📥 Download JSON Report",
            data=json.dumps(analysis_data, indent=2),
            file_name="assumption_guard_analysis.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_raw:
        with st.expander("🔍 View Raw JSON Response"):
            st.json(analysis_data)
