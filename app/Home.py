"""
SpaceDebrisRadar.AI - Home Page (System Overview)
Premium Redesign: High-end situational awareness dashboard.
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
        height: 400px;
        border-radius: 24px;
        margin-bottom: 40px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
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
        font-size: 3rem;
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
                Advanced Orbital Situational Awareness powered by Autonomous Machine Learning. 
                Monitoring {metrics['total_satellites']:,} objects across {metrics['total_shells']} orbital shells.
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
        <div class="premium-metric-label">Active Trackers</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value">{metrics['total_shells']}</div>
        <div class="premium-metric-label">Orbital Regimes</div>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value" style="background: {risk_style['color']}; -webkit-background-clip: text;">{risk}</div>
        <div class="premium-metric-label">Collision Risk Index</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# CORE CONTENT
# =============================================================================

left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.markdown("#### 🌍 Orbital Intelligence")
    st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)
    
    for _, row in cluster_summary.iterrows():
        r_style = get_risk_style(row['risk_level'])
        t_icon = get_trend_icon(row['trend_type'])
        
        st.markdown(f"""
        <div class="glass-card" style="margin-bottom: 12px; padding: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #f1f5f9;">Shell {row['cluster_id']} <span style="font-weight: 400; color: #64748b; font-size: 0.9rem; margin-left: 8px;">{row['min_altitude']:.0f}-{row['max_altitude']:.0f} km</span></div>
                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">Capacity: {row['satellite_count']:,} active objects</div>
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
                    <span style="color: #e2e8f0; font-weight: 500;">{row['anomaly_rate']}%</span> Error Rate
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with right_col:
    st.markdown("#### 🧪 Methodology")
    st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="glass-card">
        <p style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.6;">
            We track thousands of satellites in real-time, using a custom analysis engine to keep the skies safe:
        </p>
        <div style="margin-top: 15px;">
            <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                <div style="background: rgba(0, 212, 255, 0.1); width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #00d4ff; font-weight: bold;">1</div>
                <div>
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Smart Grouping</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">We organize satellites into groups based on their altitude and path, making it easier to spot outliers.</div>
                </div>
            </div>
            <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                <div style="background: rgba(124, 58, 237, 0.1); width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #7c3aed; font-weight: bold;">2</div>
                <div>
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Anomaly Detection</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">Our system watches for any satellite behaving "weirdly"—like drifting off course or moving at the wrong speed.</div>
                </div>
            </div>
            <div style="display: flex; gap: 15px;">
                <div style="background: rgba(244, 63, 94, 0.1); width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #f43f5e; font-weight: bold;">3</div>
                <div>
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Risk Prediction</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">By looking at current trends, we estimate where the most crowded areas will be in the future.</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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

foot1, foot2, foot3 = st.columns(3)

with foot1:
    st.info("**Tip:** Use the Orbital Shells page for granular per-shell visualization.")

with foot2:
    st.success("**Update:** Anomaly deviation profiling is now active in the inspector.")

with foot3:
    st.warning("**Note:** Data refreshed every 24h from Celestrak NORAD sources.")

# =============================================================================
# SIDEBAR
# =============================================================================

# (Moved to top)
