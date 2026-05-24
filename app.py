import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv
import json
import time
import os

load_dotenv()

from resume_parser import parse_resume, extract_contact_info
from ats_analyzer import (
    analyze_resume,
    generate_cover_letter,
    generate_interview_questions,
    rewrite_bullets,
    compare_resumes,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResumeIQ — AI Resume Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg:        #0a0a0f;
  --surface:   #111118;
  --surface2:  #1a1a24;
  --border:    #2a2a3a;
  --accent:    #00e5a0;
  --accent2:   #7c3aed;
  --accent3:   #f59e0b;
  --danger:    #ef4444;
  --text:      #e8e8f0;
  --muted:     #6b6b80;
  --card-glow: 0 0 0 1px var(--border), 0 8px 32px rgba(0,0,0,0.4);
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Remove sidebar toggle completely ── */
[data-testid="collapsedControl"],
button[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapseButton"] {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  width: 0 !important;
  height: 0 !important;
}

/* ── Sidebar collapse/expand toggle button ── */
/* The arrow button that appears on the edge of the sidebar */
button[data-testid="collapsedControl"],
[data-testid="collapsedControl"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 0 8px 8px 0 !important;
  color: var(--accent) !important;
  width: 1.6rem !important;
  height: 2.4rem !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  opacity: 1 !important;
  visibility: visible !important;
  box-shadow: 2px 0 12px rgba(0,0,0,0.4) !important;
}
button[data-testid="collapsedControl"]:hover,
[data-testid="collapsedControl"]:hover {
  background: var(--surface2) !important;
  border-color: var(--accent) !important;
  box-shadow: 2px 0 16px rgba(0,229,160,0.2) !important;
}
button[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] svg {
  fill: var(--accent) !important;
  color: var(--accent) !important;
}

/* Also ensure the in-sidebar close arrow is visible */
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapseButton"] button {
  color: var(--muted) !important;
  opacity: 1 !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
  color: var(--accent) !important;
  background: var(--surface2) !important;
}

/* App background */
.stApp {
  background: var(--bg) !important;
  background-image:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,229,160,0.06) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 90% 80%, rgba(124,58,237,0.05) 0%, transparent 60%) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem !important; }

/* Headings */
h1, h2, h3, h4 {
  font-family: 'Syne', sans-serif !important;
  color: var(--text) !important;
}

/* Score ring container */
.score-hero {
  background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  box-shadow: var(--card-glow);
  position: relative;
  overflow: hidden;
}
.score-hero::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at center, rgba(0,229,160,0.04) 0%, transparent 60%);
  pointer-events: none;
}

/* Grade badge */
.grade-badge {
  display: inline-block;
  font-family: 'Syne', sans-serif;
  font-size: 3.5rem;
  font-weight: 800;
  padding: 0.2em 0.5em;
  border-radius: 12px;
  line-height: 1;
}

/* Metric cards */
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.2rem 1.4rem;
  box-shadow: var(--card-glow);
  transition: border-color 0.2s, transform 0.2s;
}
.metric-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}
.metric-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-bottom: 0.3rem;
}
.metric-value {
  font-family: 'Syne', sans-serif;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--accent);
}

