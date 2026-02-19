
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os


# Add components and pipeline directory to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .../app
PROJECT_ROOT = os.path.dirname(APP_DIR) # .../
PIPELINE_DIR = os.path.join(PROJECT_ROOT, 'pipeline')
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(1, APP_DIR)
if COMPONENTS_DIR not in sys.path:
    sys.path.insert(2, COMPONENTS_DIR)
if PIPELINE_DIR not in sys.path:
    sys.path.insert(3, PIPELINE_DIR)

import data_loader
import sidebar
import ui_theme
from components import context_explainer
from pipeline import risk_model, trend_analysis
import importlib
importlib.reload(risk_model)
importlib.reload(trend_analysis)

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
        # We only need trend_summary to get Global Benchmarks (min/max slope)
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

# =============================================================================
# RISK ASSESSMENT ADAPTER (Connects Selection -> Risk Model)
# =============================================================================

def get_live_risk_assessment(env_sats, trend_df, alt_span_km):
    """
    Calculates risk using the centralized Risk Model on the filtered dataset.
    Performs Live Trend Analysis on the user selection.
    """
    
    # 1. Calculate The Trio (Congestion, Stability, Complexity)
    total_count = len(env_sats)
    
    if total_count > 0:
        anomalies = len(env_sats[env_sats['ANOMALY_LABEL'] == -1])
        anomaly_rate = anomalies / total_count
        avg_inclination = env_sats['INCLINATION'].mean()
    else:
        anomaly_rate = 0.0
        avg_inclination = 0.0
        
        
    # Get labels AND flags
    congestion_label, congestion_crit = risk_model.get_congestion_level(total_count, alt_span_km)
    stability_label, stability_crit = risk_model.get_stability_level(anomaly_rate)
    complexity_label, complexity_crit = risk_model.get_complexity_level(avg_inclination)
    
    # 2. Live Trend Analysis (The Forecast)
    # Create a "Virtual Cluster" to feed into the standard pipeline function
    current_fraction = 0.5 # Default fallback
    
    if total_count >= 3:
        virtual_df = env_sats.copy()
        virtual_df['CLUSTER'] = 9999 # Dummy ID
        
        # Reuse pipeline logic
        ts = trend_analysis.prepare_time_series(virtual_df)
        _, models = trend_analysis.apply_linear_reg(ts)
        
        # Extract the slope and activity from our single virtual model
        if models and models[0]['Model'] is not None:
            slope = models[0]['Slope']
            current_fraction = models[0]['Current activity fraction']
        else:
            slope = 0.0
    else:
        slope = 0.0
        
    # 3. Global Benchmarking
    # Compare our local slope to the global system bounds
    if not trend_df.empty:
        min_global = trend_df['SLOPE'].min()
        max_global = trend_df['SLOPE'].max()
    else:
        min_global, max_global = -0.001, 0.001
        
    trend_type, trend_strength = risk_model.classify_trend(slope, min_global, max_global)
    
    # 4. Final Risk Calculation
    risk_class = risk_model.calculate_risk_level(
        congestion_label, 
        stability_label, 
        complexity_label, 
        trend_strength,
        current_fraction
    )
    
    return {
        "class": risk_class,
        "indicators": {
            "Congestion": congestion_label,
            "Stability": stability_label,
            "Complexity": complexity_label,
            "Trend": trend_type,
            "TrendStrength": trend_strength
        }
    }

# =============================================================================
# UI: MISSION INPUTS
# =============================================================================

def reset_scan():
    st.session_state.mission_scan_active = False

st.markdown("### 🚀 Mission Configuration")

col_mission, col_space = st.columns([1, 1])

with col_mission:
    mission_name = st.text_input("Mission / Payload Name", value="Alpha-1", on_change=reset_scan)
    
    alt_band = st.selectbox("Target Altitude Band", options=ALT_OPTIONS, index=1, on_change=reset_scan)
    current_alt_idx = ALT_OPTIONS.index(alt_band)

    inc_class = st.selectbox("Target Inclination", options=INC_OPTIONS, index=1, on_change=reset_scan)

