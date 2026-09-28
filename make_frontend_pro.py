import os
ROOT = r"D:\DineIQ\frontend"
os.makedirs(ROOT, exist_ok=True)

FILES = {}

FILES["__init__.py"] = ""

FILES["theme.py"] = '''"""DineIQ professional dark theme."""

CSS = """
<style>
    .stApp { background: linear-gradient(135deg, #0E1117 0%, #131820 100%); }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #131820 0%, #0E1117 100%);
        border-right: 1px solid #2D3548;
    }

    .metric-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 1px solid #2D3548;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #FF6B35;
        box-shadow: 0 4px 20px rgba(255,107,53,0.15);
        transform: translateY(-2px);
    }
    .metric-label { color: #A0A8B8; font-size: 13px; text-transform: uppercase;
                    letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { color: #FFFFFF; font-size: 32px; font-weight: 700; margin: 0;
                    line-height: 1.2; }

    .page-title { color: #FFFFFF; font-size: 32px; font-weight: 700; margin-bottom: 4px; }
    .page-subtitle { color: #6B7280; font-size: 14px; margin-bottom: 24px; }

    .section-header {
        color: #FFFFFF; font-size: 18px; font-weight: 600;
        margin: 24px 0 12px 0; padding-bottom: 8px;
        border-bottom: 2px solid #FF6B35; display: inline-block;
    }

    .empty-state {
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 2px dashed #2D3548;
        border-radius: 12px; padding: 48px 24px;
        text-align: center; margin: 24px 0;
    }
    .empty-icon { font-size: 64px; margin-bottom: 16px; }
    .empty-title { color: #FFFFFF; font-size: 20px; font-weight: 600; margin-bottom: 8px; }
    .empty-desc { color: #A0A8B8; font-size: 14px; }

    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px;
             font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .badge-critical { background: rgba(255,71,87,0.2); color: #FF4757; border: 1px solid #FF4757; }
    .badge-high { background: rgba(255,184,0,0.2); color: #FFB800; border: 1px solid #FFB800; }
    .badge-medium { background: rgba(74,158,255,0.2); color: #4A9EFF; border: 1px solid #4A9EFF; }
    .badge-low { background: rgba(160,168,184,0.2); color: #A0A8B8; border: 1px solid #A0A8B8; }
    .badge-success { background: rgba(0,200,150,0.2); color: #00C896; border: 1px solid #00C896; }

    .user-avatar {
        width: 48px; height: 48px; border-radius: 50%;
        background: linear-gradient(135deg, #FF6B35, #FF8555);
        color: white; display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 20px; margin-bottom: 12px;
    }

    .info-banner {
        background: linear-gradient(135deg, rgba(74,158,255,0.1), rgba(74,158,255,0.05));
        border: 1px solid rgba(74,158,255,0.3);
        border-radius: 8px; padding: 16px 20px; margin: 16px 0; color: #FFFFFF;
    }

    .login-container {
        max-width: 480px; margin: 5% auto;
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 1px solid #2D3548; border-radius: 16px;
        padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .login-logo { font-size: 64px; text-align: center; margin-bottom: 8px; }
    .login-title { color: #FFFFFF; font-size: 28px; font-weight: 700;
                   text-align: center; margin-bottom: 4px; }
    .login-subtitle { color: #A0A8B8; font-size: 14px;
                      text-align: center; margin-bottom: 24px; }

    .stButton > button {
        background: linear-gradient(135deg, #FF6B35, #FF8555);
        color: white; border: none; border-radius: 8px; font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 15px rgba(255,107,53,0.4);
        transform: translateY(-1px);
    }

    .stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #2D3548; }

    .rec-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 1px solid #2D3548; border-left: 4px solid #FF6B35;
        border-radius: 8px; padding: 16px 20px; margin: 12px 0;
    }
    .rec-action {
        background: rgba(0,200,150,0.08); border-left: 3px solid #00C896;
        padding: 10px 14px; border-radius: 4px; margin-top: 10px;
        color: #D0D8E8; font-size: 14px;
    }
</style>
"""

COLORS = {
    "orange": "#FF6B35",
    "blue": "#4A9EFF",
    "green": "#00C896",
    "yellow": "#FFB800",
    "red": "#FF4757",
    "gray": "#A0A8B8",
}
'''

