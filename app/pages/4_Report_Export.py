"""
SpaceDebrisRadar.AI - Report Preview and Export Page
Generate dynamic PDF reports using ReportLab.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import sys
import os

# Add components directory to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')
sys.path.insert(0, COMPONENTS_DIR)

from data_loader import (
    get_system_metrics,
    get_cluster_summary,
    get_anomaly_data,
    load_trend_summary
)
from anomaly_explainer import get_risk_style, get_anomaly_explanation
from sidebar import render_sidebar
from components import ui_theme

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Report Export | SpaceDebrisRadar.AI",
    page_icon="📄",
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
    
    .report-section {
        background: linear-gradient(145deg, rgba(30, 30, 50, 0.9), rgba(20, 20, 35, 0.95));
        border: 1px solid rgba(100, 100, 150, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
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
        📄 Report Export
    </h1>
    <p style="color: #8888aa; font-size: 1rem;">
        Generate and download comprehensive PDF reports
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# LOAD DATA
# =============================================================================

metrics = get_system_metrics()
cluster_summary = get_cluster_summary()
anomalies = get_anomaly_data()
trend_summary = load_trend_summary()

# =============================================================================
# DYNAMIC INSIGHTS GENERATION
# =============================================================================

def generate_dynamic_insights():
    """Generate logical insights based on the data."""
    insights = []
    
    # Overall risk insight
    if metrics['overall_risk'] == 'High':
        insights.append("⚠️ WATCH OUT: The risk of a collision is HIGH right now. Several areas are becoming dangerously crowded.")
    elif metrics['overall_risk'] == 'Moderate':
        insights.append("⚡ ADVISORY: Collision risk is moderate. Some areas should be double-checked before launching anything new.")
    else:
        insights.append("✅ CLEAR: Collision risk is low. Things look pretty quiet across the orbital shells today.")
    
    # High-risk shells
    high_risk_shells = trend_summary[trend_summary['LAUNCH_RISK_LEVEL'] == 'High']
    if len(high_risk_shells) > 0:
        shell_ids = ', '.join([str(int(s)) for s in high_risk_shells['CLUSTER_ID'].values])
        insights.append(f"🔴 Danger zones: Shells {shell_ids} are much more crowded than usual.")
    
    # Most congested
    most_congested = cluster_summary.loc[cluster_summary['satellite_count'].idxmax()]
    insights.append(f"🔥 Most congested: Shell {int(most_congested['cluster_id'])} with {most_congested['satellite_count']:,} satellites ({most_congested['anomaly_rate']}% anomaly rate).")
    
    # Anomaly patterns
    top_anomaly_type = anomalies['TOP_DEVIATING_FEATURE'].value_counts().index[0]
    top_count = anomalies['TOP_DEVIATING_FEATURE'].value_counts().iloc[0]
    expl = get_anomaly_explanation(top_anomaly_type)
    insights.append(f"📊 Primary anomaly pattern: {expl['title']} ({top_count} occurrences) - {expl['description']}")
    
    # Trend analysis
    rising = len(trend_summary[trend_summary['TREND_TYPE'].str.contains('Rising', na=False)])
    if rising >= 3:
        insights.append(f"📈 {rising} of 5 shells are getting more crowded. We recommend keeping a close watch on these areas.")
    
    return insights


# =============================================================================
# PDF GENERATION
# =============================================================================

def generate_pdf_report():
    """Generate a professional PDF report using ReportLab."""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#1a1a2e'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#2d2d5a'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, spaceAfter=8)
    insight_style = ParagraphStyle('Insight', parent=styles['Normal'], fontSize=10, spaceAfter=6, leftIndent=10, textColor=colors.HexColor('#333333'))
    
    elements = []
    
    # Title
    elements.append(Paragraph("SpaceDebrisRadar.AI", title_style))
    elements.append(Paragraph("Low Earth Orbit Analysis Report", ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.grey)))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ParagraphStyle('Date', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.grey)))
    elements.append(Spacer(1, 30))
    
    # Executive Summary
    elements.append(Paragraph("1. Executive Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Satellites Analyzed', f"{metrics['total_satellites']:,}"],
        ['Orbital Shells', str(metrics['total_shells'])],
        ['Anomalies Detected', f"{metrics['total_anomalies']:,} ({metrics['anomaly_rate']}%)"],
        ['Overall Launch Risk', metrics['overall_risk']]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d5a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Key Insights
    elements.append(Paragraph("2. Key Insights", heading_style))
    insights = generate_dynamic_insights()
    for insight in insights:
        elements.append(Paragraph(f"• {insight}", insight_style))
    elements.append(Spacer(1, 20))
    
    # Shell Analysis
    elements.append(Paragraph("3. Orbital Shell Analysis", heading_style))
    
    shell_data = [['Shell', 'Satellites', 'Anomalies', 'Avg Alt (km)', 'Trend', 'Risk']]
    for _, row in cluster_summary.iterrows():
        shell_data.append([
            f"Shell {int(row['cluster_id'])}",
            f"{row['satellite_count']:,}",
            f"{row['anomaly_count']} ({row['anomaly_rate']}%)",
            f"{row['avg_altitude']:.0f}",
            row['trend_type'],
            row['risk_level']
        ])
    
    shell_table = Table(shell_data, colWidths=[60, 70, 90, 70, 100, 70])
    shell_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d5a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f8f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(shell_table)
    elements.append(Spacer(1, 20))
    
    # Top Anomalies
    elements.append(Paragraph("4. Top Anomalies (First 15)", heading_style))
    
    anomaly_data = [['Satellite', 'Shell', 'Type', 'Severity']]
    for _, row in anomalies.head(15).iterrows():
        expl = get_anomaly_explanation(row.get('TOP_DEVIATING_FEATURE', 'UNKNOWN'))
        dev = row.get('DEVIATION_SIGMA', 0)
        severity = 'Critical' if dev >= 5 else 'High' if dev >= 3 else 'Moderate' if dev >= 2 else 'Low'
        anomaly_data.append([
            row['OBJECT_NAME'][:20],
            str(int(row['CLUSTER'])),
            expl['title'].replace(' Anomaly', '')[:18],
            f"{severity} ({dev:.1f}σ)"
        ])
    
    anomaly_table = Table(anomaly_data, colWidths=[120, 50, 140, 100])
    anomaly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5a2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(anomaly_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    elements.append(Paragraph("─" * 60, normal_style))
    elements.append(Paragraph("Generated by SpaceDebrisRadar.AI • Data source: CelesTrak", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =============================================================================
# UI
# =============================================================================

col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown("### 📋 Report Preview")
    
    st.markdown(f"""
    <div class="report-section">
        <h4 style="color: #e0e0e8; margin-bottom: 12px;">Executive Summary</h4>
        <p style="color: #a0a0b0;">
            <strong>{metrics['total_satellites']:,}</strong> satellites analyzed across 
            <strong>{metrics['total_shells']}</strong> orbital shells.<br>
            <strong style="color: {'#ff6b6b' if metrics['overall_risk']=='High' else '#ffa502' if metrics['overall_risk']=='Moderate' else '#2ed573'};">
            {metrics['overall_risk']}</strong> overall launch risk.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 💡 Key Insights")
    insights = generate_dynamic_insights()
    for insight in insights:
        st.markdown(f"<div style='color: #c0c0d0; padding: 4px 0; font-size: 0.9rem;'>{insight}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("### 📥 Download")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Generate PDF
    pdf_buffer = generate_pdf_report()
    
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_buffer,
        file_name=f"SpaceDebrisRadar_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CSV exports
    st.download_button(
        label="📊 Shell Summary (CSV)",
        data=cluster_summary.to_csv(index=False),
        file_name=f"shell_summary_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.download_button(
        label="⚠️ Anomaly List (CSV)",
        data=anomalies.to_csv(index=False),
        file_name=f"anomalies_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
# =============================================================================
# SIDEBAR
# =============================================================================

# (Moved to top)
