"""
Context Explainer Component
Provides on-demand definitions for technical terms using "click-to-reveal" expanders.
"""
import streamlit as st

EXPLAINER_CONTENT = {
    # HOME PAGE TERMS
    'collision_risk_index': {
        'title': 'Collision Risk Index',
        'text': 'A categorical assessment (Low, Moderate, High) of current risk, based on the number of tracked objects and the frequency of anomalies within each orbital shell.'
    },
    'active_trackers': {
        'title': 'Tracked Objects',
        'text': 'The total count of man-made objects, including active satellites and debris, currently cataloged and monitored by the system.'
    },
    'orbital_regimes': {
        'title': 'Orbital Shells',
        'text': 'Altitude bands used to group satellites and analyze congestion and risk within LEO.'
    },
    
    # ORBITAL SHELLS PAGE TERMS
    'orbital_period': {
        'title': 'Orbital Period',
        'text': 'The time it takes for a satellite to complete one full revolution around the Earth. Lower altitudes have shorter periods (moving faster) while higher altitudes take longer.'
    },
    'orbital_velocity': {
        'title': 'Orbital Velocity',
        'text': 'The speed at which satellites in this shell travel to maintain their orbit. In LEO, this is typically around 7.5 to 7.8 km/s.'
    },
    'inclination': {
        'title': 'Inclination',
        'text': 'The tilt angle of the orbital plane relative to the Earth\'s equator. An inclination of 0° is equatorial, while 90° passes over the poles.'
    },
    
    # LAUNCH RISK PAGE TERMS
    'congestion': {
        'title': 'Congestion',
        'text': 'A measure of how crowded this area is. High congestion means more satellites and debris are packed into this space, increasing the chance of a collision.'
    },
    'stability': {
        'title': 'Stability',
        'text': 'How predictable the environment is. If satellites here frequently drift off course or behave unexpectedly, stability is rated as poor.'
    },
    'complexity': {
        'title': 'Geometric Complexity',
        'text': 'How "messy" the traffic flow is. High complexity means satellites are crossing paths at many different angles, making it much harder to coordinate safety.'
    }
}

def render_explainer(key, context=None):
    """
    Renders a compact, subtle expander with a single balanced explanation.
    """
    content = EXPLAINER_CONTENT.get(key)
    if not content:
        return
    
    # Custom CSS to compact the expander
    st.markdown("""
        <style>
        .compact-expander .streamlit-expanderHeader {
            font-size: 0.85rem;
            color: #64748b;
            padding: 0px 5px;
            min-height: 0px;
            line-height: 1.5;
        }
        .compact-expander .streamlit-expanderContent {
            font-size: 0.9rem;
            color: #cbd5e1;
            padding: 5px 10px;
        }
        </style>
    """, unsafe_allow_html=True)
        
    with st.expander(f"ℹ️ {content['title']}", expanded=False):
        st.markdown(f"<div style='font-size: 0.9rem; color: #a0a0b0; line-height: 1.5;'>{content['text']}</div>", unsafe_allow_html=True)
        
        if context:
             st.markdown(f"<div style='font-size: 0.85rem; color: #00d4ff; margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 4px;'><b>Context:</b> {context}</div>", unsafe_allow_html=True)