FILES["components.py"] = '''"""Reusable UI components."""
import streamlit as st


def metric_card(label, value, icon="", delta=None):
    icon_html = f'<div style="font-size:24px;margin-bottom:8px;">{icon}</div>' if icon else ""
    delta_html = f'<div style="color:#00C896;font-size:12px;margin-top:4px;">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        {icon_html}
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def page_header(title, subtitle, icon=""):
    st.markdown(f"""
    <div class="page-title">{icon} {title}</div>
    <div class="page-subtitle">{subtitle}</div>
    """, unsafe_allow_html=True)


def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def empty_state(icon, title, description):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">{icon}</div>
        <div class="empty-title">{title}</div>
        <div class="empty-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def info_banner(html_text):
    st.markdown(f'<div class="info-banner">{html_text}</div>', unsafe_allow_html=True)


def priority_badge(p):
    p = (p or "low").lower()
    return f'<span class="badge badge-{p}">{p.upper()}</span>'


def user_avatar(name):
    initials = "".join([w[0].upper() for w in (name or "U").split()[:2]])
    return f'<div class="user-avatar">{initials}</div>'


def recommendation_card(finding, evidence, action, priority):
    st.markdown(f"""
    <div class="rec-card">
        <div style="display:flex;justify-content:space-between;align-items:start;">
            <div style="color:#FFFFFF;font-size:16px;font-weight:600;flex:1;">
                {finding}
            </div>
            <div>{priority_badge(priority)}</div>
        </div>
        <div style="color:#A0A8B8;font-size:13px;margin-top:10px;">
            <b>📋 Evidence:</b> {evidence}
        </div>
        <div class="rec-action">
            <b>✅ Action:</b> {action}
        </div>
    </div>
    """, unsafe_allow_html=True)
'''

FILES["api.py"] = '''"""API client."""
import requests
import streamlit as st
import pandas as pd


class DineIQAPI:
    def __init__(self, base="http://localhost:5000/api/v1"):
        self.base = base

    def _h(self):
        t = st.session_state.get("token")
        return {"Authorization": f"Bearer {t}"} if t else {}

    def login(self, email, password):
        return requests.post(f"{self.base}/auth/login",
                             json={"email": email, "password": password}, timeout=15)

    def get(self, path, **params):
        return requests.get(f"{self.base}{path}", headers=self._h(),
                            params=params, timeout=30)

    def post(self, path, json=None):
        return requests.post(f"{self.base}{path}", headers=self._h(),
                             json=json, timeout=30)

    def df(self, path, **params):
        r = self.get(path, **params)
        if r.status_code != 200:
            return None
        data = r.json()
        return pd.DataFrame(data) if data else pd.DataFrame()

    def summary(self):
        r = self.get("/analytics/summary")
        return r.json() if r.status_code == 200 else {}
'''

FILES["app.py"] = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from theme import CSS
from components import (metric_card, page_header, section_header,
                        empty_state, info_banner, user_avatar,
                        recommendation_card)
from api import DineIQAPI

API = DineIQAPI()

st.set_page_config(
    page_title="DineIQ Analytics",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#A0A8B8",
    height=340,
    margin=dict(l=20, r=20, t=30, b=20),
)


# ============ LOGIN ============
def login_page():
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🍽️</div>
        <div class="login-title">DineIQ Analytics</div>
        <div class="login-subtitle">MenuMatrix Dining Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.form("login_form", border=False):
            email = st.text_input("📧 Email", value="admin@dineiq.local")
            password = st.text_input("🔒 Password", type="password", value="Admin@12345")
            submit = st.form_submit_button("Sign In →", use_container_width=True)

        if submit:
            with st.spinner("Authenticating..."):
                r = API.login(email, password)
            if r.status_code == 200:
                d = r.json()
                st.session_state.token = d["access_token"]
                st.session_state.user = d["user"]
                st.rerun()
            else:
                st.error(f"❌ Login failed ({r.status_code})")

        st.markdown("""
        <div style="text-align:center;margin-top:24px;color:#6B7280;font-size:12px;">
            Default: admin@dineiq.local / Admin@12345
        </div>
        """, unsafe_allow_html=True)


