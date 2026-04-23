#!/usr/bin/env python3
"""
ReflectScan AI - Synthetic Data Generator
Generates realistic synthetic road images for testing and demos.
"""

import cv2
import numpy as np
from typing import Optional
from config import config

class SyntheticRoadGenerator:
    """Generates synthetic road marking images for demo/testing."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
    
    def generate(self, condition: str = "day_dry") -> np.ndarray:
        """
        Generate synthetic road image with markings.
        
        Args:
            condition: Environmental condition (day_dry, night_wet, etc.)
        
        Returns:
            RGB numpy array
        """
        profile = config.conditions.get(condition, config.conditions["day_dry"])
        
        # Initialize road surface
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        road_color = profile["road_brightness"]
        img[:, :] = road_color
        
        # Add road texture
        self._add_asphalt_texture(img, condition)
        
        # Calculate marking brightness
        marking_offset = profile["marking_brightness_offset"]
        
        # Draw markings
        self._draw_edge_lines(img, marking_offset)
        self._draw_center_line(img, marking_offset)
        self._draw_road_studs(img, marking_offset)
        
        # Add environmental effects
        self._add_environmental_effects(img, condition)
        
        # Add realistic noise
        self._add_camera_noise(img, condition)
        
        return img
    
    def _add_asphalt_texture(self, img: np.ndarray, condition: str) -> None:
        """Add realistic asphalt surface texture."""
        noise = np.random.randint(-15, 15, img.shape, dtype=np.int16)
        img_int = img.astype(np.int16) + noise
        np.clip(img_int, 0, 255, out=img_int)
        img[:] = img_int.astype(np.uint8)
    
    def _draw_edge_lines(self, img: np.ndarray, brightness: int) -> None:
        """Draw white edge lines."""
        profile = config.conditions.get("day_dry")
        offset = profile["marking_brightness_offset"]
        bright = min(brightness + offset, 255)
        
        # Left edge line
        cv2.rectangle(img, (100, 0), (115, self.height), (bright, bright, bright), -1)
        # Right edge line
        cv2.rectangle(img, (self.width - 115, 0), (self.width - 100, self.height),
                     (bright, bright, bright), -1)
    
    def _draw_center_line(self, img: np.ndarray, brightness: int) -> None:
        """Draw yellow center line (dashed)."""
        profile = config.conditions.get("day_dry")
        offset = profile["marking_brightness_offset"]
        bright = min(brightness + offset - 30, 255)
        yellow = (bright, bright, 40)
        
        dash_length = 70
        gap = 50
        
        for y in range(0, self.height, dash_length + gap):
            cv2.rectangle(img, (self.width // 2 - 8, y),
                         (self.width // 2 + 8, min(y + dash_length, self.height)),
                         yellow, -1)
    
    def _draw_road_studs(self, img: np.ndarray, brightness: int) -> None:
        """Draw retroreflective road studs (RPM)."""
        profile = config.conditions.get("day_dry")
        offset = profile["marking_brightness_offset"]
        bright = min(brightness + offset + 20, 255)
        stud_color = (bright, min(bright - 10, 255), 50)
        
        for y in range(100, self.height, 160):
            cv2.circle(img, (self.width // 2, y), 10, stud_color, -1)
    
    def _add_environmental_effects(self, img: np.ndarray, condition: str) -> None:
        """Add weather-specific visual effects."""
        if "wet" in condition:
            # Water droplets and reflections
            for _ in range(20):
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                cv2.circle(img, (x, y), np.random.randint(2, 8),
                          (200, 205, 210), -1)
                cv2.circle(img, (x, y), np.random.randint(8, 12),
                          (180, 185, 190), 2)
        
        if "fog" in condition:
            # White fog overlay
            fog = np.ones_like(img) * 180
            img[:] = cv2.addWeighted(img, 0.6, fog, 0.4, 0)
        
        if "contamination" in condition:
            # Dust/dirt particles
            for _ in range(50):
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                cv2.circle(img, (x, y), 1, (60, 60, 60), -1)
    
    def _add_camera_noise(self, img: np.ndarray, condition: str) -> None:
        """Add realistic camera noise."""
        profile = config.conditions.get(condition, config.conditions["day_dry"])
        snr_factor = profile["snr_factor"]
        
        # Gaussian noise inversely proportional to SNR
        noise_level = int(20 * (1 - snr_factor))
        noise = np.random.normal(0, noise_level, img.shape)
        
        img_f = img.astype(np.float32) + noise
        img[:] = np.clip(img_f, 0, 255).astype(np.uint8)

# ─────────────────────────────────────────────────────────────────────────────
# DEMO BATCH GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class BatchDemoGenerator:
    """Generates realistic batch scenarios for highway scanning."""
    
    def __init__(self):
        self.generator = SyntheticRoadGenerator()
    
    def create_test_cases(self, num_sections: int = 5):
        """
        Generate realistic test cases simulating highway scan.
        
        Returns:
            List of (condition, marking_type, location_km, image)
        """
        test_cases = [
            ("day_dry", "White Pavement Marking (New)", "KM 0+200"),
            ("night_dry", "White Pavement Marking (In-Service)", "KM 1+500"),
            ("day_wet", "Yellow Pavement Marking (New)", "KM 2+100"),
            ("foggy", "Road Stud (RPM)", "KM 3+800"),
            ("night_wet", "Type 3A Sign Sheeting", "KM 4+300"),
        ]
        
        results = []
        for condition, marking, location in test_cases[:num_sections]:
            img = self.generator.generate(condition)
            # Simulate some variation in image quality
            if np.random.random() > 0.7:
                # Add some motion blur occasionally
                kernel_size = 5
                kernel = np.ones((kernel_size, kernel_size)) / (kernel_size ** 2)
                img = cv2.filter2D(img, -1, kernel)
            
            results.append((condition, marking, location, img))
        
        return results
