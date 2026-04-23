#!/usr/bin/env python3
"""
ReflectScan AI Configuration Module
Manages system parameters, IRC standards, and calibration models.
"""

from typing import Dict, Any
import yaml
import os

# ─────────────────────────────────────────────────────────────────────────────
# IRC COMPLIANCE STANDARDS (Indian Road Congress)
# Based on IRC:67 Specification of Reflective Materials for Road Safety
# ─────────────────────────────────────────────────────────────────────────────

IRC_STANDARDS = {
    "White Pavement Marking": {
        "new": 300,
        "inservice": 100,
        "deprecated": 40,
        "unit": "mcd/m²/lux",
        "category": "white_marking"
    },
    "Yellow Pavement Marking": {
        "new": 200,
        "inservice": 75,
        "deprecated": 25,
        "unit": "mcd/m²/lux",
        "category": "yellow_marking"
    },
    "Type 1 Sign Sheeting": {
        "min": 70,
        "unit": "mcd/m²/lux",
        "category": "sign_type1"
    },
    "Type 2 Sign Sheeting": {
        "min": 150,
        "unit": "mcd/m²/lux",
        "category": "sign_type2"
    },
    "Type 3A Sign Sheeting": {
        "min": 250,
        "unit": "mcd/m²/lux",
        "category": "sign_type3a"
    },
    "Road Stud (RPM)": {
        "min": 300,
        "unit": "mcd/m²/lux",
        "category": "road_stud"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# ML CALIBRATION MODEL PARAMETERS
# Empirical coefficients for physics-based retroreflectivity estimation
# These should be fine-tuned with actual retroreflectometer data
# ─────────────────────────────────────────────────────────────────────────────

CALIBRATION_PARAMS = {
    "model_type": "physics_based_regression",  # Can be: physics_based_regression, cnn_regression, ensemble
    "version": "v1.2",
    
    # ASTM E1710 (30m observation geometry) coefficients
    "astm_observation_distance": 30.0,  # meters
    "astm_observation_angle": 0.5,      # degrees
    
    # Brightness-to-RL mapping (calibrated for Indian road conditions)
    "brightness_coefficient": 2.85,     # Linear mapping coefficient
    "brightness_exponent": 1.15,        # Non-linear exponent (gamma)
    "base_reference_rl": 250.0,         # Reference mcd/m²/lux at normalized luminance
    
    # Environmental depreciation factors
    "wet_condition_factor": 0.65,       # Water film reduces RL by ~35%
    "fog_condition_factor": 0.78,       # Fog attenuation ~22%
    "night_infrared_gain": 1.9,         # IR illumination boost (simulation)
    "contamination_factor": 0.85,       # Dust/dirt aging
    
    # Image processing thresholds
    "adaptive_threshold_block_size": 15,  # OpenCV adaptive threshold block
    "adaptive_threshold_constant": 15,    # Threshold adjustment constant
    "min_marking_coverage_pct": 0.5,      # Minimum detected marking %
    "morphological_iterations": 2,        # Closing iterations for fill
    "min_contour_area_ratio": 0.01,       # Minimum contour as % of image
    
    # Quality control thresholds
    "min_image_quality_score": 0.3,       # Reject if quality < 0.3
    "max_luminance_saturation": 240,      # Flag if markings are clipped
    "min_marking_luminance": 50,          # Flag if markings too dark
}

# ─────────────────────────────────────────────────────────────────────────────
# CONDITION PROFILES (for synthetic data generation & preprocessing)
# ─────────────────────────────────────────────────────────────────────────────

CONDITION_PROFILES = {
    "day_dry": {
        "name": "Daylight - Dry Conditions",
        "road_brightness": (80, 80, 80),
        "marking_brightness_offset": 135,
        "adaptive_filter": None,
        "brightness_scale": 1.0,
        "contrast_scale": 1.0,
        "snr_factor": 1.0,
        "season": "all"
    },
    "night_dry": {
        "name": "Night Vision - Dry Conditions",
        "road_brightness": (25, 25, 30),
        "marking_brightness_offset": 155,
        "adaptive_filter": "brightness_boost",
        "brightness_scale": 1.8,
        "contrast_scale": 1.1,
        "snr_factor": 0.85,
        "season": "all"
    },
    "day_wet": {
        "name": "Daylight - Wet/Rain Conditions",
        "road_brightness": (65, 70, 80),
        "marking_brightness_offset": 100,
        "adaptive_filter": "contrast_enhance",
        "brightness_scale": 0.9,
        "contrast_scale": 1.4,
        "snr_factor": 0.7,
        "season": "monsoon"
    },
    "night_wet": {
        "name": "Night Vision - Wet Conditions",
        "road_brightness": (18, 22, 32),
        "marking_brightness_offset": 90,
        "adaptive_filter": "brightness_and_contrast",
        "brightness_scale": 2.0,
        "contrast_scale": 1.5,
        "snr_factor": 0.6,
        "season": "monsoon"
    },
    "foggy": {
        "name": "Foggy/Low Visibility",
        "road_brightness": (130, 130, 135),
        "marking_brightness_offset": 120,
        "adaptive_filter": "dehaze",
        "brightness_scale": 1.2,
        "contrast_scale": 1.3,
        "snr_factor": 0.5,
        "season": "winter"
    },
    "heavy_contamination": {
        "name": "Heavy Dust/Contamination",
        "road_brightness": (85, 85, 85),
        "marking_brightness_offset": 80,
        "adaptive_filter": "wiener_filter",
        "brightness_scale": 1.1,
        "contrast_scale": 1.2,
        "snr_factor": 0.4,
        "season": "summer"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# MAINTENANCE RECOMMENDATION THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────

MAINTENANCE_THRESHOLDS = {
    "critical": {
        "compliance_ratio": (0, 0.7),
        "action": "IMMEDIATE",
        "days": 1,
        "icon": "🚨",
        "description": "IMMEDIATE maintenance required - Safety hazard"
    },
    "degraded": {
        "compliance_ratio": (0.7, 1.0),
        "action": "URGENT",
        "days": 7,
        "icon": "⚠️",
        "description": "URGENT maintenance - Schedule within 1 week"
    },
    "warning": {
        "compliance_ratio": (1.0, 1.3),
        "action": "SOON",
        "days": 30,
        "icon": "🔔",
        "description": "Schedule maintenance within 30 days"
    },
    "caution": {
        "compliance_ratio": (1.3, 1.7),
        "action": "SCHEDULED",
        "days": 90,
        "icon": "📅",
        "description": "Include in next routine inspection cycle (90 days)"
    },
    "healthy": {
        "compliance_ratio": (1.7, float('inf')),
        "action": "NONE",
        "days": 365,
        "icon": "✅",
        "description": "No action required - Good condition"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# REPORT AND EXPORT SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

REPORT_SETTINGS = {
    "format": ["console", "csv", "json", "html"],
    "csv_filename": "reflectscan_report.csv",
    "json_filename": "reflectscan_report.json",
    "html_filename": "reflectscan_report.html",
    "include_annotated_images": True,
    "image_output_format": "jpg",
    "image_quality": 95,
    "batch_size": 50,  # Process in batches for memory efficiency
    "enable_gps_metadata": True,
}

class ConfigManager:
    """Centralized configuration manager."""
    
    def __init__(self, config_file: str = None):
        self.irc_standards = IRC_STANDARDS
        self.calibration = CALIBRATION_PARAMS
        self.conditions = CONDITION_PROFILES
        self.maintenance = MAINTENANCE_THRESHOLDS
        self.report_settings = REPORT_SETTINGS
        
        if config_file and os.path.exists(config_file):
            self.load_from_yaml(config_file)
    
    def load_from_yaml(self, filepath: str) -> None:
        """Load configuration from YAML file."""
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'calibration' in config:
            self.calibration.update(config['calibration'])
        if 'conditions' in config:
            self.conditions.update(config['conditions'])
        if 'report_settings' in config:
            self.report_settings.update(config['report_settings'])
    
    def get_irc_standard(self, marking_type: str, condition: str = "inservice") -> Dict[str, Any]:
        """Get IRC standard for a marking type."""
        for key, standard in self.irc_standards.items():
            if key.lower() in marking_type.lower():
                if condition in standard:
                    return {"min": standard[condition], "unit": standard["unit"]}
                elif "min" in standard:
                    return {"min": standard["min"], "unit": standard["unit"]}
        return {"min": 100, "unit": "mcd/m²/lux"}  # Default fallback
    
    def get_maintenance_action(self, compliance_ratio: float) -> Dict[str, Any]:
        """Get maintenance recommendation for compliance ratio."""
        for level, threshold in self.maintenance.items():
            min_r, max_r = threshold["compliance_ratio"]
            if min_r <= compliance_ratio < max_r:
                return threshold
        return self.maintenance["healthy"]

# Global instance
config = ConfigManager()
