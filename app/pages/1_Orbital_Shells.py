"""
SpaceDebrisRadar.AI - Orbital Shell Analysis Page
Detailed examination of clustered orbital regions - FOCUS ON CLUSTERS.
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
        Deep dive into each orbital shell - satellite density, stability metrics, and congestion trends
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# DATA
# =============================================================================

df = load_satellite_data()
cluster_summary = get_cluster_summary()
trend_summary = load_trend_summary()

# =============================================================================
# SHELL SELECTOR
# =============================================================================

col_select, col_info = st.columns([1, 2])

with col_select:
    shell_id = st.selectbox(
        "Select Shell to Analyze",
        options=sorted(df['CLUSTER'].unique()),
        format_func=lambda x: f"Shell {x}"
    )

# Get selected shell data
shell_data = cluster_summary[cluster_summary['cluster_id'] == shell_id].iloc[0]
shell_satellites = df[df['CLUSTER'] == shell_id]
shell_trend = trend_summary[trend_summary['CLUSTER_ID'] == shell_id].iloc[0]

risk_style = get_risk_style(shell_data['risk_level'])
trend_icon = get_trend_icon(shell_data['trend_type'])

with col_info:
    st.markdown(f"""
    <div style="padding: 10px 20px; background: rgba(40,40,70,0.4); border-radius: 12px; display: inline-block;">
        <span style="color: {risk_style['color']}; font-weight: 600; font-size: 1.2rem;">
            {risk_style['icon']} {shell_data['risk_level']} Risk
        </span>
        <span style="color: #6b6b8a; margin-left: 20px;">
            {trend_icon} {shell_data['trend_type']}
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

st.markdown("### 🪐 Orbital Dynamics Profile")

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
            Speed variance of {(shell_data['max_speed'] - shell_data['min_speed']):.2f} km/s across clusters
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            Typical orbit takes ~{int(shell_data['avg_period'])} minutes
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            Altitude span: <span style="color: white; font-weight: 600;">{shell_data['altitude_span']} km</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# SHELL INTELLIGENCE (NATURAL LANGUAGE INSIGHTS)
# =============================================================================

def generate_shell_insight(data):
    insights = []
    
    # Traffic/Density Insight
    if data['satellite_count'] > 2000:
        insights.append(f"📡 <b>High-Traffic Zone:</b> With {data['satellite_count']:,} objects, this is one of the most crowded regions in LEO.")
    elif data['satellite_count'] > 1000:
        insights.append(f"🛰️ <b>Moderate Density:</b> This shell maintains a steady flow of traffic with {data['satellite_count']:,} active objects.")
    else:
        insights.append(f"🌌 <b>Quiet Corridor:</b> A relatively sparse orbital region with only {data['satellite_count']:,} satellites tracked.")
        
    # Uniformity/Span Insight
    if data['altitude_span'] < 50:
        insights.append("🎯 <b>Precision Alignment:</b> Satellites here are flying in a remarkably tight corridor (within 50km span).")
    elif data['altitude_span'] > 250:
        insights.append(f"🌊 <b>Broad Distribution:</b> Objects are scattered across a wide {data['altitude_span']:.0f}km altitude range.")
        
    # Stability Insight
    if data['risk_level'] == 'Low':
        insights.append("✅ <b>Operational Stability:</b> The overall behavior suggests a highly predictable and stable environment.")
    elif data['risk_level'] == 'High':
        insights.append("⚠️ <b>Congestion Warning:</b> The rising trend and high density increase the risk of close-approach events.")

    return insights

shell_insights = generate_shell_insight(shell_data)

st.markdown(f"""
<div style="background: linear-gradient(90deg, rgba(0, 212, 255, 0.05), rgba(124, 58, 237, 0.05)); border-left: 4px solid #00d4ff; padding: 25px; border-radius: 0 16px 16px 0; margin-bottom: 30px;">
    <div style="font-size: 0.8rem; font-weight: 800; color: #00d4ff; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px;">
        🧠 Shell Intelligence Summary
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        {''.join([f'<div style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5;">{ins}</div>' for ins in shell_insights])}
    </div>
</div>
""", unsafe_allow_html=True)

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
# =============================================================================
# SIDEBAR
# =============================================================================

# (Moved to top)