# ============ SIDEBAR ============
def render_sidebar():
    u = st.session_state.user
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:16px 0;">
            {user_avatar(u.get('full_name') or u.get('username'))}
            <div style="color:white;font-weight:600;font-size:16px;">
                {u.get('full_name') or u.get('username')}
            </div>
            <div style="color:#A0A8B8;font-size:12px;">{u.get('email')}</div>
            <div style="margin-top:8px;">
                <span class="badge badge-success">{(u.get('roles') or [''])[0]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        pages = [
            ("📊  Executive",              "Executive"),
            ("🍽️  Menu Intelligence",      "Menu"),
            ("👥  Customer Intelligence",  "Customer"),
            ("🗑️  Wastage",                 "Wastage"),
            ("📈  Forecast",                "Forecast"),
            ("🔀  Dual Pipeline",           "Dual"),
            ("💡  Recommendations",         "Recommendations"),
            ("🤖  Model Versions",          "Models"),
            ("📜  Audit Trail",             "Audit"),
        ]
        page = st.radio("Navigate",
                        [p[1] for p in pages],
                        format_func=lambda x: next(p[0] for p in pages if p[1] == x),
                        label_visibility="collapsed")

        st.divider()
        if st.button("🚪  Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

        st.markdown("""
        <div style="text-align:center;color:#4A5568;font-size:11px;margin-top:12px;">
            DineIQ v1.0 · SRS Ref
        </div>
        """, unsafe_allow_html=True)
    return page


# ============ EXECUTIVE ============
def page_executive():
    page_header("Executive Dashboard", "SRS Step 42 — Business KPIs and overview", "📊")
    s = API.summary()

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Recommendations", s.get("recommendations_count", 0), "💡")
    with c2: metric_card("Dual-Pipeline Cases", s.get("dual_pipeline_count", 0), "🔀")
    with c3: metric_card("Slow-Moving Items", s.get("slow_moving_count", 0), "🐢")
    with c4: metric_card("Locations Analyzed", s.get("location_intelligence_count", 0), "📍")

    st.markdown("<br>", unsafe_allow_html=True)

    if s.get("recommendations_count", 0) == 0:
        info_banner("""
        <b>⏳ Status:</b> 4B outputs are <b>PENDING_VALIDATION</b>.<br>
        <span style="color:#A0A8B8;font-size:13px;">
        SRS Step 13/14 + Anti-Shortcut §1.8 item 10 require an independent
        Python pipeline. 4B used an alternate baseline; integration resumes
        once corrected.
        </span>
        """)
        return

    df = API.df("/analytics/channel_intelligence")
    if df is not None and not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            section_header("Revenue by Channel")
            fig = px.bar(df, x="preferred_channel", y="revenue",
                         color="revenue", color_continuous_scale="Oranges")
            fig.update_layout(**CHART_LAYOUT, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            section_header("Channel Distribution")
            fig = px.pie(df, names="preferred_channel", values="orders",
                         color_discrete_sequence=px.colors.sequential.Oranges_r,
                         hole=0.5)
            fig.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)


# ============ MENU ============
def page_menu():
    page_header("Menu Intelligence", "SRS Step 43 — Classification and slow-moving items", "🍽️")
    df = API.df("/analytics/slow_moving")
    if df is None or df.empty:
        empty_state("🍽️", "No Menu Data Yet",
                    "Awaiting 4B validated outputs — data appears automatically.")
        return

    with st.expander("🔎 Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            classes = ["All"] + sorted(df["performance_class"].dropna().unique().tolist())
            perf = st.selectbox("Performance Class", classes)
        with c2:
            max_r = int(df["revenue"].max() or 1000)
            min_rev = st.slider("Min Revenue", 0, max_r, 0)
        with c3:
            max_w = float(df["wastage_pct"].max() or 100)
            max_waste = st.slider("Max Wastage %", 0.0, max_w, max_w)

    f = df.copy()
    if perf != "All":
        f = f[f["performance_class"] == perf]
    f = f[f["revenue"] >= min_rev]
    f = f[f["wastage_pct"] <= max_waste]

    c1, c2 = st.columns(2)
    with c1:
        section_header("Performance Distribution")
        counts = df["performance_class"].value_counts().reset_index()
        counts.columns = ["class", "count"]
        fig = px.pie(counts, names="class", values="count",
                     color_discrete_sequence=["#00C896", "#4A9EFF", "#FFB800", "#FF4757"],
                     hole=0.5)
        fig.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        section_header("Top 10 by Revenue")
        top = f.nlargest(10, "revenue")
        fig = px.bar(top, x="revenue", y="item_name", orientation="h",
                     color="revenue", color_continuous_scale="Oranges")
        fig.update_layout(**CHART_LAYOUT, yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    section_header(f"Items ({len(f)})")
    st.dataframe(f, use_container_width=True, height=380)


# ============ CUSTOMER ============
def page_customer():
    page_header("Customer Intelligence", "SRS Step 44 — Segments and channels", "👥")
    df = API.df("/analytics/channel_intelligence")
    if df is None or df.empty:
        empty_state("👥", "No Customer Data", "Awaiting 4B validated outputs.")
        return
    section_header("Channel Overview")
    st.dataframe(df, use_container_width=True)
    if "customers" in df.columns and "preferred_channel" in df.columns:
        fig = px.bar(df, x="preferred_channel", y="customers",
                     color="customers", color_continuous_scale="Oranges")
        fig.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)


# ============ WASTAGE ============
def page_wastage():
    page_header("Wastage Analysis", "SRS Step 45 — High-wastage items", "🗑️")
    df = API.df("/analytics/slow_moving")
    if df is None or df.empty:
        empty_state("🗑️", "No Wastage Data", "Awaiting 4B validated outputs.")
        return
    top = df.nlargest(20, "wastage_pct")[["item_name", "wastage_pct", "revenue", "performance_class"]]
    section_header("Top 20 High-Wastage Items")
    fig = px.bar(top, x="wastage_pct", y="item_name", orientation="h",
                 color="wastage_pct", color_continuous_scale="Reds")
    fig.update_layout(**CHART_LAYOUT, yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(top, use_container_width=True)


# ============ FORECAST ============
def page_forecast():
    page_header("Demand Forecast", "SRS Step 46 — Historical vs predicted", "📈")
    df = API.df("/analytics/dual_pipeline", limit=200)
    if df is None or df.empty:
        empty_state("📈", "No Forecast Data", "Awaiting 4B validated outputs.")
        return
    section_header("Forecast Timeline")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["actual"], name="Actual",
                             line=dict(color="#4A9EFF", width=2)))
    if "python_prediction" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["python_prediction"],
                                 name="Python", line=dict(color="#FF6B35", dash="dash")))
    if "spark_prediction" in df.columns and df["spark_prediction"].notna().any():
        fig.add_trace(go.Scatter(x=df["date"], y=df["spark_prediction"],
                                 name="Spark", line=dict(color="#00C896", dash="dot")))
    fig.update_layout(**CHART_LAYOUT, height=420)
    st.plotly_chart(fig, use_container_width=True)


