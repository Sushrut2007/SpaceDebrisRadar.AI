"""
SpaceDebrisRadar.AI - Orbital Shell Analysis Page
Comprehensive analysis of orbital shells.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add components directory to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')
sys.path.insert(0, COMPONENTS_DIR)

from data_loader import (
    load_satellite_data,
    get_cluster_summary,
    load_trend_summary
)
from anomaly_explainer import (
    get_risk_style,
    get_trend_icon,
    RISK_COLORS
)
from sidebar import render_sidebar
from components import ui_theme
from components import context_explainer

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Orbital Shells | SpaceDebrisRadar.AI",
    page_icon="🌐",
    layout="wide"
)

# Apply Theme
ui_theme.apply_theme()

render_sidebar()

# =============================================================================
# STYLING
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    
    .shell-detail-card {
        background: linear-gradient(145deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 35, 0.98));
        border: 1px solid rgba(100, 100, 150, 0.3);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 24px;
    }
    
    .shell-stat {
        background: rgba(40, 40, 70, 0.6);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label { color: #8888aa; font-size: 0.85rem; margin-top: 4px; }
    
    /* Dynamics Cards */
    .dynamics-card {
        background: rgba(30, 30, 60, 0.4);
        border: 1px solid rgba(100, 100, 200, 0.2);
        border-radius: 16px;
        padding: 20px;
        height: 100%;
        transition: transform 0.3s ease;
    }
    .dynamics-card:hover {
        transform: translateY(-5px);
        background: rgba(40, 40, 80, 0.5);
        border-color: rgba(0, 212, 255, 0.4);
    }
    .dynamics-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .range-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        text-align: center;
    }
    .range-item {
        display: flex;
        flex-direction: column;
    }
    .range-val {
        font-size: 1.1rem;
        font-weight: 700;
        color: white;
    }
    .range-label {
        font-size: 0.65rem;
        color: #64748b;
        margin-top: 2px;
    }
    .avg-highlight {
        color: #00d4ff;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="padding: 10px 0 20px 0;">
    <h1 style="font-size: 2rem; font-weight: 700; color: #e0e0e8; margin-bottom: 4px;">
        🌐 Orbital Shell Analysis
    </h1>
    <p style="color: #8888aa; font-size: 1rem;">
        Detailed assessment of orbital clusters — object distribution and environmental stability
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# DATA
# =============================================================================

df = load_satellite_data()
# We still load the summary for the "Overview" table, but we will recompute specific shell stats dynamically
cluster_summary = get_cluster_summary()
trend_summary = load_trend_summary()

# =============================================================================
# DATA FILTERS (SIDEBAR)
# =============================================================================

st.sidebar.markdown("### 🔍 Data Filters")

# 1. Altitude Range Filter
min_alt = int(df['ORBIT_HEIGHT'].min())
max_alt = int(df['ORBIT_HEIGHT'].max())
selected_alt_range = st.sidebar.slider(
    "Altitude Range (km)",
    min_value=min_alt,
    max_value=max_alt,
    value=(min_alt, max_alt),
    step=50
)

# 2. Satellite Family Filter
# Heuristic: First word of OBJECT_NAME is the family (e.g., STARLINK, ONEWEB)
# refined to handle "STARLINK-123" by treating hyphens as separators
df['FAMILY'] = df['OBJECT_NAME'].apply(lambda x: x.replace('-', ' ').split()[0].upper() if isinstance(x, str) else 'Unknown')
family_counts = df['FAMILY'].value_counts()
# Only show families with > 50 satellites (increased threshold since we have 13k sats) to keep list clean
major_families = family_counts[family_counts > 50].index.tolist()
# Add "Other" for the rest
if len(df['FAMILY'].unique()) > len(major_families):
    major_families.append("Other")

selected_family = st.sidebar.selectbox(
    "Satellite Family",
    options=["All Families"] + sorted(major_families),
    index=0
)

# Apply Filters
filtered_df = df[
    (df['ORBIT_HEIGHT'] >= selected_alt_range[0]) & 
    (df['ORBIT_HEIGHT'] <= selected_alt_range[1])
]

if selected_family != "All Families":
    if selected_family == "Other":
        # Filter for families NOT in the major list (excluding 'Other' string itself)
        explicit_families = [f for f in major_families if f != "Other"]
        filtered_df = filtered_df[~filtered_df['FAMILY'].isin(explicit_families)]
    else:
        filtered_df = filtered_df[filtered_df['FAMILY'] == selected_family]


# =============================================================================
# SHELL SELECTOR
# =============================================================================

available_shells = sorted(filtered_df['CLUSTER'].unique())

col_select, col_info = st.columns([1, 2])

with col_select:
    # Handle case where filter returns empty result
    if len(available_shells) == 0:
        st.warning("No satellites match the current filters.")
        st.stop()
    
    # Logic to persist selection across filter updates
    # We try to keep the currently selected shell if it still exists in the filtered list
    current_selection = st.session_state.get('last_selected_shell')
    
    default_index = 0
    if current_selection in available_shells:
        default_index = available_shells.index(current_selection)
        
    shell_id = st.selectbox(
        "Select Shell to Analyze",
        options=available_shells,
        index=default_index,
        format_func=lambda x: f"Shell {x}"
    )
    
    # Update session state
    st.session_state.last_selected_shell = shell_id

# DYNAMIC RECOMPUTATION OF SHELL DATA
# Instead of using pre-computed `cluster_summary`, we calculate from `filtered_df`
shell_satellites = filtered_df[filtered_df['CLUSTER'] == shell_id]
shell_trend = trend_summary[trend_summary['CLUSTER_ID'] == shell_id].iloc[0] if not trend_summary[trend_summary['CLUSTER_ID'] == shell_id].empty else None

# Helper to safely get value or default
trend_type = shell_trend['TREND_TYPE'] if shell_trend is not None else "Unknown"
risk_level = shell_trend['LAUNCH_RISK_LEVEL'] if shell_trend is not None else "N/A"

# On-the-fly stats for the selected subset
shell_data = {
    'satellite_count': len(shell_satellites),
    'anomaly_count': len(shell_satellites[shell_satellites['ANOMALY_LABEL'] == -1]),
    'anomaly_rate': round(len(shell_satellites[shell_satellites['ANOMALY_LABEL'] == -1]) / len(shell_satellites) * 100, 1) if len(shell_satellites) > 0 else 0,
    'avg_altitude': round(shell_satellites['ORBIT_HEIGHT'].mean(), 1),
    'avg_inclination': round(shell_satellites['INCLINATION'].mean(), 1),
    'min_speed': round(shell_satellites['ORBITAL_SPEED'].min(), 2),
    'max_speed': round(shell_satellites['ORBITAL_SPEED'].max(), 2),
    'avg_speed': round(shell_satellites['ORBITAL_SPEED'].mean(), 2),
    'min_period': round(shell_satellites['ORBIT_PERIOD_SEC'].min() / 60, 1),
    'max_period': round(shell_satellites['ORBIT_PERIOD_SEC'].max() / 60, 1),
    'avg_period': round(shell_satellites['ORBIT_PERIOD_SEC'].mean() / 60, 1),
    'min_inclination': round(shell_satellites['INCLINATION'].min(), 1),
    'max_inclination': round(shell_satellites['INCLINATION'].max(), 1),
    'altitude_span': round(shell_satellites['ORBIT_HEIGHT'].max() - shell_satellites['ORBIT_HEIGHT'].min(), 1),
    'activity_fraction': round(shell_trend['CURRENT_ACTIVITY_FRACTION'] * 100, 1) if shell_trend is not None else 0,
    'trend_type': trend_type,
    'risk_level': risk_level
}

risk_style = get_risk_style(shell_data['risk_level'])
trend_icon = get_trend_icon(shell_data['trend_type'])

with col_info:
    st.markdown(f"""
    <div style="padding: 10px 20px; background: rgba(40,40,70,0.4); border-radius: 12px; display: inline-block; margin-top: 28px;">
        <span style="color: {risk_style['color']}; font-weight: 600; font-size: 1.2rem;">
            {risk_style['icon']} {shell_data['risk_level']} Risk
        </span>
        <span style="color: #6b6b8a; margin-left: 20px;">
            {trend_icon} {shell_data['trend_type']}
        </span>
        <span style="color: #00d4ff; margin-left: 20px; font-size: 0.9rem;">
            Subset: {shell_data['satellite_count']} objects
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# SHELL DETAILED STATS
# =============================================================================

