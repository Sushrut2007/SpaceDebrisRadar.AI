"""
Anomaly Explainer Component for SpaceDebrisRadar.AI
Translates technical anomaly data into human-readable explanations.
"""

FEATURE_EXPLANATIONS = {
    'MEAN_MOTION': {
        'title': 'Speed Change',
        'description': 'Unusual orbital speed detected. The satellite may be maneuvering or experiencing decay.',
        'icon': '🚀'
    },
    'ECCENTRICITY': {
        'title': 'Orbit Shape Shift',
        'description': 'The orbit shape is more elliptical than expected for this cluster.',
        'icon': '🔄'
    },
    'INCLINATION': {
        'title': 'Tilt Deviation',
        'description': 'The orbital plane is tilted away from the cluster\'s common inclination.',
        'icon': '📐'
    },
    'RA_OF_ASC_NODE': {
        'title': 'Path Alignment Drift',
        'description': 'The equatorial crossing point (RAAN) has shifted significantly from the group norm.',
        'icon': '🌐'
    },
    'ARG_OF_PERICENTER': {
        'title': 'Orbit Rotation',
        'description': 'The orbit\'s lowest point (perigee) is rotated to an unusual position relative to the cluster.',
        'icon': '📍'
    },
    'MEAN_ANOMALY': {
        'title': 'Timing Gap',
        'description': 'The satellite\'s position along the orbit deviates from the expected timing.',
        'icon': '⏱️'
    },
    'BSTAR': {
        'title': 'Atmospheric Drag',
        'description': 'Higher than expected air resistance acting on the object.',
        'icon': '🌬️'
    },
    'ORBIT_HEIGHT': {
        'title': 'Altitude Shift',
        'description': 'The orbital altitude deviates significantly from the cluster average.',
        'icon': '📏'
    },
    'AGE_SINCE_LAUNCH': {
        'title': 'Launch Timing',
        'description': 'Launch timing discrepancy relative to the cluster majority.',
        'icon': '📅'
    },
    'UNKNOWN': {
        'title': 'Unusual Behavior',
        'description': 'Observed trajectory deviation not classified by specific parameters.',
        'icon': '⚠️'
    }
}

RISK_COLORS = {
    'Low': '#2ed573',
    'Moderate': '#ffa502', 
    'High': '#ff4757',
    'N/A': '#747d8c'
}

RISK_ICONS = {
    'Low': '🟢',
    'Moderate': '🟡',
    'High': '🔴',
    'N/A': '⚪'
}

TREND_ICONS = {
    'High Activity': '🔥',  # Was Strong Rising
    'Active': '📈',         # Was Moderate Rising
    'Low Activity': '↗️',   # Was Mild Rising
    'Stable': '➡️',        # Was Flat
    'Dormant': '📉',       # Was Calming
    'No Trend': '❓'
}


def get_anomaly_explanation(feature_name):
    """Get human-readable explanation for an anomaly."""
    return FEATURE_EXPLANATIONS.get(feature_name, FEATURE_EXPLANATIONS['UNKNOWN'])


def get_severity_label(deviation_sigma):
    """Convert deviation sigma value to severity label and color."""
    if deviation_sigma >= 5:
        return ('Critical', '#ff4757')
    elif deviation_sigma >= 3:
        return ('High', '#ff6b35')
    elif deviation_sigma >= 2:
        return ('Moderate', '#ffa502')
    else:
        return ('Low', '#2ed573')


def format_anomaly_card(row):
    """Format a single anomaly row for display."""
    feature = row.get('TOP_DEVIATING_FEATURE', 'UNKNOWN')
    deviation = row.get('DEVIATION_SIGMA', 0)
    
    explanation = get_anomaly_explanation(feature)
    severity_label, severity_color = get_severity_label(deviation)
    
    return {
        'name': row.get('OBJECT_NAME', 'Unknown'),
        'norad_id': row.get('NORAD_CAT_ID', 'N/A'),
        'cluster': row.get('CLUSTER', 'N/A'),
        'anomaly_title': explanation['title'],
        'anomaly_description': explanation['description'],
        'anomaly_icon': explanation['icon'],
        'severity_label': severity_label,
        'severity_color': severity_color,
        'deviation_sigma': round(deviation, 2)
    }


def get_risk_style(risk_level):
    """Get styling information for a risk level."""
    return {
        'color': RISK_COLORS.get(risk_level, RISK_COLORS['N/A']),
        'icon': RISK_ICONS.get(risk_level, RISK_ICONS['N/A'])
    }


def get_trend_icon(trend_type):
    """Get icon for trend type."""
    return TREND_ICONS.get(trend_type, '❓')
