import os

import streamlit as st
from dotenv import load_dotenv

# Cloud: use Streamlit Secrets. Local: use .env. Never put real keys in code.
load_dotenv()
try:
    cloud_key = st.secrets.get("DEEPSEEK_API_KEY")
except (FileNotFoundError, KeyError, AttributeError):
    cloud_key = None
if cloud_key and not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = str(cloud_key)

if not os.getenv("DEEPSEEK_API_KEY"):
    st.error("未配置 DeepSeek API Key。请在 Streamlit Cloud → App settings → Secrets 中设置 DEEPSEEK_API_KEY。")
    st.stop()
import numpy as np
import matplotlib.pyplot as plt

from planner import planner_agent
from tutor import tutor_agent
from evaluator import evaluator_agent

from memory import (
    load_progress,
    save_progress,

    load_self_assessment,
    save_self_assessment,

    get_learning_records,
    get_learning_records_by_date,
    get_daily_summary,
    get_recurring_weak_points,
    get_learning_trend,
    get_memory_summary,

    get_topic_attempt_count,
    update_latest_record_action,

    clear_progress
)


# =========================================================
# 页面设置
# =========================================================

st.set_page_config(
    page_title="Global AI课程引导型智能体",
    page_icon="🎓",
    layout="wide"
)


# Responsive layout: compact headings and spacing on phones only.
st.markdown("""
<style>
@media (max-width: 640px) {
    .stMainBlockContainer, .block-container {
        padding-top: 4.5rem !important; /* Keep title below Streamlit mobile toolbar */
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 4rem !important;
    }
    .stMainBlockContainer h1, .block-container h1 {
        font-size: 1.75rem !important;
        line-height: 1.3 !important;
        overflow-wrap: anywhere;
        margin: 0.45rem 0 0.65rem !important;
    }
    .stMainBlockContainer h2, .block-container h2 {
        font-size: 1.4rem !important;
        line-height: 1.35 !important;
        margin: 0.8rem 0 0.4rem !important;
    }
    .stMainBlockContainer h3, .block-container h3 {
        font-size: 1.2rem !important;
        line-height: 1.35 !important;
        margin: 0.65rem 0 0.3rem !important;
    }
    .stMainBlockContainer p, .block-container p,
    .stMainBlockContainer li, .block-container li {
        font-size: 0.96rem;
        line-height: 1.6;
        overflow-wrap: anywhere;
    }
    .stMainBlockContainer [data-testid="stVerticalBlock"] {
        gap: 0.7rem;
    }
    .stMainBlockContainer [data-testid="stMarkdownContainer"] pre {
        max-width: 100%;
        overflow-x: auto;
    }
    .stMainBlockContainer .stButton button,
