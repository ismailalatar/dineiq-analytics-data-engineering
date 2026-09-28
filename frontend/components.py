"""Reusable UI components."""
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
