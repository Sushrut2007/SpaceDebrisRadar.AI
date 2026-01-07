"""
Sidebar Component for SpaceDebrisRadar.AI
Centralizes the premium sidebar design across all pages.
"""

import streamlit as st

def render_sidebar():
    """Renders the consistent premium sidebar."""
    
    # Injected CSS for sidebar styling
    st.markdown("""
    <style>
        /* Hide default sidebar navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Sidebar container styling - targeting the sidebar div */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #0f0f23 100%);
        }
        
        /* Ensure sidebar content text is readable */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p {
            color: #f1f5f9;
        }
        
        /* Divider color */
        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # LOGO SECTION
        st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 1.5rem; font-weight: 800; color: white;">SDR<span style="color:#00d4ff">.AI</span></div>
            <div style="font-size: 0.7rem; color: #64748b;">VERSION 2.5.0</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # NAVIGATION SECTION
        st.markdown("### 🧭 NAVIGATION")
        st.page_link("Home.py", label="Dashboard Overview", icon="🏠")
        st.page_link("pages/1_Orbital_Shells.py", label="Shell Analytics", icon="🛰️")
        st.page_link("pages/2_Anomaly_Inspector.py", label="Anomaly Inspector", icon="🔍")
        st.page_link("pages/3_Report_Export.py", label="Report Center", icon="📄")
        st.page_link("pages/4_Settings.py", label="Settings", icon="⚙️")
        
        st.divider()
        
        # ABOUT SECTION
        st.markdown("### ℹ️ ABOUT")
        st.markdown("""
        <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.6;">
            SpaceDebrisRadar.AI is a research project exploring how we can use 
            smart computers to keep track of satellites and avoid 
            collisions in space.
            <br><br>
            Built to show what's possible for the next generation of space safety.
        </div>
        """, unsafe_allow_html=True)
