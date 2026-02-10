"""
Risk Model for SpaceDebrisRadar.AI

Centralized logic for determining orbital risk levels.
Architecture: "Dynamic Base + Context Modifiers (Up/Down)"
"""

def get_congestion_level(count, altitude_span_km=100.0):
    """
    Determine congestion intensity based on Linear Density (Sats/km).
    Returns Label and Boolean Flag (Legacy support, though calc uses Label now).
    """
    if altitude_span_km <= 0: altitude_span_km = 1.0
    density = count / altitude_span_km
    
    # Thresholds (Satellites per km)
    if density > 10.0:
        return "High", True 
    elif density > 2.0:
        return "Medium", False
    else:
        return "Low", False

def get_stability_level(anomaly_rate):
    """
    Determine stability based on anomaly rate.
    """
    if anomaly_rate > 0.08:   # > 8%
        return "Poor", True
    elif anomaly_rate > 0.02: # > 2%
        return "Concern", False
    else:
        return "Nominal", False # Good

def get_complexity_level(avg_inclination):
    """
    Determine complexity based on inclination.
    """
    if avg_inclination >= 60: 
        return "High", True
    elif avg_inclination >= 30:
        return "Medium", False
    else:
        return "Low", False


def classify_trend(slope, min_global_slope, max_global_slope):
    """
    Classify the trend slope.
    """
    if max_global_slope == min_global_slope:
        return "Flat", 0.0
        
    normalized = (slope - min_global_slope) / (max_global_slope - min_global_slope)
    normalized = max(-1.0, min(1.0, normalized))

    if normalized > 0.70:
        return 'High Activity', normalized
    elif normalized >= 0.30:
        return 'Active', normalized
    elif normalized >= 0.10:
        return 'Low Activity', normalized
    elif normalized >= -0.10:
        return 'Stable', abs(normalized)
    else:
        return 'Dormant', abs(normalized)


def _bump_risk(current_level, direction):
    """
    Helper to shift risk level up or down.
    Levels: Low <-> Moderate <-> High
    """
    levels = ["Low", "Moderate", "High"]
    try:
        idx = levels.index(current_level)
    except ValueError:
        return current_level
        
    if direction == "UP":
        return levels[min(idx + 1, 2)]
    elif direction == "DOWN":
        return levels[max(idx - 1, 0)]
    return current_level


def calculate_risk_level(congestion_label, stability_label, complexity_label, trend_strength, activity_fraction):
    """
    Calculate final Launch Risk Level using Modifier Logic (Up/Down).
    
    Step 1: Base Risk (From Trend & Activity)
    Step 2: Modifiers (Crowded/Unstable = UP. Empty/Stable = DOWN).
    """
    
    # --- 1. Base Risk (Dynamics) ---
    base_risk = "Low"
    
    # Rising Trend Logic
    if trend_strength > 0.30 and activity_fraction > 0.30:
        base_risk = "High" # Fast Rising + Active
    elif trend_strength > 0.00:
        if activity_fraction > 0.10:
            base_risk = "Moderate" 
        else:
            base_risk = "Low"
    else:
        base_risk = "Low"
        
        
    # --- 2. Context Modifiers ---
    final_risk = base_risk
    
    # A. Stability (The Strongest Modifier)
    if stability_label == "Poor":
        final_risk = _bump_risk(final_risk, "UP")
    elif stability_label == "Nominal":
        # Safety Credit: A well-behaved shell is safer than it looks
        final_risk = _bump_risk(final_risk, "DOWN")
        
    # B. Congestion (Physical Hazard)
    if congestion_label == "High":
        final_risk = _bump_risk(final_risk, "UP")
    elif congestion_label == "Low":
        # Safety Credit: Empty space is forgiving
        final_risk = _bump_risk(final_risk, "DOWN")
        
    # C. Complexity (Geometric Hazard)
    # Only acts as a penalty, never a credit (Geometry doesn't save you)
    if complexity_label == "High" and final_risk == "Low":
        final_risk = "Moderate"
        
    return final_risk
