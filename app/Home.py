"""
SpaceDebrisRadar.AI - Home Page (System Overview)
SpaceDebrisRadar | LEO Situational Awareness.
"""

import streamlit as st
import sys
import os
import time
from datetime import datetime
import base64

# Add components directory to path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')
sys.path.insert(0, COMPONENTS_DIR)

from data_loader import (
    get_system_metrics,
    get_cluster_summary,
    load_trend_summary
)
from anomaly_explainer import (
    get_risk_style,
    get_trend_icon
)
from sidebar import render_sidebar
from components import ui_theme
from components import context_explainer

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="SpaceDebrisRadar.AI | LEO Situational Awareness",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Theme
ui_theme.apply_theme()

render_sidebar()

# =============================================================================
# UTILITIES
# =============================================================================

def get_base64_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_hero_image(png_file):
    bin_str = get_base64_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .hero-container {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        height: 250px;
        border-radius: 24px;
        margin-bottom: 30px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .hero-overlay {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to bottom, rgba(10,10,15,0.2), rgba(10,10,15,0.8));
    }}
    .hero-content {{
        position: relative;
        z-index: 10;
        text-align: center;
        padding: 0 20px;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# =============================================================================
# CUSTOM STYLING
# =============================================================================
# Note: Theme styling is now handled globally by ui_theme.apply_theme()
# We only keep page-specific layout styles if necessary.
st.markdown("""
<style>
    /* Hide default sidebar navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Metric Styles - inheriting from theme but adding layout specifics */
    .premium-metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 8px;
    }
    
    .premium-metric-label {
        font-size: 0.85rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }

    /* Sub-header underline */
    .sub-glow {
        height: 2px;
        width: 60px;
        background: linear-gradient(90deg, #00d4ff, transparent);
        margin-bottom: 20px;
    }

    /* Status Pulse */
    .status-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #10b981;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 1);
        transform: scale(1);
        animation: pulse-green 2s infinite;
    }

    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA LOADING
# =============================================================================

metrics = get_system_metrics()
trend_summary = load_trend_summary()
cluster_summary = get_cluster_summary()

# =============================================================================
# HERO SECTION
# =============================================================================

hero_path = os.path.join(APP_DIR, 'assets', 'hero.png')
if os.path.exists(hero_path):
    set_hero_image(hero_path)
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-overlay"></div>
        <div class="hero-content">
            <h1 style="font-size: 3.5rem; color: white; margin-bottom: 10px;">SPACEDEBRIS<span style="color:#00d4ff">RADAR</span>.AI</h1>
            <p style="font-size: 1.2rem; color: #cbd5e1; max-width: 600px; margin: 0 auto; line-height: 1.5;">
                Low Earth Orbit Traffic & Risk Monitoring System.<br>
                Tracking {metrics['total_satellites']:,} objects.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🛰️ SpaceDebrisRadar.AI")

# =============================================================================
# OPERATIONAL SNAPSHOT
# =============================================================================

st.markdown("### 📡 Operational Snapshot")
st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value">{metrics['total_satellites']:,}</div>
        <div class="premium-metric-label">Tracked Objects</div>
    </div>
    """, unsafe_allow_html=True)
    context_explainer.render_explainer('active_trackers', f"{metrics['total_satellites']:,} objects tracked")

with m_col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value">{metrics['total_shells']}</div>
        <div class="premium-metric-label">Orbital Shells</div>
    </div>
    """, unsafe_allow_html=True)
    context_explainer.render_explainer('orbital_regimes', f"{metrics['total_shells']} shells defined")

with m_col3:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value" style="background: linear-gradient(135deg, #fb7185 0%, #f43f5e 100%); -webkit-background-clip: text;">{metrics['total_anomalies']:,}</div>
        <div class="premium-metric-label">Anomalies Detected</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    risk = metrics['overall_risk']
    risk_style = get_risk_style(risk)
    # Adjust font size for longer text (e.g. "Moderate")
    font_size = "2.2rem" if len(risk) > 5 else "3rem"
    
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value" style="background: {risk_style['color']}; -webkit-background-clip: text; font-size: {font_size};">{risk}</div>
        <div class="premium-metric-label">Collision Risk Index</div>
    </div>
    """, unsafe_allow_html=True)
    context_explainer.render_explainer('collision_risk_index', f"Current Level: {risk}")

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# CORE CONTENT
# =============================================================================

left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.markdown("#### 🌍 Orbital Traffic Overview")
    st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)
    
    for _, row in cluster_summary.iterrows():
        r_style = get_risk_style(row['risk_level'])
        t_icon = get_trend_icon(row['trend_type'])
        
        st.markdown(f"""
        <div class="glass-card" style="margin-bottom: 12px; padding: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #f1f5f9;">Shell {row['cluster_id']} <span style="font-weight: 400; color: #64748b; font-size: 0.9rem; margin-left: 8px;">{row['min_altitude']:.0f}-{row['max_altitude']:.0f} km</span></div>
                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">Active Objects: {row['satellite_count']:,} active objects</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {r_style['color']}; font-weight: 600; font-size: 0.9rem;">{r_style['icon']} {row['risk_level']}</div>
                    <div style="color: #64748b; font-size: 0.85rem;">{t_icon} {row['trend_type']}</div>
                </div>
            </div>
            <div style="margin-top: 12px; display: flex; gap: 20px;">
                <div style="font-size: 0.8rem; color: #64748b;">
                    <span style="color: #e2e8f0; font-weight: 500;">{row['anomaly_count']}</span> Anomalies
                </div>
                <div style="font-size: 0.8rem; color: #64748b;">
                    <span style="color: #e2e8f0; font-weight: 500;">{row['anomaly_rate']}%</span> Anomaly Rate
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with right_col:
    st.markdown("#### 🧪 Methodology")
    st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)
    
    # Initialize session state for methodology selection if not exists
    if 'methodology_selection' not in st.session_state:
        st.session_state.methodology_selection = 'Orbital Clustering'

    # Methodology Buttons
    st.markdown("""
        <style>
        div.stButton > button {
            height: 3.5rem;
            white-space: pre-wrap;
        }
        </style>
    """, unsafe_allow_html=True)
    
    meth_col1, meth_col2, meth_col3 = st.columns(3)
    
    with meth_col1:
        if st.button("Orbital Clustering", use_container_width=True, type="primary" if st.session_state.methodology_selection == 'Orbital Clustering' else "secondary"):
            st.session_state.methodology_selection = 'Orbital Clustering'
            st.rerun()
            
    with meth_col2:
        if st.button("Anomaly Detection", use_container_width=True, type="primary" if st.session_state.methodology_selection == 'Anomaly Detection' else "secondary"):
            st.session_state.methodology_selection = 'Anomaly Detection'
            st.rerun()
            
    with meth_col3:
        if st.button("Risk Prediction", use_container_width=True, type="primary" if st.session_state.methodology_selection == 'Risk Prediction' else "secondary"):
            st.session_state.methodology_selection = 'Risk Prediction'
            st.rerun()

    # Dynamic Content Display
    st.markdown(f"""
    <div class="glass-card" style="margin-top: 10px; min-height: 120px;">
        <p style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 15px;">
            The system analyzes satellite traffic and orbital behavior using clustering, anomaly detection, and trend analysis to assess congestion and collision risk in Low Earth Orbit.
        </p>
    """, unsafe_allow_html=True)

    if st.session_state.methodology_selection == 'Orbital Clustering':
        st.markdown(f"""
        <div style="display: flex; gap: 15px; animation: fadeIn 0.5s;">
            <div style="background: rgba(0, 212, 255, 0.1); width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #00d4ff; font-weight: bold; font-size: 1.2rem;">1</div>
            <div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 1.1rem; margin-bottom: 4px;">Orbital Clustering</div>
                <div style="font-size: 0.9rem; color: #94a3b8;">Groups satellites with similar orbital patterns to organize the LEO environment.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    elif st.session_state.methodology_selection == 'Anomaly Detection':
        st.markdown(f"""
        <div style="display: flex; gap: 15px; animation: fadeIn 0.5s;">
            <div style="background: rgba(124, 58, 237, 0.1); width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #7c3aed; font-weight: bold; font-size: 1.2rem;">2</div>
            <div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 1.1rem; margin-bottom: 4px;">Anomaly Detection</div>
                <div style="font-size: 0.9rem; color: #94a3b8;">Detects satellites showing unusual deviations from their expected group behavior.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    elif st.session_state.methodology_selection == 'Risk Prediction':
        st.markdown(f"""
        <div style="display: flex; gap: 15px; animation: fadeIn 0.5s;">
            <div style="background: rgba(244, 63, 94, 0.1); width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #f43f5e; font-weight: bold; font-size: 1.2rem;">3</div>
            <div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 1.1rem; margin-bottom: 4px;">Risk Prediction</div>
                <div style="font-size: 0.9rem; color: #94a3b8;">Analyzes historical trends to forecast future traffic growth and potential risks.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # SYSTEM STATUS
    st.markdown(f"""
    <div class="glass-card" style="padding: 15px;">
        <div style="display: flex; align-items: center;">
            <div class="status-pulse"></div>
            <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">System Operational</div>
        </div>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 8px; margin-left: 18px;">
            Last sync: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC<br>
            Pipeline Status: Nominal
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# FOOTER / NAV
# =============================================================================

st.markdown("<br><hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)

st.warning("**Note:** Data refreshed every ~12h from Celestrak NORAD sources.")

# =============================================================================
# SIDEBAR
# =============================================================================

# (Moved to top)
