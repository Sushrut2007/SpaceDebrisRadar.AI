import streamlit as st
import time
import sys
import os

# Adjust path: Add project root AND pipeline directory to sys.path
# This ensures that both 'from pipeline import X' AND 'import utils' (internal pipeline calls) work.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
pipeline_dir = os.path.join(project_root, 'pipeline')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if pipeline_dir not in sys.path:
    sys.path.insert(1, pipeline_dir)

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

    if st.button("🔄 Sync Latest Data & Re-run Pipeline", type="primary"):
        # Container for the loading state to separate it visually
        loading_container = st.empty()
        
        with loading_container.container():
            st.markdown('<div class="progress-status-container">', unsafe_allow_html=True)
            
            # Status text placeholder (using markdown for styling)
            status_placeholder = st.empty()
            
            # Progress bar
            progress_bar = st.progress(0, text="Initializing Pipeline...")
            
            try:
                # Helper to update status with style
                def update_status(text, step_num):
                    status_placeholder.markdown(f"""
                        <div class="progress-step-text">
                            <span>🚀</span>
                            <span>STAGE {step_num}/5: <span class="progress-highlight">{text}</span></span>
                        </div>
                    """, unsafe_allow_html=True)

                # 1. Setup & Imports
                update_status("Loading modules...", 0)
                
                # Explicitly import pipeline stages here
                from pipeline import utils, preprocess, clustering, anomaly_detection, trend_analysis
                
                # ----------------------------------------------------------------
                # STAGE 1: INGESTION (10%)
                # ----------------------------------------------------------------
                update_status("Fetching live TLE data from CelesTrak...", 1)
                progress_bar.progress(10, text="Ingesting Data...")
                
                raw_df = utils.fetch_dataset('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv')
                utils.save_dataset(raw_df, 'data/raw/gp.csv')
                
                # ----------------------------------------------------------------
                # STAGE 2: PREPROCESSING (30%)
                # ----------------------------------------------------------------
                update_status("Cleaning data & Engineering features...", 2)
                progress_bar.progress(30, text="Preprocessing...")
                
                sat_cleaned = preprocess.drop_rows(raw_df)
                sat_engineered = preprocess.create_features(sat_cleaned)
                sat_final_engineered = utils.drop_features(sat_engineered, 
                                        'OBJECT_ID', 'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'ELEMENT_SET_NO', 'SAT_TYPE')
                
                # Scaling
                df_for_scaling = utils.drop_features(sat_final_engineered, 'OBJECT_NAME', 'EPOCH', 'NORAD_CAT_ID')  
                scaled_df = preprocess.scale_dataset(df_for_scaling)
                
                # ----------------------------------------------------------------
                # STAGE 3: CLUSTERING (50%)
                # ----------------------------------------------------------------
                update_status("Identifying Orbital Shells (K-Means)...", 3)
                progress_bar.progress(50, text="Clustering Shells...")
                
                df_for_clustering = utils.drop_redundant_features(scaled_df)
                sat_scaled_clustered = clustering.run_KMeans(df_for_clustering)
                
                # ----------------------------------------------------------------
                # STAGE 4: ANOMALY DETECTION (70%)
                # ----------------------------------------------------------------
                update_status("Detecting Anomalous Satellites (Isolation Forest)...", 4)
                progress_bar.progress(70, text="Running Anomaly Detection...")
                
                # Use same features as K-Means (except Age)
                df_iso = sat_scaled_clustered.copy().drop(columns=['AGE_SINCE_LAUNCH']) 
                cluster_size_list, sd_list = anomaly_detection.compute_basic_stats(df_iso)
                contamination_list, n_estimator_list, max_sample_list = anomaly_detection.find_iso_paramters(sd_list, cluster_size_list)
                
                sat_unscaled_labeled, _ = anomaly_detection.train_iso_model(df_iso, 
                                                            contamination_list, n_estimator_list, max_sample_list)
                
                # Compute Deviation Profile
                anomaly_features_used = utils.drop_features(df_iso, 'CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE').columns
                final_anomalies = anomaly_detection.compute_anomaly_deviation_profile(sat_unscaled_labeled, anomaly_features_used)
                
                # Join labels
                streamlit_ready_df = sat_engineered.join(sat_unscaled_labeled[['CLUSTER', 'ANOMALY_LABEL', 'ANOMALY_SCORE']])
                utils.save_dataset(streamlit_ready_df, 'data/outputs/anomaly_clustered.csv')
                
                # Final Anomaly Formatting
                final_anomalies = final_anomalies.join(sat_final_engineered[['OBJECT_NAME', 'NORAD_CAT_ID']])
                cols = final_anomalies.columns.tolist()
                cols = ['OBJECT_NAME', 'NORAD_CAT_ID'] + [c for c in cols if c not in ['OBJECT_NAME', 'NORAD_CAT_ID']]
                final_anomalies = final_anomalies[cols]
                utils.save_dataset(final_anomalies, 'data/outputs/anomalies.csv')
                
                # ----------------------------------------------------------------
                # STAGE 5: TREND ANALYSIS (90%)
                # ----------------------------------------------------------------
                update_status("Modeling Congestion Trends...", 5)
                progress_bar.progress(90, text="Trend Analysis...")
                
                shell_time_series = trend_analysis.prepare_time_series(streamlit_ready_df)
                activity_df, cluster_models = trend_analysis.apply_linear_reg(shell_time_series)
                trend_summary = trend_analysis.trend_analysis(streamlit_ready_df, cluster_models)
                utils.save_dataset(trend_summary, 'data/outputs/trend_summary.csv')
                
                # ----------------------------------------------------------------
                # COMPLETION
                # ----------------------------------------------------------------
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
                st.error(f"Pipeline Failed: {str(e)}")
                st.info("Check usage of 'pipeline' modules in Settings.py.")
                progress_bar.empty()
            
            st.markdown('</div>', unsafe_allow_html=True) # Close container

st.markdown("---")
st.caption(f"SpaceDebrisRadar.AI v2.5.0 | Active Theme: {selected_theme}")
