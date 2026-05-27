"""
Radioactive Water Predictor — Prediction Engine
=================================================
Derives water quality parameters from TDS using chemistry correlations,
identifies likely radioactive contaminants, and calculates risk scores.
"""

import random
import math
from config import SAFE_RANGES

# ─────────────────────────────────────────────────────────────
#  1. CHEMISTRY-BASED PARAMETER DERIVATION FROM TDS
# ─────────────────────────────────────────────────────────────

def _add_noise(value, pct=0.05):
    """Add ±pct% realistic sensor noise to a derived value."""
    noise = value * random.uniform(-pct, pct)
    return round(value + noise, 2)


def derive_parameters(tds: float) -> dict:
    """
    Derive approximate water quality parameters from TDS reading.
    
    Based on established water chemistry relationships:
    - Conductivity ≈ TDS / 0.65  (standard TDS-EC ratio)
    - pH correlates with mineral content (higher TDS → slightly alkaline)
    - Hardness ≈ 40% of TDS  (Ca²⁺ + Mg²⁺ mineral fraction)
    - Nitrate ≈ 5% of TDS   (NO₃⁻ contribution)
    - Sulfate ≈ 15% of TDS  (SO₄²⁻ contribution)
    - Chloride ≈ 20% of TDS (Cl⁻ contribution)
    - Turbidity correlates with particulate load above 200 mg/L
    """
    tds = max(0, float(tds))
    
    # Electrical Conductivity (µS/cm)
    conductivity = _add_noise(tds / 0.65)
    
    # pH estimation
    # Pure water = 7.0, high TDS shifts slightly alkaline
    # Uses sigmoid-like curve bounded to realistic range [4.5, 9.5]
    ph_shift = (tds - 300) * 0.002
    ph_raw = 7.0 + ph_shift + random.uniform(-0.3, 0.3)
    ph = round(max(4.5, min(9.5, ph_raw)), 2)
    
    # Total Hardness (mg/L as CaCO₃)
    # Approximately 40% of TDS consists of hardness-causing minerals
    hardness = _add_noise(tds * 0.40)
    hardness = max(0, hardness)
    
    # Nitrate (mg/L as NO₃⁻)
    # ~5% of TDS; higher in agricultural runoff areas
    nitrate = _add_noise(tds * 0.05)
    nitrate = max(0, nitrate)
    
    # Sulfate (mg/L as SO₄²⁻)
    # ~15% of dissolved solids in typical groundwater
    sulfate = _add_noise(tds * 0.15)
    sulfate = max(0, sulfate)
    
    # Chloride (mg/L as Cl⁻)
    # ~20% of TDS in typical groundwater
    chloride = _add_noise(tds * 0.20)
    chloride = max(0, chloride)
    
    # Turbidity (NTU)
    # Correlated with particulate load; increases above 200 mg/L TDS
    turbidity_raw = max(0, (tds - 200) * 0.02) + random.uniform(0, 0.5)
    turbidity = round(max(0, turbidity_raw), 2)
    
    return {
        "tds": round(tds, 2),
        "ph": ph,
        "conductivity": conductivity,
        "hardness": hardness,
        "nitrate": nitrate,
        "sulfate": sulfate,
        "chloride": chloride,
        "turbidity": turbidity,
    }


# ─────────────────────────────────────────────────────────────
#  2. RADIOACTIVE ELEMENT DETECTION
# ─────────────────────────────────────────────────────────────

RADIOACTIVE_ELEMENTS = [
    {
        "tds_min": 0, "tds_max": 200,
        "element": "None Detected",
        "isotope": "—",
        "symbol": "—",
        "half_life": "—",
        "description": "Water appears clean with no significant radioactive indicators.",
        "health_effects": "No immediate health risk from radioactive contamination.",
        "color": "#39FF14",
    },
    {
        "tds_min": 200, "tds_max": 500,
        "element": "Radon",
        "isotope": "²²²Rn",
        "symbol": "Rn",
        "half_life": "3.82 days",
        "description": "Radon-222 is a naturally occurring radioactive gas that dissolves in groundwater. Common in granite/bedrock regions.",
        "health_effects": "Inhalation of released radon gas increases lung cancer risk. Ingestion may cause stomach cancer.",
        "color": "#FFD300",
    },
    {
        "tds_min": 500, "tds_max": 800,
        "element": "Radium",
        "isotope": "²²⁶Ra",
        "symbol": "Ra",
        "half_life": "1,600 years",
        "description": "Radium-226 correlates with high mineral content. Found in deep well water with high hardness.",
        "health_effects": "Bone cancer risk. Accumulates in bones replacing calcium. Causes anemia and cataracts.",
        "color": "#FF7518",
    },
    {
        "tds_min": 800, "tds_max": 1200,
        "element": "Uranium",
        "isotope": "²³⁸U",
        "symbol": "U",
        "half_life": "4.47 billion years",
        "description": "Uranium-238 dissolves from mineral-rich rock formations. High TDS indicates heavy mineral dissolution.",
        "health_effects": "Kidney damage (nephrotoxicity). Chemical toxicity more immediate than radioactive effects.",
        "color": "#FF4444",
    },
    {
        "tds_min": 1200, "tds_max": 1600,
        "element": "Strontium",
        "isotope": "⁹⁰Sr",
        "symbol": "Sr",
        "half_life": "28.8 years",
        "description": "Strontium-90 is a nuclear fission product. Its presence suggests nuclear fallout contamination.",
        "health_effects": "Replaces calcium in bones. Causes bone cancer and leukemia. Extremely dangerous for children.",
        "color": "#FF0040",
    },
    {
        "tds_min": 1600, "tds_max": float('inf'),
        "element": "Cesium",
        "isotope": "¹³⁷Cs",
        "symbol": "Cs",
        "half_life": "30.17 years",
        "description": "Cesium-137 indicates severe nuclear contamination (reactor accident or weapons testing).",
        "health_effects": "Distributes throughout soft tissue. Causes acute radiation syndrome, increased cancer risk across all organs.",
        "color": "#CC0000",
    },
]


