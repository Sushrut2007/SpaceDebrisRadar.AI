"""
SpaceDebrisRadar.AI - Anomaly Inspection Page
Detailed review of satellites flagged for potential issues.
"""

import streamlit as st
import sys
import os

# Add components directory to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')
sys.path.insert(0, COMPONENTS_DIR)

from data_loader import get_anomaly_data, get_top_deviating_features_summary
from anomaly_explainer import get_anomaly_explanation, get_severity_label
from sidebar import render_sidebar
from components import ui_theme

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Anomaly Inspector | SpaceDebrisRadar.AI",
    page_icon="⚠️",
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
    
    .anomaly-card {
        background: linear-gradient(145deg, rgba(50, 30, 30, 0.9), rgba(30, 20, 25, 0.95));
        border-left: 4px solid #ff6b6b;
        border-radius: 0 12px 12px 0;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    .satellite-name {
        font-size: 1.15rem;
        font-weight: 600;
        color: #e0e0e8;
    }
    
    .anomaly-type {
        color: #ff9f43;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    .anomaly-reason {
        color: #a0a0b0;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-top: 8px;
    }
    
    .meta-tag {
        display: inline-block;
        background: rgba(100, 100, 150, 0.2);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #8888aa;
        margin-right: 8px;
    }
    
    .severity-critical { border-left-color: #ff4757; }
    .severity-high { border-left-color: #ff6b35; }
    .severity-moderate { border-left-color: #ffa502; }
    .severity-low { border-left-color: #2ed573; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================

anomalies = get_anomaly_data()
total_anomalies = len(anomalies)

st.markdown(f"""
<div style="padding: 10px 0 20px 0;">
    <h1 style="font-size: 2rem; font-weight: 700; color: #e0e0e8; margin-bottom: 4px;">
        ⚠️ Anomaly Inspection
    </h1>
    <p style="color: #8888aa; font-size: 1rem;">
        Detailed review of <strong style="color: #ff6b6b;">{total_anomalies}</strong> satellites flagged for potential issues
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# FILTERS & SUMMARY
# =============================================================================

col_filter1, col_filter2, col_summary = st.columns([1, 1, 2])

with col_filter1:
    clusters = ["All Shells"] + [f"Shell {c}" for c in sorted(anomalies['CLUSTER'].unique())]
    selected_cluster = st.selectbox("Filter by Shell", clusters)

with col_filter2:
    feature_options = ["All Types"] + list(anomalies['TOP_DEVIATING_FEATURE'].unique())
    selected_feature = st.selectbox("Filter by Anomaly Type", feature_options)

# Apply filters
filtered = anomalies.copy()
if selected_cluster != "All Shells":
    cluster_id = int(selected_cluster.split()[-1])
    filtered = filtered[filtered['CLUSTER'] == cluster_id]
if selected_feature != "All Types":
    filtered = filtered[filtered['TOP_DEVIATING_FEATURE'] == selected_feature]

with col_summary:
    st.markdown(f"""
    <div style="background: rgba(40,40,70,0.4); border-radius: 12px; padding: 12px 20px; margin-top: 5px;">
        Showing <strong style="color: #00d4ff;">{len(filtered)}</strong> of {total_anomalies} anomalies
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# ANOMALY TYPE BREAKDOWN
# =============================================================================

st.markdown("### 🔍 Anomaly Type Breakdown")

feature_counts = filtered['TOP_DEVIATING_FEATURE'].value_counts()
if len(feature_counts) > 0:
    # Aggregate by display title to merge duplicates (e.g. unknown features)
    title_data = {}
    
    for feature, count in feature_counts.items():
        expl = get_anomaly_explanation(feature)
        title = expl['title'].replace(' Anomaly', '')
        
        if title in title_data:
            title_data[title]['count'] += count
        else:
            title_data[title] = {
                'count': count,
                'icon': expl['icon']
            }
            
    # Sort by count descending
    sorted_titles = sorted(title_data.items(), key=lambda item: item[1]['count'], reverse=True)
    
    # Logic: If > 5 categories, show Top 4 + "Others" so the total matches
    if len(sorted_titles) > 5:
        top_items = sorted_titles[:4]
        other_count = sum(item[1]['count'] for item in sorted_titles[4:])
        top_items.append(('Others', {'count': other_count, 'icon': '📚'}))
    else:
        top_items = sorted_titles
    
    # Display
    cols = st.columns(min(5, len(top_items)))

    for i, (title, data) in enumerate(top_items):
        with cols[i]:
            st.markdown(f"""
            <div style="background: rgba(40,40,70,0.5); border-radius: 12px; padding: 16px; text-align: center;">
                <div style="font-size: 1.5rem;">{data['icon']}</div>
                <div style="color: #e0e0e8; font-weight: 600; margin: 8px 0;">{data['count']}</div>
                <div style="color: #8888aa; font-size: 0.75rem;">{title}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No anomalies found matching the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# INDIVIDUAL SATELLITE CARDS
# =============================================================================

st.markdown(f"### 🛰️ Flagged Satellites ({len(filtered)} shown)")

# Pagination
items_per_page = 15
total_pages = max(1, (len(filtered) + items_per_page - 1) // items_per_page)

col_page, col_info = st.columns([1, 3])
with col_page:
    page = st.number_input("Page", 1, total_pages, 1)

start_idx = (page - 1) * items_per_page
end_idx = min(start_idx + items_per_page, len(filtered))

# Display satellite cards
for idx in range(start_idx, end_idx):
    row = filtered.iloc[idx]
    
    feature = row.get('TOP_DEVIATING_FEATURE', 'UNKNOWN')
    deviation = row.get('DEVIATION_SIGMA', 0)
    
    expl = get_anomaly_explanation(feature)
    severity_label, severity_color = get_severity_label(deviation)
    severity_class = f"severity-{severity_label.lower()}"
    
    st.markdown(f"""
    <div class="anomaly-card {severity_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span class="satellite-name">{row['OBJECT_NAME']}</span>
                <div class="anomaly-type" style="margin-top: 6px;">
                    {expl['icon']} {expl['title']}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: {severity_color}; color: white; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 600;">
                    {severity_label} • {deviation:.1f}σ
                </span>
            </div>
        </div>
        <div class="anomaly-reason">{expl['description']}</div>
        <div style="margin-top: 12px;">
            <span class="meta-tag">🆔 NORAD {int(row['NORAD_CAT_ID'])}</span>
            <span class="meta-tag">🌐 Shell {int(row['CLUSTER'])}</span>
            <span class="meta-tag">📊 Score {row['ANOMALY_SCORE']:.3f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Pagination footer
if total_pages > 1:
    st.markdown(f"""
    <div style="text-align: center; color: #6b6b8a; margin-top: 20px;">
        Page {page} of {total_pages} • Satellites {start_idx + 1}-{end_idx} of {len(filtered)}
    </div>
    """, unsafe_allow_html=True)
# =============================================================================
# SIDEBAR
# =============================================================================

# (Moved to top)