# ============ DUAL ============
def page_dual():
    page_header("Dual-Pipeline Comparison", "SRS Step 47 — Spark vs Python", "🔀")
    df = API.df("/analytics/dual_pipeline", limit=100)
    if df is None or df.empty:
        empty_state("🔀", "No Dual-Pipeline Data", "Awaiting 4B validated outputs.")
        return
    if "match" in df.columns:
        matched = int(df["match"].sum())
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("Total Cases", len(df), "📊")
        with c2: metric_card("Matched", matched, "✅")
        with c3: metric_card("Agreement %", f"{matched/len(df)*100:.1f}%", "🎯")
    st.dataframe(df, use_container_width=True, height=400)


# ============ RECOMMENDATIONS ============
def page_recommendations():
    page_header("Recommendations", "SRS Step 37/38 — Evidence-based actions", "💡")
    df = API.df("/analytics/recommendations")
    if df is None or df.empty:
        empty_state("💡", "No Recommendations Yet", "Awaiting 4B validated outputs.")
        return

    priorities = ["All"] + sorted(df["priority"].dropna().unique().tolist())
    p = st.selectbox("Filter by Priority", priorities)
    f = df if p == "All" else df[df["priority"] == p]

    st.caption(f"Showing {len(f)} recommendations")
    for _, row in f.iterrows():
        recommendation_card(
            finding=row.get("finding", ""),
            evidence=row.get("evidence", ""),
            action=row.get("action", ""),
            priority=row.get("priority", "Low"),
        )


# ============ MODELS ============
def page_models():
    page_header("Model Version Tracking", "SRS FR lxii — Identify model versions", "🤖")
    df = API.df("/models")
    if df is None or df.empty:
        empty_state("🤖", "No Models Registered",
                    "Register via POST /api/v1/models")
        return
    st.dataframe(df, use_container_width=True)


# ============ AUDIT ============
def page_audit():
    page_header("Audit Trail", "SRS FR lxiii — User, Action, Resource, Result", "📜")
    df = API.df("/audit", limit=200)
    if df is None or df.empty:
        empty_state("📜", "No Audit Entries", "Actions will appear here.")
        return
    actions = ["All"] + sorted(df["action"].dropna().unique().tolist())
    a = st.selectbox("Filter by Action", actions)
    f = df if a == "All" else df[df["action"] == a]
    st.dataframe(f, use_container_width=True, height=500)


# ============ ROUTER ============
def main():
    page = render_sidebar()
    if page == "Executive":       page_executive()
    elif page == "Menu":          page_menu()
    elif page == "Customer":      page_customer()
    elif page == "Wastage":       page_wastage()
    elif page == "Forecast":      page_forecast()
    elif page == "Dual":          page_dual()
    elif page == "Recommendations": page_recommendations()
    elif page == "Models":        page_models()
    elif page == "Audit":         page_audit()


if st.session_state.token is None:
    login_page()
else:
    main()
'''

for name, content in FILES.items():
    path = os.path.join(ROOT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  created: frontend/{name}")

print("\nDONE frontend pro")