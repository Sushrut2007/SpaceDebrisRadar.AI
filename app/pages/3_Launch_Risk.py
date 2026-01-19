
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add components directory to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')
sys.path.insert(0, COMPONENTS_DIR)

import data_loader
import sidebar
import ui_theme
from components import context_explainer

# Page Config
st.set_page_config(page_title="Regional Suitability Assessment", page_icon="🛡️", layout="wide")
ui_theme.apply_theme()
sidebar.render_sidebar()

st.title("🛡️ Environmental Suitability Assessment")
st.markdown("""
<div style="font-size: 1.1rem; color: #cbd5e1; margin-bottom: 25px; line-height: 1.6;">
    Evaluate how suitable different orbital shells are for your mission.
    This tool helps you evaluate environmental risks based on satellite density, stability, and geometric complexity.
</div>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    try:
        trend_df = pd.read_csv(os.path.join(APP_DIR, '../data/outputs/trend_summary.csv'))
        sat_df = data_loader.load_satellite_data()
        return sat_df, trend_df
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

sat_df, trend_df = load_data()

if sat_df.empty:
    st.error("Environmental data unavailable.")
    st.stop()

# =============================================================================
# CONSTANTS & MAPPINGS
# =============================================================================

ALT_OPTIONS = [
    "Very Low LEO (200 - 400 km)",
    "Low LEO (400 - 600 km)",
    "Mid LEO (600 - 800 km)",
    "High LEO (800 - 1200 km)",
    "Upper LEO (1200+ km)"
]
ALT_MAP = {
    "Very Low LEO (200 - 400 km)": (200, 400),
    "Low LEO (400 - 600 km)": (400, 600),
    "Mid LEO (600 - 800 km)": (600, 800),
    "High LEO (800 - 1200 km)": (800, 1200),
    "Upper LEO (1200+ km)": (1200, 50000)
}

INC_OPTIONS = [
    "Equatorial (0° - 30°)",
    "Mid-Inclination (30° - 60°)",
    "Polar / SSO (60° - 100°)"
]
INC_MAP = {
    "Equatorial (0° - 30°)": (0, 30),
    "Mid-Inclination (30° - 60°)": (30, 60),
    "Polar / SSO (60° - 100°)": (60, 100)
}

# =============================================================================
# CLASSIFICATION LOGIC (RULE-BASED)
# =============================================================================

def assess_environment(alt_range, inc_range, density_mode, risk_profile, _sat_df):
    """
    Classifies the environment into Low/Moderate/High Suitability Risk using qualitative indicators.
    Returns dictionary with classification and indicator states.
    """
    alt_min, alt_max = alt_range
    inc_min, inc_max = inc_range
    
    # 1. Filter Environment Context (Aggregated Population)
    env_sats = _sat_df[
        (_sat_df['ORBIT_HEIGHT'] >= alt_min) & (_sat_df['ORBIT_HEIGHT'] < alt_max) &
        (_sat_df['INCLINATION'] >= inc_min) & (_sat_df['INCLINATION'] < inc_max)
    ]
    
    if density_mode == "Constellations Only":
        kws = ['STARLINK', 'ONEWEB', 'FLOCK', 'LEMUR']
        env_sats = env_sats[env_sats['OBJECT_NAME'].str.upper().str.contains('|'.join(kws), na=False)]
    elif density_mode == "Non-Constellation Objects":
        kws = ['STARLINK', 'ONEWEB', 'FLOCK', 'LEMUR']
        env_sats = env_sats[~env_sats['OBJECT_NAME'].str.upper().str.contains('|'.join(kws), na=False)]

    # 2. Indicator A: Congestion Level (Relative Intensity)
    # Heuristic thresholds for classification
    count = len(env_sats)
    # Determine thresholds based on altitude band width to normalize roughly
    if count > 1000: congestion = "High"
    elif count > 300: congestion = "Medium"
    else: congestion = "Low"
    
    # 3. Indicator B: Stability Condition (Anomaly Prevalence)
    anomalies = len(env_sats[env_sats['ANOMALY_LABEL'] == -1])
    rate = anomalies / count if count > 0 else 0
    
    if rate > 0.15: stability = "Poor"        # >15% anomalous
    elif rate > 0.05: stability = "Concern"   # 5-15% anomalous
    else: stability = "Nominal"               # <5% anomalous (Good)
    
    # 4. Indicator C: Geometric Complexity (Intrinsic)
    # Fixed by inclination class
    mid_inc = (inc_min + inc_max) / 2
    if mid_inc < 30: complexity = "Low"
    elif mid_inc < 60: complexity = "Medium"
    else: complexity = "High" # Polar/SSO
    
    # 5. Rule-Based Classification Matrix
    # Base risk derived from worst indicators
    
    # Conservative Profile Rules (Safety First)
    if "Conservative" in risk_profile:
        if congestion == "High" or stability == "Poor":
            risk_class = "High"
        elif congestion == "Medium" and (stability == "Concern" or complexity == "High"):
            risk_class = "High"
        elif congestion == "Medium" or complexity == "High":
             risk_class = "Moderate"
        else:
             risk_class = "Low"
             
    # Tolerant Profile Rules (Move Fast)
    elif "Tolerant" in risk_profile:
        if congestion == "High" and stability == "Poor":
            risk_class = "High"
        elif congestion == "High": # Tolerates high density if stable
            risk_class = "Moderate" 
        elif stability == "Poor":
            risk_class = "Moderate"
        else:
            risk_class = "Low"
            
    # Balanced (Standard)
    else:
        if congestion == "High" and stability == "Poor":
            risk_class = "High"
        elif congestion == "High" or stability == "Poor":
            risk_class = "Moderate" # Evaluates to Mod if only one factor is critical
            # Adjust for complexity
            if complexity == "High" and congestion == "High": risk_class = "High"
        elif congestion == "Medium" and stability == "Concern":
            risk_class = "Moderate"
        else:
            risk_class = "Low"

    return {
        "class": risk_class,
        "indicators": {
            "Congestion": congestion,
            "Stability": stability,
            "Complexity": complexity
        }
    }

# =============================================================================
# UI: MISSION INPUTS
# =============================================================================

st.markdown("### 🚀 Mission Configuration")

col_mission, col_space = st.columns([1, 1])

with col_mission:
    mission_name = st.text_input("Mission / Payload Name", value="Alpha-1")
    
    alt_band = st.selectbox("Target Altitude Band", options=ALT_OPTIONS, index=1)
    current_alt_idx = ALT_OPTIONS.index(alt_band)

    inc_class = st.selectbox("Target Inclination", options=INC_OPTIONS, index=1)

with col_space:
    density_mode = st.selectbox("Environment Filter", options=["All Active Satellites", "Constellations Only", "Non-Constellation Objects"])
    if density_mode == "Constellations Only":
        st.caption("ℹ️ **Focus:** Analyzes major satellite constellations.")
    elif density_mode == "Non-Constellation Objects":
        st.caption("ℹ️ **Focus:** Analyzes independent satellites and debris.")
    else:
         st.caption("ℹ️ **Focus:** Analyzes the complete orbital population.")

    risk_profile = st.selectbox("Risk Sensitivity", options=["Conservative (Strict)", "Balanced (Standard)", "Tolerant (Experimental)"], index=1)
    if "Conservative" in risk_profile:
        st.caption("⚖️ **Logic:** Prioritizes safety per precautionary principles.")
    elif "Tolerant" in risk_profile:
        st.caption("⚖️ **Logic:** Tolerates density; flags only critical instability.")
    else:
        st.caption("⚖️ **Logic:** Standard multi-factor evaluation.")

# =============================================================================
# MAIN ASSESSMENT
# =============================================================================

assessment = assess_environment(ALT_MAP[alt_band], INC_MAP[inc_class], density_mode, risk_profile, sat_df)
r_class = assessment['class']
indicators = assessment['indicators']

# Colors
colors = {"High": "#ef4444", "Moderate": "#f59e0b", "Low": "#10b981"}
main_color = colors.get(r_class, "grey")

st.markdown("---")
st.markdown("### 📋 Environment Suitability")

# Main Result Card
st.markdown(f"""
<div style="background: rgba(30,30,50,0.4); border-left: 8px solid {main_color}; padding: 25px; border-radius: 6px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
    <div style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Launch Risk Classification</div>
    <div style="font-size: 3.5rem; font-weight: 800; color: {main_color}; margin: 5px 0;">{r_class.upper()}</div>
    <div style="font-size: 1.1rem; color: #e2e8f0; margin-top: 15px; font-weight: 500;">
        {
            "This orbital shell is currently experiencing significant congestion or instability. Proceed with enhanced safety protocols." if r_class == 'High' else
            "This region shows elevated activity levels. Standard collision avoidance measures are recommended." if r_class == 'Moderate' else
            "Nominal Conditions: This orbit is relatively clear with stability within nominal ranges."
        }
    </div>
</div>
""", unsafe_allow_html=True)

# Indicator Cards (No Numbers)
st.markdown("")
c1, c2, c3 = st.columns(3)

def indicator_card(title, value, help_text):
    # Color logic for badges
    if value in ["High", "Poor", "Critical"]: i_color = "#ef4444"
    elif value in ["Medium", "Concern"]: i_color = "#f59e0b"
    else: i_color = "#10b981"
    
    return f"""
    <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 1.4rem; font-weight: 600; color: {i_color};">{value}</div>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 5px;">{help_text}</div>
    </div>
    """

with c1:
    st.markdown(indicator_card("Congestion Level", indicators['Congestion'], "Volume of active satellites in this band"), unsafe_allow_html=True)
    context_explainer.render_explainer('congestion', f"Level: {indicators['Congestion']}")
with c2:
    st.markdown(indicator_card("Stability Condition", indicators['Stability'], "Frequency of irregular satellite behavior"), unsafe_allow_html=True)
    context_explainer.render_explainer('stability', f"Status: {indicators['Stability']}")
with c3:
    st.markdown(indicator_card("Geometric Complexity", indicators['Complexity'], "Natural geometric complexity of the orbit"), unsafe_allow_html=True)
    context_explainer.render_explainer('complexity', f"Rating: {indicators['Complexity']}")

# HAZARD PROFILE VISUALIZATION (Segmented Status Ring)
col_vis, col_spacer = st.columns([1, 1.5])

with col_vis:
    st.markdown("### ⚠️ Hazard Profile")
    st.caption("Categorical status of environmental pillars.")
    
    # Define Segments
    labels = ["Congestion", "Stability", "Complexity"]
    
    # Map colors based on state
    def get_color(val):
        if val in ["High", "Poor", "Critical"]: return "#ef4444" # Red
        elif val in ["Medium", "Concern"]: return "#f59e0b" # Orange
        else: return "#10b981" # Green
        
    colors_mapped = [
        get_color(indicators['Congestion']),
        get_color(indicators['Stability']),
        get_color(indicators['Complexity'])
    ]
    
    # Create Donut Chart with equal segments
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=[1, 1, 1], # Equal size
        marker=dict(colors=colors_mapped, line=dict(color='#000000', width=4)),
        textinfo='label',
        hoverinfo='label+text',
        textfont=dict(size=14, color='white'),
        hole=0.6,
        sort=False,
        direction='clockwise'
    )])
    
    fig.update_layout(
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
        annotations=[dict(text=r_class.upper(), x=0.5, y=0.5, font_size=20, showarrow=False, font_weight='bold', font_color='white')]
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# SAFER ALTERNATIVES
# =============================================================================

if r_class != "Low":
    st.markdown("---")
    st.markdown("### 💡 Safer Alternatives")
    st.info(f"The selected regime ({alt_band}) is assessed as **{r_class} Risk**. Scanning adjacent bands for improved suitability...")
    
    # Check neighbors
    neighbors = []
    if current_alt_idx > 0: neighbors.append(current_alt_idx - 1)
    if current_alt_idx < len(ALT_OPTIONS) - 1: neighbors.append(current_alt_idx + 1)
    
    found_better = False
    col_alts = st.columns(len(neighbors))
    
    for i, idx in enumerate(neighbors):
        nb_name = ALT_OPTIONS[idx]
        nb_res = assess_environment(ALT_MAP[nb_name], INC_MAP[inc_class], density_mode, risk_profile, sat_df)
        
        # Determine if better: Low > Moderate > High
        rank = {"Low": 1, "Moderate": 2, "High": 3}
        is_better = rank[nb_res['class']] < rank[r_class]
        
        with col_alts[i]:
            nb_color = colors.get(nb_res['class'], "grey")
            border = f"2px solid {nb_color}" if is_better else "1px solid rgba(255,255,255,0.1)"
            opacity = "1.0" if is_better else "0.5"
            
            st.markdown(f"""
            <div style="border: {border}; padding: 15px; border-radius: 6px; background: rgba(0,0,0,0.2); opacity: {opacity};">
                <div style="font-size: 0.85rem; color: #cbd5e1;">{nb_name}</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {nb_color}; margin: 5px 0;">{nb_res['class']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Congestion: {nb_res['indicators']['Congestion']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if is_better: found_better = True

    if found_better:
        st.success("Recommendation: The highlighted adjacent bands offer a more favorable environmental profile.")
    else:
        st.warning("No significantly safer adjacent bands found within this inclination class.")

st.markdown("---")
st.caption("Methodology: Environmental Suitability is determined via qualitative classification of aggregated hazard indicators, not numeric probability modeling.")