with col_space:
    density_mode = st.selectbox("Environment Filter", options=["All Active Satellites", "Constellations Only", "Non-Constellation Objects"], on_change=reset_scan)
    if density_mode == "Constellations Only":
        st.caption("ℹ️ **Focus:** Analyzes major satellite constellations.")
    elif density_mode == "Non-Constellation Objects":
        st.caption("ℹ️ **Focus:** Analyzes independent satellites and debris.")
    else:
         st.caption("ℹ️ **Focus:** Analyzes the complete orbital population.")



# =============================================================================
# TRIGGER ANALYSIS
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)
col_btn, _ = st.columns([1, 2])
with col_btn:
    if st.button("🔍 Run Mission Safety Scan", use_container_width=True, type="primary", key="mission_safety_scan_btn"):
         # Trigger the scan
         with st.spinner("Analyzing orbital dynamics..."):
            import time
            time.sleep(1.2) # Just for the "Scan" feel
            
            # Perform Heavy Calculations ONCE
            alt_min, alt_max = ALT_MAP[alt_band]
            inc_min, inc_max = INC_MAP[inc_class]

            env_sats_filtered = sat_df[
                (sat_df['ORBIT_HEIGHT'] >= alt_min) & (sat_df['ORBIT_HEIGHT'] < alt_max) &
                (sat_df['INCLINATION'] >= inc_min) & (sat_df['INCLINATION'] < inc_max)
            ]

            if density_mode == "Constellations Only":
                kws = ['STARLINK', 'ONEWEB', 'FLOCK', 'LEMUR']
                env_sats_filtered = env_sats_filtered[env_sats_filtered['OBJECT_NAME'].str.upper().str.contains('|'.join(kws), na=False)]
            elif density_mode == "Non-Constellation Objects":
                kws = ['STARLINK', 'ONEWEB', 'FLOCK', 'LEMUR']
                env_sats_filtered = env_sats_filtered[~env_sats_filtered['OBJECT_NAME'].str.upper().str.contains('|'.join(kws), na=False)]
                
            alt_span = alt_max - alt_min
            assessment_result = get_live_risk_assessment(env_sats_filtered, trend_df, alt_span)
            
            # Store in state
            st.session_state.mission_scan_active = True
            st.session_state.scan_results = {
                "assessment": assessment_result,
                "env_sats": env_sats_filtered,
                "alt_band": alt_band,
                "inc_class": inc_class,
                "current_alt_idx": current_alt_idx
            }