def detect_radioactive_element(tds: float) -> dict:
    """Identify the most likely radioactive contaminant based on TDS level."""
    tds = max(0, float(tds))
    for elem in RADIOACTIVE_ELEMENTS:
        if elem["tds_min"] <= tds < elem["tds_max"]:
            return {
                "element": elem["element"],
                "isotope": elem["isotope"],
                "symbol": elem["symbol"],
                "half_life": elem["half_life"],
                "description": elem["description"],
                "health_effects": elem["health_effects"],
                "color": elem["color"],
            }
    return RADIOACTIVE_ELEMENTS[-1]  # Fallback to worst case


# ─────────────────────────────────────────────────────────────
#  3. RISK SCORE CALCULATION (0–100)
# ─────────────────────────────────────────────────────────────

def calculate_risk_score(params: dict) -> int:
    """
    Calculate overall radioactive contamination risk score (0–100).
    
    Weights:
    - TDS exceedance:       25%
    - pH deviation:         20%
    - Hardness exceedance:  20%
    - Nitrate exceedance:   20%
    - Sulfate + Chloride:   15%
    """
    score = 0.0
    
    # TDS contribution (25 points max)
    tds = params.get("tds", 0)
    if tds > 500:
        score += min(25, (tds - 500) / 1500 * 25)
    
    # pH deviation (20 points max)
    ph = params.get("ph", 7.0)
    ph_dev = abs(ph - 7.0)
    if ph_dev > 1.5:
        score += min(20, (ph_dev - 1.5) / 2.5 * 20)
    elif ph < 6.5 or ph > 8.5:
        score += min(15, ph_dev / 1.5 * 15)
    
    # Hardness contribution (20 points max)
    hardness = params.get("hardness", 0)
    if hardness > 200:
        score += min(20, (hardness - 200) / 600 * 20)
    
    # Nitrate contribution (20 points max)
    nitrate = params.get("nitrate", 0)
    if nitrate > 45:
        score += min(20, (nitrate - 45) / 55 * 20)
    
    # Sulfate + Chloride contribution (15 points max)
    sulfate = params.get("sulfate", 0)
    chloride = params.get("chloride", 0)
    combined_excess = max(0, sulfate - 250) + max(0, chloride - 250)
    if combined_excess > 0:
        score += min(15, combined_excess / 500 * 15)
    
    return min(100, max(0, int(round(score))))


# ─────────────────────────────────────────────────────────────
#  4. RISK LEVEL CLASSIFICATION
# ─────────────────────────────────────────────────────────────

def get_risk_level(score: int) -> dict:
    """Classify risk score into human-readable level."""
    if score < 20:
        return {"level": "Safe", "emoji": "✅", "color": "#39FF14", "advice": "Water quality is within safe limits. Regular monitoring recommended."}
    elif score < 40:
        return {"level": "Low Risk", "emoji": "🟡", "color": "#FFD300", "advice": "Minor contamination possible. Consider additional filtration."}
    elif score < 60:
        return {"level": "Moderate Risk", "emoji": "⚠️", "color": "#FF7518", "advice": "Significant contamination detected. Do NOT drink without treatment. Contact local authorities."}
    elif score < 80:
        return {"level": "High Risk", "emoji": "☢️", "color": "#FF4444", "advice": "Dangerous contamination levels. Evacuate water source immediately. Alert health authorities."}
    else:
        return {"level": "Critical", "emoji": "🚨", "color": "#CC0000", "advice": "EXTREME DANGER. Possible nuclear contamination. Evacuate area. Contact national disaster response."}


# ─────────────────────────────────────────────────────────────
#  5. COMPARISON WITH WHO SAFE RANGES
# ─────────────────────────────────────────────────────────────

def get_comparison(params: dict) -> list:
    """Compare current readings against WHO safe ranges."""
    comparison = []
    for key, safe in SAFE_RANGES.items():
        value = params.get(key, 0)
        is_safe = safe["min"] <= value <= safe["max"]
        comparison.append({
            "parameter": key.replace("_", " ").title(),
            "value": value,
            "safe_min": safe["min"],
            "safe_max": safe["max"],
            "unit": safe["unit"],
            "is_safe": is_safe,
            "status": "Safe" if is_safe else "Exceeded",
            "color": "#39FF14" if is_safe else "#FF4444",
        })
    return comparison


# ─────────────────────────────────────────────────────────────
#  6. FULL ANALYSIS PIPELINE
# ─────────────────────────────────────────────────────────────

def full_analysis(tds: float, location: str = "Unknown") -> dict:
    """
    Run the complete analysis pipeline:
    TDS → Derive Params → Detect Element → Risk Score → Comparison
    """
    params = derive_parameters(tds)
    element = detect_radioactive_element(tds)
    risk_score = calculate_risk_score(params)
    risk_level = get_risk_level(risk_score)
    comparison = get_comparison(params)
    
    return {
        "location": location,
        "parameters": params,
        "radioactive_element": element,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "comparison": comparison,
        "timestamp": None,  # Set by the caller
    }
