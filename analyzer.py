#!/usr/bin/env python3
"""
ReflectScan AI - Core Analysis Engine
Main module for retroreflectivity estimation from camera images.
"""

import cv2
import numpy as np
import math
from typing import Tuple, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from config import config, IRC_STANDARDS

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AnalysisMetrics:
    """Detailed metrics from analysis pipeline."""
    mean_luminance: float
    max_luminance: float
    min_luminance: float
    std_luminance: float
    coverage_pct: float
    marking_area_pixels: int
    total_pixels: int
    snr_ratio: float
    saturation_flag: bool
    quality_score: float

@dataclass
class AnalysisResult:
    """Complete analysis result with metadata."""
    marking_type: str
    condition: str
    estimated_rl: float
    min_required: int
    compliance_ratio: float
    status: str
    health: str
    recommendation: str
    metrics: AnalysisMetrics
    timestamp: str
    image_path: Optional[str] = None
    location_gps: Optional[Tuple[float, float]] = None

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE LOADING AND PREPROCESSING
# ─────────────────────────────────────────────────────────────────────────────

class ImageLoader:
    """Handles image loading and validation."""
    
    @staticmethod
    def load_rgb(image_path: str) -> np.ndarray:
        """Load image from disk in RGB format."""
        if not cv2.os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def validate_image(image: np.ndarray) -> Tuple[bool, str]:
        """Validate image quality and dimensions."""
        if len(image.shape) != 3 or image.shape[2] != 3:
            return False, "Image must be RGB (3 channels)"
        
        if image.shape[0] < 320 or image.shape[1] < 320:
            return False, "Image too small (min 320x320)"
        
        if image.shape[0] > 4096 or image.shape[1] > 4096:
            return False, "Image too large (max 4096x4096)"
        
        return True, "Valid"

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE PREPROCESSING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class PreprocessingEngine:
    """Condition-aware image preprocessing."""
    
    def __init__(self, condition: str = "day_dry"):
        self.condition = condition
        self.profile = config.conditions.get(condition, config.conditions["day_dry"])
    
    def process(self, image: np.ndarray) -> np.ndarray:
        """Apply condition-specific preprocessing."""
        img = image.copy().astype(np.float32) / 255.0
        
        # Apply filters based on condition profile
        filter_type = self.profile.get("adaptive_filter")
        
        if filter_type == "brightness_boost":
            img = self._boost_brightness(img)
        elif filter_type == "contrast_enhance":
            img = self._enhance_contrast(img)
        elif filter_type == "brightness_and_contrast":
            img = self._boost_brightness(img)
            img = self._enhance_contrast(img)
        elif filter_type == "dehaze":
            img = self._dehaze(img)
        elif filter_type == "wiener_filter":
            img = self._wiener_denoise(img)
        
        return (img * 255).astype(np.uint8)
    
    def _boost_brightness(self, img: np.ndarray) -> np.ndarray:
        """Boost brightness (night mode)."""
        scale = self.profile["brightness_scale"]
        return np.clip(img * scale, 0, 1)
    
    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE."""
        img_uint8 = (img * 255).astype(np.uint8)
        if len(img.shape) == 3:
            lab = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_eq = clahe.apply(l)
            lab_eq = cv2.merge([l_eq, a, b])
            result = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            result = clahe.apply(img_uint8)
        return result.astype(np.float32) / 255.0
    
    def _dehaze(self, img: np.ndarray) -> np.ndarray:
        """Dehaze using Laplacian pyramid."""
        img_uint8 = (img * 255).astype(np.uint8)
        blurred = cv2.GaussianBlur(img_uint8, (0, 0), 3)
        lapla = cv2.Laplacian(img_uint8, cv2.CV_32F)
        dehazed = cv2.convertScaleAbs(img_uint8 + lapla * 0.5)
        return dehazed.astype(np.float32) / 255.0
    
    def _wiener_denoise(self, img: np.ndarray) -> np.ndarray:
        """Apply morphological denoise."""
        img_uint8 = (img * 255).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        denoised = cv2.morphologyEx(img_uint8, cv2.MORPH_OPEN, kernel)
        return denoised.astype(np.float32) / 255.0

# ─────────────────────────────────────────────────────────────────────────────
# MARKING DETECTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class MarkingDetector:
    """Detects retroreflective road markings using advanced CV techniques."""
    
    def __init__(self):
        self.cal = config.calibration
    
    def detect(self, image: np.ndarray) -> Tuple[np.ndarray, 'AnalysisMetrics']:
        """
        Detect road markings and extract luminance statistics.
        Returns binary mask and detailed metrics.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Adaptive thresholding for bright regions
        block_size = self.cal["adaptive_threshold_block_size"]
        # Ensure block size is odd
        block_size = max(5, min(block_size, min(gray.shape) // 4))
        if block_size % 2 == 0:
            block_size += 1
        
        constant = self.cal["adaptive_threshold_constant"]
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, block_size, -constant)
        
        # Morphological cleaning
        kernel = np.ones((3, 3), np.uint8)
        for _ in range(self.cal["morphological_iterations"]):
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Contour filtering for noise rejection
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros_like(gray)
        
        min_area = self.cal["min_contour_area_ratio"] * gray.shape[0] * gray.shape[1]
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)
        
        # Fallback if no significant markings detected
        if mask.sum() == 0:
            mask = thresh
        
        # Extract luminance metrics
        metrics = self._extract_metrics(gray, mask)
        
        return mask, metrics
    
    def _extract_metrics(self, gray: np.ndarray, mask: np.ndarray) -> 'AnalysisMetrics':
        """Extract detailed luminance statistics."""
        background_mask = ~mask.astype(bool)
        marking_pixels = gray[mask > 0]
        background_pixels = gray[background_mask]
        
        if len(marking_pixels) > 0:
            mean_lum = float(np.mean(marking_pixels))
            max_lum = float(np.max(marking_pixels))
            min_lum = float(np.min(marking_pixels))
            std_lum = float(np.std(marking_pixels))
        else:
            mean_lum = max_lum = min_lum = std_lum = 0.0
        
        # SNR calculation
        if len(background_pixels) > 0:
            bg_mean = np.mean(background_pixels)
            snr = (mean_lum - bg_mean) / (np.std(background_pixels) + 1e-6)
        else:
            snr = 0.0
        
        coverage_pct = (mask.sum() / mask.size) * 100
        saturation = max_lum >= self.cal["max_luminance_saturation"]
        
        # Quality score (0-1)
        quality = min(1.0, coverage_pct / 5.0) * (1.0 if not saturation else 0.8)
        quality *= 1.0 if min_lum > self.cal["min_marking_luminance"] else 0.5
        
        return AnalysisMetrics(
            mean_luminance=mean_lum,
            max_luminance=max_lum,
            min_luminance=min_lum,
            std_luminance=std_lum,
            coverage_pct=coverage_pct,
            marking_area_pixels=int(mask.sum()),
            total_pixels=mask.size,
            snr_ratio=snr,
            saturation_flag=saturation,
            quality_score=quality
        )

