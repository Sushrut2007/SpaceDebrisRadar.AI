
import streamlit as st
import textwrap

def apply_theme():
    """
    Apply the selected theme from session state to the current page.
    If no theme is selected, defaults to 'Slate Minimal'.
    """
    if "theme" not in st.session_state:
        st.session_state.theme = "Slate Minimal"
    
    theme = st.session_state.theme
    
    # Base CSS (Glassmorphism & Layouts)
    base_css = textwrap.dedent("""
    <style>
        /* Global Background & Text */
        .stApp {
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: cover;
        }
        
        /* Glassmorphism Cards - Universal Clear Style */
        .glass-card {
            background: rgba(17, 25, 40, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        /* Metric Styling */
        div[data-testid="stMetricValue"] {
            font-family: 'SF Pro Display', 'Inter', sans-serif;
            font-weight: 600;
        }
    </style>
    """)
    
    # Theme Specific CSS
    theme_css = ""
    
    if theme == "Slate Minimal":
        theme_css = textwrap.dedent("""
        <style>
            .stApp {
                background-color: #0f1116;
                /* Subtle radial gradient for depth */
                background-image: radial-gradient(circle at 50% 0%, #1c2333 0%, #0f1116 70%);
                color: #e6e6e6;
            }
            h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 500; }
            div[data-testid="stMetricValue"] { color: #60a5fa !important; } /* Blue-400 */
            div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
            .glass-card {
                background: rgba(30, 41, 59, 0.4); /* Slate-800 low opacity */
                border: 1px solid rgba(148, 163, 184, 0.1);
            }
            /* Custom Scrollbar */
            ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        </style>
        """)
        
        
    elif theme == "Oceanic Pro":
        theme_css = textwrap.dedent("""
        <style>
            .stApp {
                background: linear-gradient(to bottom right, #001e2b, #001219);
                color: #d8f3dc;
            }
            h1, h2, h3 { color: #4cc9f0 !important; }
            div[data-testid="stMetricValue"] { color: #4cc9f0 !important; }
            .glass-card {
                background: rgba(0, 30, 43, 0.6);
                border: 1px solid rgba(76, 201, 240, 0.15);
            }
        </style>
        """)
        
    elif theme == "Mint & Charcoal":
        theme_css = textwrap.dedent("""
        <style>
            .stApp {
                background-color: #121212;
                background-image: repeating-linear-gradient(45deg, #121212 0px, #121212 10px, #151515 10px, #151515 20px);
                color: #e0e0e0;
            }
            h1, h2, h3 { color: #69f0ae !important; }
            div[data-testid="stMetricValue"] { color: #69f0ae !important; }
            .glass-card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(105, 240, 174, 0.2);
            }
        </style>
        """)

    # Inject
    st.markdown(base_css + theme_css, unsafe_allow_html=True) 

def get_themes():
    return ["Slate Minimal", "Oceanic Pro", "Mint & Charcoal"]
