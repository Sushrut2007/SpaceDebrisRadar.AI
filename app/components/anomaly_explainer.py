"""
Anomaly Explainer Component for SpaceDebrisRadar.AI
Translates technical anomaly data into human-readable explanations.
"""

FEATURE_EXPLANATIONS = {
    'MEAN_MOTION': {
        'title': 'Speed Change',
        'description': 'This satellite is moving at an unusual speed. It might be dropping in altitude or could have intentionally moved.',
        'icon': '🚀'
    },
    'ECCENTRICITY': {
        'title': 'Orbit Shape Shift',
        'description': 'The path of this satellite is more oval-shaped than expected, which can happen if its orbit becomes unstable.',
        'icon': '🔄'
    },
    'INCLINATION': {
        'title': 'Tilt Deviation',
        'description': 'This satellite has tilted away from its usual path compared to other satellites in the same group.',
        'icon': '📐'
    },
    'RA_OF_ASC_NODE': {
        'title': 'Path Alignment Drift',
        'description': 'The point where this satellite crosses the equator has shifted significantly from its normal position.',
        'icon': '🌐'
    },
    'ARG_OF_PERICENTER': {
        'title': 'Orbit Rotation',
        'description': 'The lowest point of this satellite\'s orbit has rotated to an unusual position.',
        'icon': '📍'
    },
    'MEAN_ANOMALY': {
        'title': 'Timing Gap',
        'description': 'The satellite isn\'t quite where we expected it to be along its path today.',
        'icon': '⏱️'
    },
    'BSTAR': {
        'title': 'Atmospheric Drag',
        'description': 'Air resistance is pulling on this satellite more than usual. This often happens if it starts tumbling.',
        'icon': '🌬️'
    },
    'ORBIT_HEIGHT': {
        'title': 'Altitude Shift',
        'description': 'This satellite is flying higher or lower than the other satellites in its group.',
        'icon': '📏'
    },
    'AGE_SINCE_LAUNCH': {
        'title': 'Launch Timing',
        'description': 'This satellite has been in space for a different amount of time than most others in this group.',
        'icon': '📅'
    },
    'UNKNOWN': {
        'title': 'Unusual Behavior',
        'description': 'Something about this satellite\'s path looks different from its peers, though we haven\'t pinned down exactly why yet.',
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
    'Strong Rising': '📈',
    'Moderate Rising': '📈',
    'Mild Rising': '↗️',
    'Flat': '➡️',
    'Calming': '📉',
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