# ─────────────────────────────────────────────────────────────────────────────
# ML CALIBRATION MODEL
# ─────────────────────────────────────────────────────────────────────────────

class CalibrationModel:
    """
    Physics-based retroreflectivity estimation model.
    Can be extended with trained CNN weights.
    
    Core equation:
    RL = coeff_brightness * (L_norm ^ brightness_exponent) * condition_factor
    """
    
    def __init__(self):
        self.cal = config.calibration
    
    def predict(self, metrics: 'AnalysisMetrics', condition: str) -> float:
        """
        Estimate retroreflectivity (mcd/m²/lux) from image metrics.
        
        Args:
            metrics: AnalysisMetrics from detection engine
            condition: Environmental condition (day_dry, night_wet, etc.)
        
        Returns:
            Estimated RL value
        """
        # Normalize luminance to [0, 1]
        L_norm = metrics.mean_luminance / 255.0
        
        # Core regression: RL ~ coeff * L^gamma
        gamma = self.cal["brightness_exponent"]
        base_rl = self.cal["coeff_brightness"] * (L_norm ** gamma) * self.cal["base_reference_rl"]
        
        # Apply condition-specific depreciation
        condition_factor = self._get_condition_factor(condition)
        estimated_rl = base_rl * condition_factor
        
        # Apply quality adjustments
        if metrics.quality_score < self.cal["min_image_quality_score"]:
            estimated_rl *= metrics.quality_score + 0.2  # Penalize low quality
        
        return max(0, estimated_rl)
    
    def _get_condition_factor(self, condition: str) -> float:
        """Get environmental depreciation factor."""
        if "wet" in condition:
            factor = self.cal["wet_condition_factor"]
        elif "fog" in condition:
            factor = self.cal["fog_condition_factor"]
        elif "contamination" in condition:
            factor = self.cal["contamination_factor"]
        else:
            factor = 1.0
        
        # Night-time gains (active IR)
        if "night" in condition:
            factor *= self.cal["night_infrared_gain"]
        
        return factor

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