st.markdown(f"""
<div class="shell-detail-card">
    <h2 style="color: #e0e0e8; margin-bottom: 24px; font-size: 1.5rem;">
        📊 Shell {shell_id} Statistics
    </h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="shell-stat">
        <div class="stat-number">{shell_data['satellite_count']:,}</div>
        <div class="stat-label">Total Satellites</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="shell-stat">
        <div class="stat-number">{shell_data['anomaly_count']}</div>
        <div class="stat-label">Anomalies ({shell_data['anomaly_rate']}%)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="shell-stat">
        <div class="stat-number">{shell_data['avg_altitude']:.0f}</div>
        <div class="stat-label">Avg Altitude (km)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="shell-stat">
        <div class="stat-number">{shell_data['avg_inclination']:.1f}°</div>
        <div class="stat-label">Avg Inclination</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="shell-stat">
        <div class="stat-number">{shell_data['activity_fraction']}%</div>
        <div class="stat-label">Activity Level</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# ORBITAL DYNAMICS SECTION
# =============================================================================

st.markdown("### 🪐 Orbital Parameter Summary")

dyn_col1, dyn_col2, dyn_col3 = st.columns(3)

with dyn_col1:
    st.markdown(f"""
    <div class="dynamics-card">
        <div class="dynamics-title">⚡ Velocity Profile (km/s)</div>
        <div class="range-grid">
            <div class="range-item">
                <div class="range-val">{shell_data['min_speed']}</div>
                <div class="range-label">MINIMUM</div>
            </div>
            <div class="range-item">
                <div class="range-val avg-highlight">{shell_data['avg_speed']}</div>
                <div class="range-label">AVERAGE</div>
            </div>
            <div class="range-item">
                <div class="range-val">{shell_data['max_speed']}</div>
                <div class="range-label">MAXIMUM</div>
            </div>
        </div>
        <div style="margin-top: 15px; font-size: 0.75rem; color: #64748b; text-align: center;">
    </div>
    """, unsafe_allow_html=True)
    context_explainer.render_explainer('orbital_velocity', f"Avg Speed: {shell_data['avg_speed']} km/s")

with dyn_col2:
    st.markdown(f"""
    <div class="dynamics-card">
        <div class="dynamics-title">⏱️ Orbital Timing (min)</div>
        <div class="range-grid">
            <div class="range-item">
                <div class="range-val">{shell_data['min_period']}</div>
                <div class="range-label">MINIMUM</div>
            </div>
            <div class="range-item">
                <div class="range-val avg-highlight">{shell_data['avg_period']}</div>
                <div class="range-label">AVERAGE</div>
            </div>
            <div class="range-item">
                <div class="range-val">{shell_data['max_period']}</div>
                <div class="range-label">MAXIMUM</div>
            </div>
        </div>
        <div style="margin-top: 15px; font-size: 0.75rem; color: #64748b; text-align: center;">
    </div>
    """, unsafe_allow_html=True)
    context_explainer.render_explainer('orbital_period', f"Avg Period: {shell_data['avg_period']} min")

with dyn_col3:
    st.markdown(f"""
    <div class="dynamics-card">
        <div class="dynamics-title">📐 Geometry & Span</div>
        <div class="range-grid">
            <div class="range-item">
                <div class="range-val">{shell_data['min_inclination']}°</div>
                <div class="range-label">MIN INC</div>
            </div>
            <div class="range-item">
                <div class="range-val avg-highlight">{shell_data['avg_inclination']}°</div>
                <div class="range-label">AVG INC</div>
            </div>
            <div class="range-item">
                <div class="range-val">{shell_data['max_inclination']}°</div>
                <div class="range-label">MAX INC</div>
            </div>
        </div>
        <div style="margin-top: 15px; font-size: 0.75rem; color: #64748b; text-align: center;">
    </div>
    """, unsafe_allow_html=True)
    context_explainer.render_explainer('inclination', f"Avg Inc: {shell_data['avg_inclination']}°")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# SHELL INTELLIGENCE (NATURAL LANGUAGE INSIGHTS)
# =============================================================================

def generate_shell_insight(data):
    insights = {}
    
    # Traffic/Density Insight
    if data['satellite_count'] > 2000:
        insights['Traffic Analysis'] = f"📡 <b>High-Density Shell:</b> With {data['satellite_count']:,} objects, this shell exhibits high congestion levels."
    elif data['satellite_count'] > 1000:
        insights['Traffic Analysis'] = f"🛰️ <b>Moderate Density:</b> This shell maintains a steady flow of traffic with {data['satellite_count']:,} active objects."
    else:
        insights['Traffic Analysis'] = f"🌌 <b>Low Activity Region:</b> A lower density orbital region with {data['satellite_count']:,} satellites tracked."
        
    # Uniformity/Span Insight
    if data['altitude_span'] < 50:
        insights['Orbital Geometry'] = f"🎯 <b>Narrow Altitude Band:</b> Objects occupy a {data['altitude_span']:.0f}km vertical range."
    elif data['altitude_span'] > 250:
        insights['Orbital Geometry'] = f"🌊 <b>Large Altitude Band:</b> Objects occupy a {data['altitude_span']:.0f}km vertical range."
    else:
        insights['Orbital Geometry'] = f"📐 <b>Normal Altitude Band:</b> Objects occupy a {data['altitude_span']:.0f}km vertical range."
        
    # Stability Insight
    if data['risk_level'] == 'Low':
        insights['Stability Status'] = "✅ <b>Stable conditions:</b> The orbital environment is currently safe and predictable."
    elif data['risk_level'] == 'High':
        insights['Stability Status'] = "⚠️ <b>High risk:</b> Significant congestion and potential for collision detected."
    else:
        insights['Stability Status'] = "⚖️ <b>Moderate risk:</b> Activity levels are elevated but manageable."

    return insights

shell_insights = generate_shell_insight(shell_data)

st.markdown("### 🧠 Operational Observations")

# Tabs for navigation
# Custom CSS for bigger tabs
st.markdown("""
<style>
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        padding: 0px 20px;
    }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Traffic Analysis", "Orbital Geometry", "Stability Status"])