if st.session_state.get('mission_scan_active', False) and 'scan_results' in st.session_state:
    results = st.session_state.scan_results
    assessment = results['assessment']
    env_sats = results['env_sats']
    
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
        st.markdown(indicator_card("Congestion Level", indicators['Congestion'], f"{len(env_sats)} active satellites in this band"), unsafe_allow_html=True)
        context_explainer.render_explainer('congestion', f"Level: {indicators['Congestion']}")
    with c2:
        st.markdown(indicator_card("Stability Condition", indicators['Stability'], "Frequency of irregular satellite behavior"), unsafe_allow_html=True)
        context_explainer.render_explainer('stability', f"Status: {indicators['Stability']}")
    with c3:
        st.markdown(indicator_card("Geometric Complexity", indicators['Complexity'], "Natural geometric complexity of the orbit"), unsafe_allow_html=True)
        context_explainer.render_explainer('complexity', f"Rating: {indicators['Complexity']}")

    # LIVE DISTRIBUTION SCATTER
    col_vis, col_spacer = st.columns([1.5, 1])

    with col_vis:
        st.markdown("### 🛰️ Local Population Density")
        st.caption(f"Inclination vs. Altitude distribution of {len(env_sats)} objects in target shell.")
        
        if not env_sats.empty:
            # Color by Anomaly Label if it exists
            if 'ANOMALY_LABEL' in env_sats.columns:
                color_map = {1: '#60a5fa', -1: '#ef4444'}
                color_val = env_sats['ANOMALY_LABEL'].map(color_map).fillna('#60a5fa')
            else:
                color_val = '#60a5fa'
                
            fig = go.Figure(data=[go.Scattergl(
                x=env_sats['INCLINATION'],
                y=env_sats['ORBIT_HEIGHT'],
                mode='markers',
                marker=dict(
                    size=7,
                    color=color_val,
                    opacity=0.6,
                    line=dict(width=1, color='rgba(255,255,255,0.1)')
                ),
                text=env_sats['OBJECT_NAME'] if 'OBJECT_NAME' in env_sats.columns else "",
                hovertemplate="<b>%{text}</b><br>Inc: %{x}°<br>Alt: %{y} km<extra></extra>"
            )])
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(255,255,255,0.02)',
                margin=dict(l=10, r=10, t=10, b=10),
                height=350,
                xaxis=dict(
                    title="Inclination (degree)", 
                    gridcolor='rgba(255,255,255,0.05)', 
                    showgrid=True,
                    zeroline=False
                ),
                yaxis=dict(
                    title="Altitude (km)", 
                    gridcolor='rgba(255,255,255,0.05)', 
                    showgrid=True,
                    zeroline=False
                ),
                font=dict(color='#94a3b8')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No distribution data available for selected range.")

    # =============================================================================
    # SAFER ALTERNATIVES
    # =============================================================================

    if r_class != "Low":
        # Scanner UI Implementation
        st.markdown("""
        <style>
            .scanner-container {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                display: flex;
                align-items: center;
                gap: 15px;
                position: relative;
                overflow: hidden;
                backdrop-filter: blur(5px);
            }
            
            .scanner-icon {
                width: 12px;
                height: 12px;
                background: #38bdf8;
                border-radius: 50%;
                position: relative;
                box-shadow: 0 0 10px #38bdf8;
                animation: pulse-scanner 2s infinite;
            }
            
            @keyframes pulse-scanner {
                0% { transform: scale(1); opacity: 0.8; box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }
                70% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); }
                100% { transform: scale(1); opacity: 0.8; box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
            }
            
            .scanner-content {
                color: #e2e8f0;
                font-size: 1.05rem;
                line-height: 1.5;
                z-index: 1;
            }
            
            .scanner-beam {
                position: absolute;
                top: 0;
                left: -100%;
                width: 200px;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.05), transparent);
                animation: sweep 4s infinite linear;
            }
            
            @keyframes sweep {
                0% { left: -100%; }
                100% { left: 200%; }
            }
        </style>
        <div class="scanner-container">
            <div class="scanner-beam"></div>
            <div class="scanner-icon"></div>
            <div class="scanner-content">
                The selected regime (<b>""" + results['alt_band'] + f"""</b>) is assessed as <b style="color: {colors.get(r_class, '#fff')}">{r_class} Risk</b>. Scanning adjacent bands for improved suitability...
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Check neighbors
        neighbors = []
        if results['current_alt_idx'] > 0: neighbors.append(results['current_alt_idx'] - 1)
        if results['current_alt_idx'] < len(ALT_OPTIONS) - 1: neighbors.append(results['current_alt_idx'] + 1)
        
        found_better = False
        col_alts = st.columns(len(neighbors))
        
        for i, idx in enumerate(neighbors):
            nb_name = ALT_OPTIONS[idx]
            nb_min, nb_max = ALT_MAP[nb_name]
            inc_min, inc_max = INC_MAP[results['inc_class']]
            
            nb_sats = sat_df[
                 (sat_df['ORBIT_HEIGHT'] >= nb_min) & (sat_df['ORBIT_HEIGHT'] < nb_max) &
                 (sat_df['INCLINATION'] >= inc_min) & (sat_df['INCLINATION'] < inc_max)
            ]
            
            if density_mode == "Constellations Only":
                 nb_sats = nb_sats[nb_sats['OBJECT_NAME'].str.upper().str.contains('|'.join(kws), na=False)]
            elif density_mode == "Non-Constellation Objects":
                 nb_sats = nb_sats[~nb_sats['OBJECT_NAME'].str.upper().str.contains('|'.join(kws), na=False)]
                 
            nb_span = nb_max - nb_min
            nb_res = get_live_risk_assessment(nb_sats, trend_df, nb_span)
            
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
            st.info(f"No safer adjacent altitudes found at this inclination ({results['inc_class']}). Consider changing inclination or orbital regime.")

    st.markdown("---")
    st.caption("Methodology: Environmental Suitability is determined via qualitative classification of aggregated hazard indicators, not numeric probability modeling.")
else:
    st.info("💡 Adjust mission settings above and click **Run Mission Safety Scan** to evaluate the environment.")