class RetroreflectivityAnalyzer:
    """Main orchestrator for retroreflectivity analysis."""
    
    def __init__(self):
        self.preprocessor = PreprocessingEngine()
        self.detector = MarkingDetector()
        self.model = CalibrationModel()
    
    def analyze(self, image: np.ndarray, condition: str = "day_dry",
                marking_type: str = "White Pavement Marking (In-Service)",
                image_path: Optional[str] = None,
                location_gps: Optional[Tuple[float, float]] = None) -> 'AnalysisResult':
        """
        Complete analysis pipeline.
        
        Args:
            image: RGB numpy array
            condition: Environmental condition
            marking_type: Type of marking
            image_path: Source image path (for logging)
            location_gps: GPS coordinates
        
        Returns:
            AnalysisResult with full details
        """
        # Validate image
        valid, msg = ImageLoader.validate_image(image)
        if not valid:
            raise ValueError(f"Invalid image: {msg}")
        
        # Preprocess
        self.preprocessor.condition = condition
        processed = self.preprocessor.process(image)
        
        # Detect markings
        mask, metrics = self.detector.detect(processed)
        
        # Estimate RL
        estimated_rl = self.model.predict(metrics, condition)
        estimated_rl = round(estimated_rl, 1)
        
        # Check compliance
        irc_std = config.get_irc_standard(marking_type)
        min_required = irc_std["min"]
        compliance_ratio = round(estimated_rl / min_required, 2) if min_required > 0 else 0
        
        # Determine health status
        status = "PASS ✅" if estimated_rl >= min_required else "FAIL ❌"
        health = self._get_health_status(compliance_ratio)
        
        # Get recommendation
        maint = config.get_maintenance_action(compliance_ratio)
        recommendation = f"{maint['icon']} {maint['description']}"
        
        return AnalysisResult(
            marking_type=marking_type,
            condition=condition.replace('_', ' ').title(),
            estimated_rl=estimated_rl,
            min_required=min_required,
            compliance_ratio=compliance_ratio,
            status=status,
            health=health,
            recommendation=recommendation,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
            image_path=image_path,
            location_gps=location_gps
        )
    
    @staticmethod
    def _get_health_status(compliance_ratio: float) -> str:
        """Map compliance ratio to health status."""
        if compliance_ratio >= 2.0:
            return "Excellent"
        elif compliance_ratio >= 1.5:
            return "Good"
        elif compliance_ratio >= 1.0:
            return "Acceptable"
        elif compliance_ratio >= 0.7:
            return "Degraded"
        else:
            return "Critical"