with tab1:
    st.markdown(f"""
        <div style="margin-top: 10px; padding: 20px; background: rgba(30, 41, 59, 0.2); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.1); color: #e2e8f0; font-size: 1.0rem; line-height: 1.6;">
            {shell_insights['Traffic Analysis']}
        </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown(f"""
        <div style="margin-top: 10px; padding: 20px; background: rgba(30, 41, 59, 0.2); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.1); color: #e2e8f0; font-size: 1.0rem; line-height: 1.6;">
            {shell_insights['Orbital Geometry']}
        </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown(f"""
        <div style="margin-top: 10px; padding: 20px; background: rgba(30, 41, 59, 0.2); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.1); color: #e2e8f0; font-size: 1.0rem; line-height: 1.6;">
            {shell_insights['Stability Status']}
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# VISUALIZATIONS - CLUSTER FOCUSED
# =============================================================================

col_viz1, col_viz2 = st.columns(2)

with col_viz1:
    st.markdown("#### 🎯 Altitude Distribution in This Shell")
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=shell_satellites['ORBIT_HEIGHT'],
        nbinsx=40,
        marker_color='#7c3aed',
        opacity=0.8
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,20,40,0.5)',
        font_color='#e0e0e8',
        xaxis_title="Altitude (km)",
        yaxis_title="Satellite Count",
        height=350,
        margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_viz2:
    st.markdown("#### 🔬 Eccentricity vs Mean Motion")
    
    # Color by anomaly status
    colors = shell_satellites['ANOMALY_LABEL'].map({1: '#4ade80', -1: '#f87171'})
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=shell_satellites['ECCENTRICITY'],
        y=shell_satellites['MEAN_MOTION'],
        mode='markers',
        marker=dict(
            color=colors,
            size=6,
            opacity=0.6
        ),
        hovertemplate="<b>%{text}</b><br>Eccentricity: %{x:.4f}<br>Mean Motion: %{y:.2f}<extra></extra>",
        text=shell_satellites['OBJECT_NAME']
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,20,40,0.5)',
        font_color='#e0e0e8',
        xaxis_title="Eccentricity",
        yaxis_title="Mean Motion (rev/day)",
        height=350,
        margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# COMPARISON WITH OTHER SHELLS
# =============================================================================

st.markdown("---")
st.markdown("### 📈 How This Shell Compares")

comparison_data = cluster_summary.copy()
comparison_data['is_selected'] = comparison_data['cluster_id'] == shell_id

col_comp1, col_comp2 = st.columns(2)

with col_comp1:
    fig = px.bar(
        comparison_data,
        x=comparison_data['cluster_id'].apply(lambda x: f"Shell {x}"),
        y='satellite_count',
        color='is_selected',
        color_discrete_map={True: '#7c3aed', False: '#4a4a6a'},
        title="Satellite Count by Shell"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,20,40,0.3)',
        font_color='#e0e0e8',
        showlegend=False,
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

with col_comp2:
    fig = px.bar(
        comparison_data,
        x=comparison_data['cluster_id'].apply(lambda x: f"Shell {x}"),
        y='anomaly_rate',
        color='risk_level',
        color_discrete_map={'Low': '#10b981', 'Moderate': '#f59e0b', 'High': '#ef4444', 'N/A': '#6b7280'},
        title="Anomaly Rate by Shell (%)"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,20,40,0.3)',
        font_color='#e0e0e8',
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# SHELL CHARACTERISTICS TABLE
# =============================================================================

st.markdown("### 📋 Shell Characteristics Summary")

# Display a clean summary table
summary_display = cluster_summary[['cluster_id', 'satellite_count', 'anomaly_rate', 
                                    'avg_altitude', 'trend_type', 'risk_level']].copy()
summary_display.columns = ['Shell', 'Satellites', 'Anomaly %', 'Avg Alt (km)', 'Trend', 'Risk']

st.dataframe(
    summary_display,
    use_container_width=True,
    hide_index=True
)