/* Tag pills */
.tag-pill {
  display: inline-block;
  font-family: 'DM Mono', monospace;
  font-size: 0.72rem;
  padding: 0.25em 0.75em;
  border-radius: 100px;
  margin: 0.2em;
  border: 1px solid;
}
.tag-green { background: rgba(0,229,160,0.08); border-color: rgba(0,229,160,0.3); color: #00e5a0; }
.tag-purple { background: rgba(124,58,237,0.08); border-color: rgba(124,58,237,0.3); color: #a78bfa; }
.tag-amber { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.3); color: #fbbf24; }
.tag-red { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.3); color: #f87171; }
.tag-blue { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.3); color: #93c5fd; }

/* Section headers */
.section-header {
  font-family: 'Syne', sans-serif;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--muted);
  padding: 0.4em 0;
  margin-bottom: 0.8rem;
  border-bottom: 1px solid var(--border);
}

/* Improvement cards */
.improvement-card {
  background: var(--surface);
  border-left: 3px solid;
  border-radius: 0 10px 10px 0;
  padding: 1rem 1.2rem;
  margin-bottom: 0.7rem;
  border-top: 1px solid var(--border);
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.imp-high { border-left-color: var(--danger); }
.imp-medium { border-left-color: var(--accent3); }
.imp-low { border-left-color: var(--accent); }

/* Strength cards */
.strength-card {
  background: rgba(0,229,160,0.04);
  border: 1px solid rgba(0,229,160,0.15);
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 0.6rem;
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
}

/* Cover letter / text output */
.output-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.6rem;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.92rem;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* Quick win cards */
.quickwin-card {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.8rem 1rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.88rem;
}

/* Red flag */
.redflag-card {
  background: rgba(239,68,68,0.05);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 10px;
  padding: 0.8rem 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.88rem;
  color: #fca5a5;
}

/* Interview Q cards */
.iq-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  margin-bottom: 0.6rem;
  font-size: 0.9rem;
  line-height: 1.6;
}

/* Comparison cards */
.compare-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.4rem;
  height: 100%;
}

/* Streamlit widget overrides */
.stTextArea textarea, .stTextInput input {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
}
.stSelectbox > div > div {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
}

/* File uploader */
.stFileUploader > div {
  background: var(--surface) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 14px !important;
}
.stFileUploader label { color: var(--muted) !important; }

/* Buttons */
.stButton > button {
  background: var(--accent) !important;
  color: #000 !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.04em !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 0.6rem 1.4rem !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: #00c988 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(0,229,160,0.3) !important;
}

/* Secondary button */
.stButton [data-baseweb="button"][kind="secondary"] {
  background: var(--surface2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-radius: 12px !important;
  padding: 4px !important;
  border: 1px solid var(--border) !important;
  gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  border-radius: 8px !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.04em !important;
}
.stTabs [aria-selected="true"] {
  background: var(--accent) !important;
  color: #000 !important;
}

/* Progress bars */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), #00c988) !important;
  border-radius: 100px !important;
}
.stProgress > div > div {
  background: var(--surface2) !important;
  border-radius: 100px !important;
}

/* Expanders */
.streamlit-expanderHeader {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}
.streamlit-expanderContent {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Alerts */
.stSuccess { background: rgba(0,229,160,0.08) !important; border-color: rgba(0,229,160,0.2) !important; color: #00e5a0 !important; }
.stWarning { background: rgba(245,158,11,0.08) !important; border-color: rgba(245,158,11,0.2) !important; }
.stError   { background: rgba(239,68,68,0.08) !important; border-color: rgba(239,68,68,0.2) !important; }
.stInfo    { background: rgba(59,130,246,0.08) !important; border-color: rgba(59,130,246,0.2) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def score_color(score: int) -> str:
    if score >= 80: return "#00e5a0"
    if score >= 60: return "#f59e0b"
    return "#ef4444"

def score_label(score: int) -> str:
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 55: return "Fair"
    return "Needs Work"

def grade_color(grade: str) -> str:
    mapping = {
        "A+": "#00e5a0", "A": "#00e5a0",
        "B+": "#34d399", "B": "#6ee7b7",
        "C+": "#f59e0b", "C": "#fbbf24",
        "D": "#f97316", "F": "#ef4444",
    }
    return mapping.get(grade, "#6b6b80")

def priority_class(p: str) -> str:
    return {"high": "imp-high", "medium": "imp-medium", "low": "imp-low"}.get(p.lower(), "imp-low")

def priority_label(p: str) -> str:
    return {"high": "🔴 HIGH", "medium": "🟡 MED", "low": "🟢 LOW"}.get(p.lower(), p)

def make_radar(breakdown: dict) -> go.Figure:
    cats = list(breakdown.keys())
    vals = list(breakdown.values())
    max_val = 25
    cats_display = [c.replace("_", " ").title() for c in cats]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=cats_display + [cats_display[0]],
        fill='toself',
        fillcolor='rgba(0,229,160,0.12)',
        line=dict(color='#00e5a0', width=2),
        name='Score',
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, max_val], tickfont=dict(color='#6b6b80', size=9), gridcolor='#2a2a3a', linecolor='#2a2a3a'),
            angularaxis=dict(tickfont=dict(color='#e8e8f0', size=11, family='Syne'), gridcolor='#2a2a3a', linecolor='#2a2a3a'),
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        height=280,
    )
    return fig

