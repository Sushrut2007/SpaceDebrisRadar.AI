import streamlit as st
import time
import sys
import os

# Add relevant directories to sys.path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(APP_DIR)
COMPONENTS_DIR = os.path.join(APP_DIR, 'components')
PIPELINE_DIR = os.path.join(PROJECT_ROOT, 'pipeline')

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(1, APP_DIR)
if COMPONENTS_DIR not in sys.path:
    sys.path.insert(2, COMPONENTS_DIR)
if PIPELINE_DIR not in sys.path:
    sys.path.insert(3, PIPELINE_DIR)

from app.components import ui_theme
from app.components import data_loader
# Try obtaining pipeline main function. 
# Note: We import it inside the function or here if we are sure it works.
pipeline_error = None
try:
    from pipeline import run_pipeline
except Exception as e:
    run_pipeline = None
    pipeline_error = str(e)

st.set_page_config(page_title="Settings - SpaceDebrisRadar", page_icon="⚙️", layout="wide")

from app.components.sidebar import render_sidebar

# Apply Theme
ui_theme.apply_theme()
render_sidebar()

st.title("⚙️ Application Settings")

# --- SECTION 1: VISUAL IDENTITY ---
st.markdown("### 🎨 Visual Identity")
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    Customize the look and feel of the dashboard. 
    Choose a theme that suits your presentation environment.
    """)

with col2:
    themes = ui_theme.get_themes()
    current_theme = st.session_state.get("theme", "Slate Minimal")
    
    # Theme Selector
    # If the current theme is invalid (from previous session), default to Slate Minimal
    if current_theme not in themes:
        current_theme = "Slate Minimal"
        st.session_state.theme = current_theme
        
    selected_theme = st.selectbox("Select Theme", themes, index=themes.index(current_theme))
    
    if selected_theme != current_theme:
        st.session_state.theme = selected_theme
        st.rerun()

    # Preview Card
    st.markdown(f"""
    <div class="glass-card">
        <h4>Theme Preview: {selected_theme}</h4>
        <p>This is how cards and text will look.</p>
        <p style="font-size: 24px; font-weight: bold;">12,345 Satellites</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- SECTION 2: DATA MANAGEMENT ---
# --- SECTION 2: DATA MANAGEMENT ---
st.markdown("### 📡 Data Management")
col3, col4 = st.columns([1, 2])

with col3:
    st.markdown("""
    **Live Data Sync**
    
    Fetch the latest orbital data from Celestrak (CelesTrak.org) and re-run the entire analysis pipeline.
    """)

with col4:
    # Custom CSS for Premium Progress Bar
    st.markdown("""
    <style>
        /* Animated Gradient Progress Bar */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(90deg, #4cc9f0 0%, #4361ee 50%, #7209b7 100%);
            box-shadow: 0 0 10px rgba(76, 201, 240, 0.5);
            transition: width 0.5s ease-in-out;
        }
        
        /* Progress Container Text */
        .progress-status-container {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            margin-bottom: 10px;
            animation: fadeIn 0.5s ease-out;
        }
        
        .progress-step-text {
            font-family: 'SF Pro Display', 'Inter', monospace;
            font-size: 14px;
            color: #e0e0e0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .progress-highlight {
            color: #4cc9f0;
            font-weight: 600;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    """, unsafe_allow_html=True)

    # Secret Management
    admin_pass = st.secrets.get("ADMIN_PASSWORD", "dev_mode_pass") # Default for local dev if not in secrets
    github_token = st.secrets.get("GITHUB_TOKEN")
    repo_name = "Sushrut2007/SpaceDebrisRadar.AI"
    workflow_filename = "actions.yml"

    st.markdown("---")
    st.markdown("#### 🔐 Admin Access")
    pwd_input = st.text_input("Enter Admin Password to Unlock", type="password")
    
    unlocked = (pwd_input == admin_pass)
    
    if not unlocked and pwd_input:
        st.error("Incorrect Password. Access Denied.")

    if st.button("🔄 Sync Latest Data & Re-run Pipeline", type="primary", disabled=not unlocked):
        # Container for the loading state to separate it visually
        loading_container = st.empty()
        
        with loading_container.container():
            st.markdown('<div class="progress-status-container">', unsafe_allow_html=True)
            
            # Status text placeholder (using markdown for styling)
            status_placeholder = st.empty()
            
            # Progress bar
            progress_bar = st.progress(0, text="Initializing Pipeline...")
            
            try:
                # Helper to update status with style (passed to trigger function)
                def update_status_ui(text, step_num):
                    status_placeholder.markdown(f"""
                        <div class="progress-step-text">
                            <span>🚀</span>
                            <span>STAGE {step_num}/5: <span class="progress-highlight">{text}</span></span>
                        </div>
                    """, unsafe_allow_html=True)

                if github_token:
                    # --- REMOTE EXECUTION (CLOUD) ---
                    from app.components import pipeline_trigger
                    
                    success = pipeline_trigger.trigger_github_workflow(
                        repo_name=repo_name,
                        workflow_filename=workflow_filename,
                        github_token=github_token,
                        update_status_func=update_status_ui,
                        progress_bar=progress_bar
                    )
                    
                    if success:
                        st.toast("Pipeline Update Completed Successfully!", icon="✅")
                        st.markdown("""
                            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 15px; border-radius: 8px; margin-top: 10px;">
                                <h4 style="color: #10b981; margin: 0;">✅ Remote Analysis Complete</h4>
                                <p style="color: #e0e0e0; margin-top: 5px;">
                                    Process finished. The dashboard will auto-refresh shortly with the latest data.
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        time.sleep(4)
                        st.rerun()

                else:
                    # --- LOCAL EXECUTION (DEV) ---
                    update_status_ui("Running Local Pipeline...", 1)
                    progress_bar.progress(30, text="Processing...")
                    
                    # Ensure pipeline module is available
                    if run_pipeline is None:
                        raise ImportError(f"Could not import run_pipeline. Error: {pipeline_error}")
                        
                    run_pipeline.main()
                    
                    # COMPLETION
                    data_loader.clear_cache()
                    progress_bar.progress(100, text="Pipeline Execution Complete!")
                    
                    st.markdown("""
                        <div style="background: rgba(76, 201, 240, 0.1); border: 1px solid #4cc9f0; padding: 10px; border-radius: 8px; margin-top: 10px;">
                            <span style="color: #4cc9f0; font-weight: bold;">✅ Sync Complete!</span>
                            <span style="color: #e0e0e0;"> All systems updated. Reloading...</span>
                        </div>
                    """, unsafe_allow_html=True)

                    time.sleep(2)
                    st.rerun()

            except Exception as e:
                st.error(f"Pipeline Execution Failed: {str(e)}")
                st.info("If running in cloud, ensure GITHUB_TOKEN is set in secrets. If local, check 'pipeline' module path.")
                progress_bar.empty()
            
            st.markdown('</div>', unsafe_allow_html=True) # Close container

st.markdown("---")
st.caption(f"SpaceDebrisRadar.AI v2.5.0 | Active Theme: {selected_theme}")