def make_gauge(score: int) -> go.Figure:
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'font': {'size': 48, 'color': color, 'family': 'Syne'}, 'suffix': ''},
        gauge={
            'axis': {'range': [0, 100], 'tickfont': {'color': '#6b6b80', 'size': 9}, 'tickcolor': '#2a2a3a'},
            'bar': {'color': color, 'thickness': 0.22},
            'bgcolor': '#1a1a24',
            'bordercolor': '#2a2a3a',
            'borderwidth': 1,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(239,68,68,0.06)'},
                {'range': [40, 70], 'color': 'rgba(245,158,11,0.06)'},
                {'range': [70, 100], 'color': 'rgba(0,229,160,0.06)'},
            ],
            'threshold': {'line': {'color': color, 'width': 2}, 'thickness': 0.75, 'value': score},
        },
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
    )
    return fig

def make_bar_breakdown(breakdown: dict) -> go.Figure:
    labels = [k.replace("_", " ").title() for k in breakdown.keys()]
    values = list(breakdown.values())
    colors = [score_color(int(v / 25 * 100)) for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation='h',
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{v}/25" for v in values],
        textposition='outside',
        textfont=dict(color='#e8e8f0', size=11, family='DM Mono'),
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[0, 30], showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(tickfont=dict(color='#e8e8f0', size=11, family='DM Sans'), gridcolor='#2a2a3a'),
        margin=dict(l=10, r=60, t=10, b=10),
        height=200,
        bargap=0.35,
    )
    return fig


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding-bottom:1rem'>
      <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#e8e8f0'>
        ⚡ ResumeIQ
      </div>
      <div style='font-family:DM Mono,monospace;font-size:0.65rem;color:#6b6b80;letter-spacing:0.1em;margin-top:2px'>
        AI-POWERED CAREER INTELLIGENCE
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["🎯 ATS Analyzer", "📝 Cover Letter", "🎤 Interview Prep", "✏️ Bullet Rewriter", "⚔️ Resume Compare"],
        label_visibility="hidden",
    )

    st.markdown('<div class="section-header" style="margin-top:1.5rem">Configuration</div>', unsafe_allow_html=True)
    jd_input = st.text_area(
        "Job Description",
        placeholder="Paste the job description here for tailored analysis...",
        height=160,
        help="Providing a JD improves accuracy significantly"
    )

    st.markdown('<div class="section-header" style="margin-top:1rem">Settings</div>', unsafe_allow_html=True)
    tone = st.selectbox("Cover Letter Tone", ["Professional", "Confident", "Creative", "Concise", "Enthusiastic"])
    show_raw = st.toggle("Show extracted text", value=False)

    st.markdown("""
    <div style='margin-top:2rem;padding:1rem;background:rgba(0,229,160,0.04);border:1px solid rgba(0,229,160,0.12);border-radius:10px'>
      <div style='font-family:DM Mono,monospace;font-size:0.65rem;color:#6b6b80;letter-spacing:0.1em;margin-bottom:0.5rem'>POWERED BY</div>
      <div style='font-family:Syne,sans-serif;font-size:0.85rem;font-weight:600;color:#a78bfa'>Groq · LLaMA 3.3 70B</div>
      <div style='font-family:DM Mono,monospace;font-size:0.6rem;color:#6b6b80;margin-top:2px'>100% FREE · NO BILLING</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ATS ANALYZER
# ══════════════════════════════════════════════════════════════════════════════
if page == "🎯 ATS Analyzer":
    st.markdown("""
    <div style='margin-bottom:2rem'>
      <h1 style='font-size:2.2rem;font-weight:800;margin-bottom:0.3rem'>
        ATS Resume Analyzer
      </h1>
      <p style='color:#6b6b80;font-size:0.92rem;margin:0'>
        Upload your resume for a full AI-powered ATS score, gap analysis, and career recommendations.
      </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop your resume here (PDF or DOCX)", type=["pdf", "docx"])

    if uploaded_file:
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            analyze_btn = st.button("⚡ Analyze Resume", use_container_width=True)

        if analyze_btn:
            with st.spinner("Parsing and analyzing..."):
                resume_text = parse_resume(uploaded_file)
                contact = extract_contact_info(resume_text)
                result = analyze_resume(resume_text, jd_input)
                st.session_state["result"] = result
                st.session_state["resume_text"] = resume_text
                st.session_state["contact"] = contact

    result = st.session_state.get("result")
    resume_text = st.session_state.get("resume_text", "")
    contact = st.session_state.get("contact", {})

    if result:
        score = result.get("ats_score", 0)
        grade = result.get("grade", "—")
        breakdown = result.get("score_breakdown", {})

        # ── Hero row ──────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns([1.2, 1.8, 1])

        with col1:
            gc = grade_color(grade)
            st.markdown(f"""
            <div class="score-hero">
              <div class="section-header">ATS SCORE</div>
              <div class="grade-badge" style="color:{gc};background:rgba(0,0,0,0.3);border:2px solid {gc}22">
                {grade}
              </div>
              <div style="font-family:DM Mono,monospace;font-size:2.8rem;font-weight:700;color:{score_color(score)};margin:0.5rem 0;line-height:1">
                {score}<span style="font-size:1.2rem;color:#6b6b80">/100</span>
              </div>
              <div style="font-family:Syne,sans-serif;font-size:0.8rem;color:{score_color(score)};font-weight:600;text-transform:uppercase;letter-spacing:0.1em">
                {score_label(score)}
              </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.plotly_chart(make_radar(breakdown), use_container_width=True, config={"displayModeBar": False})

        with col3:
            lvl = result.get("seniority_level", "—")
            yrs = result.get("experience_years", "—")
            sal = result.get("salary_range", {})
            sal_str = f"${sal.get('min', 0)//1000}k–${sal.get('max', 0)//1000}k" if sal else "—"

            for label, val, color in [
                ("SENIORITY", lvl, "#a78bfa"),
                ("EXP. YEARS", f"{yrs} yrs" if yrs else "—", "#00e5a0"),
                ("EST. SALARY", sal_str, "#f59e0b"),
            ]:
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom:0.6rem">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value" style="color:{color};font-size:1.3rem">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<hr/>", unsafe_allow_html=True)

        # ── Score bar chart ───────────────────────────────────────────────────
        st.markdown('<div class="section-header">Score Breakdown</div>', unsafe_allow_html=True)
        st.plotly_chart(make_bar_breakdown(breakdown), use_container_width=True, config={"displayModeBar": False})

        # ── Summary ───────────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.4rem;margin:0.8rem 0 1.4rem">
          <div class="section-header" style="margin-bottom:0.8rem">AI SUMMARY</div>
          <p style="color:var(--text);font-size:0.93rem;line-height:1.8;margin:0">{result.get('summary','')}</p>
        </div>
        """, unsafe_allow_html=True)

        # ── 3-col: Strengths | Improvements | Quick Wins ──────────────────────
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="section-header">✅ Strengths</div>', unsafe_allow_html=True)
            for s in result.get("strengths", []):
                st.markdown(f"""
                <div class="strength-card">
                  <span style="color:#00e5a0;font-size:1rem;margin-top:1px">◆</span>
                  <span style="font-size:0.87rem;line-height:1.5">{s}</span>
                </div>
                """, unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="section-header">🔧 Improvements</div>', unsafe_allow_html=True)
            for item in result.get("improvements", []):
                pc = priority_class(item.get("priority", "low"))
                pl = priority_label(item.get("priority", "low"))
                st.markdown(f"""
                <div class="improvement-card {pc}">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
                    <span style="font-family:DM Mono,monospace;font-size:0.65rem;font-weight:600">{pl}</span>
                    <span style="font-size:0.88rem;font-weight:600;color:var(--text)">{item.get('issue','')}</span>
                  </div>
                  <div style="font-size:0.82rem;color:#9898b0;line-height:1.5">{item.get('suggestion','')}</div>
                </div>
                """, unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="section-header">⚡ Quick Wins</div>', unsafe_allow_html=True)
            for i, qw in enumerate(result.get("quick_wins", []), 1):
                st.markdown(f"""
                <div class="quickwin-card">
                  <span style="font-family:Syne,sans-serif;font-weight:800;color:#00e5a0;font-size:1rem;min-width:24px">{i:02d}</span>
                  <span style="color:var(--text)">{qw}</span>
                </div>
                """, unsafe_allow_html=True)

            red_flags = result.get("red_flags", [])
            if red_flags:
                st.markdown('<div class="section-header" style="margin-top:1rem">🚨 Red Flags</div>', unsafe_allow_html=True)
                for rf in red_flags:
                    st.markdown(f'<div class="redflag-card">⚠ {rf}</div>', unsafe_allow_html=True)

        st.markdown("<hr/>", unsafe_allow_html=True)

        # ── Keywords + Skills + Roles ─────────────────────────────────────────
        k1, k2, k3 = st.columns(3)

        with k1:
            st.markdown('<div class="section-header">🏷️ Skills Detected</div>', unsafe_allow_html=True)
            tags_html = "".join(f'<span class="tag-pill tag-green">{s}</span>' for s in result.get("skills_found", []))
            st.markdown(f'<div style="line-height:2.2">{tags_html}</div>', unsafe_allow_html=True)

        with k2:
            st.markdown('<div class="section-header">❌ Missing Keywords</div>', unsafe_allow_html=True)
            tags_html = "".join(f'<span class="tag-pill tag-red">{k}</span>' for k in result.get("missing_keywords", []))
            st.markdown(f'<div style="line-height:2.2">{tags_html}</div>', unsafe_allow_html=True)

        with k3:
            st.markdown('<div class="section-header">🎯 Best-Fit Roles</div>', unsafe_allow_html=True)
            for role in result.get("top_roles", []):
                st.markdown(f'<span class="tag-pill tag-purple">{role}</span>', unsafe_allow_html=True)
            st.markdown('<div class="section-header" style="margin-top:1rem">🏢 Industry Fit</div>', unsafe_allow_html=True)
            for ind in result.get("industry_fit", []):
                st.markdown(f'<span class="tag-pill tag-blue">{ind}</span>', unsafe_allow_html=True)

        # ── Rewritten Summary + Certifications ───────────────────────────────
        st.markdown("<hr/>", unsafe_allow_html=True)
        r1, r2 = st.columns([2, 1])

        with r1:
            st.markdown('<div class="section-header">✍️ AI-Rewritten Summary</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="output-box" style="font-size:0.9rem">
{result.get('rewritten_summary', '')}
            </div>
            """, unsafe_allow_html=True)

        with r2:
            st.markdown('<div class="section-header">🏆 Recommended Certs</div>', unsafe_allow_html=True)
            for cert in result.get("certifications_recommended", []):
                st.markdown(f'<span class="tag-pill tag-amber">{cert}</span>', unsafe_allow_html=True)

            st.markdown('<div class="section-header" style="margin-top:1rem">📇 Contact Detected</div>', unsafe_allow_html=True)
            for k, v in contact.items():
                if v:
                    st.markdown(f"""
                    <div style="font-family:DM Mono,monospace;font-size:0.72rem;color:#9898b0;margin-bottom:0.3rem">
                      <span style="color:#6b6b80;text-transform:uppercase;letter-spacing:0.1em">{k}: </span>
                      <span style="color:#e8e8f0">{v}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Raw text toggle ───────────────────────────────────────────────────
        if show_raw and resume_text:
            with st.expander("📋 Extracted Resume Text"):
                st.text(resume_text)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: COVER LETTER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Cover Letter":
    st.markdown("""
    <div style='margin-bottom:2rem'>
      <h1 style='font-size:2.2rem;font-weight:800;margin-bottom:0.3rem'>Cover Letter Generator</h1>
      <p style='color:#6b6b80;font-size:0.92rem;margin:0'>Generate a tailored, compelling cover letter in seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"], key="cl_upload")

    if not jd_input.strip():
        st.info("💡 Tip: Add a Job Description in the sidebar for a highly tailored cover letter.")

    if uploaded_file:
        if st.button("✍️ Generate Cover Letter", use_container_width=False):
            with st.spinner("Crafting your cover letter..."):
                resume_text = parse_resume(uploaded_file)
                letter = generate_cover_letter(resume_text, jd_input, tone)
                st.session_state["cover_letter"] = letter

    if "cover_letter" in st.session_state:
        st.markdown('<div class="section-header">Generated Cover Letter</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="output-box">{st.session_state['cover_letter']}</div>
        """, unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download as .txt",
            st.session_state["cover_letter"],
            file_name="cover_letter.txt",
            mime="text/plain"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERVIEW PREP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎤 Interview Prep":
    st.markdown("""
    <div style='margin-bottom:2rem'>
      <h1 style='font-size:2.2rem;font-weight:800;margin-bottom:0.3rem'>Interview Prep Kit</h1>
      <p style='color:#6b6b80;font-size:0.92rem;margin:0'>AI-generated interview questions based on your resume and the role.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"], key="iq_upload")

    if uploaded_file:
        if st.button("🎤 Generate Interview Questions"):
            with st.spinner("Preparing your interview kit..."):
                resume_text = parse_resume(uploaded_file)
                iq = generate_interview_questions(resume_text, jd_input)
                st.session_state["interview_qs"] = iq

    if "interview_qs" in st.session_state:
        iq = st.session_state["interview_qs"]
        tabs = st.tabs(["🧠 Behavioral", "⚙️ Technical", "💡 Situational", "❓ Ask the Interviewer"])

        for tab, key, label in zip(
            tabs,
            ["behavioral", "technical", "situational", "questions_to_ask"],
            ["Behavioral Questions", "Technical Questions", "Situational Questions", "Questions to Ask"]
        ):
            with tab:
                st.markdown(f'<div class="section-header" style="margin-top:0.5rem">{label}</div>', unsafe_allow_html=True)
                for i, q in enumerate(iq.get(key, []), 1):
                    st.markdown(f"""
                    <div class="iq-card">
                      <span style="font-family:Syne,sans-serif;font-weight:700;color:#6b6b80;margin-right:0.6rem">Q{i}.</span>
                      {q}
                    </div>
                    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BULLET REWRITER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✏️ Bullet Rewriter":
    st.markdown("""
    <div style='margin-bottom:2rem'>
      <h1 style='font-size:2.2rem;font-weight:800;margin-bottom:0.3rem'>Bullet Point Rewriter</h1>
      <p style='color:#6b6b80;font-size:0.92rem;margin:0'>Paste weak resume bullets — get back powerful, ATS-optimized versions.</p>
    </div>
    """, unsafe_allow_html=True)

    bullets_input = st.text_area(
        "Paste your bullet points (one per line)",
        placeholder="• Worked on backend systems\n• Helped with marketing campaigns\n• Did data analysis tasks",
        height=200
    )

    if st.button("✏️ Rewrite Bullets") and bullets_input.strip():
        with st.spinner("Rewriting with impact..."):
            result = rewrite_bullets(bullets_input)
            st.session_state["rewritten_bullets"] = result

    if "rewritten_bullets" in st.session_state:
        rewritten = st.session_state["rewritten_bullets"].get("rewritten_bullets", [])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-header">📝 Original</div>', unsafe_allow_html=True)
            for line in bullets_input.strip().split("\n"):
                if line.strip():
                    st.markdown(f"""
                    <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem;font-size:0.88rem;color:#9898b0">{line.strip()}</div>
                    """, unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="section-header">⚡ Rewritten</div>', unsafe_allow_html=True)
            for bullet in rewritten:
                st.markdown(f"""
                <div style="background:rgba(0,229,160,0.04);border:1px solid rgba(0,229,160,0.15);border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem;font-size:0.88rem;color:var(--text)">{bullet}</div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RESUME COMPARE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚔️ Resume Compare":
    st.markdown("""
    <div style='margin-bottom:2rem'>
      <h1 style='font-size:2.2rem;font-weight:800;margin-bottom:0.3rem'>Resume Comparison</h1>
      <p style='color:#6b6b80;font-size:0.92rem;margin:0'>Compare two versions of your resume side-by-side to see which performs better.</p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-header">Resume A</div>', unsafe_allow_html=True)
        file_a = st.file_uploader("Upload Resume A", type=["pdf", "docx"], key="cmp_a")
    with col_b:
        st.markdown('<div class="section-header">Resume B</div>', unsafe_allow_html=True)
        file_b = st.file_uploader("Upload Resume B", type=["pdf", "docx"], key="cmp_b")

    if file_a and file_b:
        if st.button("⚔️ Compare Resumes", use_container_width=False):
            with st.spinner("Analyzing both resumes..."):
                text_a = parse_resume(file_a)
                text_b = parse_resume(file_b)
                cmp = compare_resumes(text_a, text_b)
                st.session_state["cmp_result"] = cmp

    if "cmp_result" in st.session_state:
        cmp = st.session_state["cmp_result"]
        winner = cmp.get("winner", "—")
        score_a = cmp.get("resume_a_score", 0)
        score_b = cmp.get("resume_b_score", 0)
        winner_color = "#00e5a0" if winner == "Resume A" else "#a78bfa" if winner == "Resume B" else "#f59e0b"

        st.markdown(f"""
        <div style="text-align:center;padding:2rem;background:var(--surface);border:1px solid var(--border);border-radius:20px;margin-bottom:1.5rem">
          <div class="section-header">WINNER</div>
          <div style="font-family:Syne,sans-serif;font-size:2.5rem;font-weight:800;color:{winner_color}">{winner}</div>
          <div style="font-family:DM Sans,sans-serif;font-size:0.9rem;color:#9898b0;margin-top:0.8rem;max-width:500px;margin-inline:auto">{cmp.get('recommendation','')}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        for col, label, score, strengths, weaknesses, color in [
            (c1, "Resume A", score_a, cmp.get("resume_a_strengths", []), cmp.get("resume_a_weaknesses", []), "#00e5a0"),
            (c2, "Resume B", score_b, cmp.get("resume_b_strengths", []), cmp.get("resume_b_weaknesses", []), "#a78bfa"),
        ]:
            with col:
                st.markdown(f"""
                <div class="compare-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
                    <div style="font-family:Syne,sans-serif;font-weight:700;font-size:1.1rem">{label}</div>
                    <div style="font-family:DM Mono,monospace;font-size:1.6rem;font-weight:700;color:{color}">{score}</div>
                  </div>
                  <div class="section-header">Strengths</div>
                  {"".join(f'<div class="strength-card" style="margin-bottom:0.4rem"><span style="color:{color}">◆</span><span style="font-size:0.85rem;margin-left:0.5rem">{s}</span></div>' for s in strengths)}
                  <div class="section-header" style="margin-top:0.8rem">Weaknesses</div>
                  {"".join(f'<div style="background:rgba(239,68,68,0.04);border:1px solid rgba(239,68,68,0.12);border-radius:8px;padding:0.6rem 0.8rem;margin-bottom:0.4rem;font-size:0.85rem;color:#fca5a5">{w}</div>' for w in weaknesses)}
                </div>
                """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#6b6b80">
          <div style="font-size:2.5rem;margin-bottom:1rem">⚔️</div>
          <div style="font-family:Syne,sans-serif;font-size:1rem">Upload two resumes above to compare them</div>
        </div>
        """, unsafe_allow_html=True)