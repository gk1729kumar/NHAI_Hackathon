#!/usr/bin/env python3
"""
ReflectScan AI - Utilities Module
Helper functions and utilities for training and evaluation.
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Any
import json
from pathlib import Path

class DatasetBuilder:
    """
    Helper for building training datasets.
    In production, you would collect real retroreflectometer ground truth data.
    """
    
    @staticmethod
    def create_ground_truth_pair(image_path: str, rl_value: float,
                                 metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a labeled training pair.
        
        Args:
            image_path: Path to road image
            rl_value: Ground truth RL (from handheld retroreflectometer)
            metadata: Associated metadata
        
        Returns:
            Training sample dictionary
        """
        return {
            "image_path": image_path,
            "ground_truth_rl": rl_value,
            "metadata": metadata,
            "timestamp": metadata.get("timestamp"),
            "gps": metadata.get("gps"),
            "condition": metadata.get("condition")
        }
    
    @staticmethod
    def build_dataset_index(dataset_dir: str, annotation_file: str = None) -> List[Dict]:
        """
        Build dataset index from directory of images.
        
        Expected structure:
            dataset/
            ├── images/
            │   ├── img_001.jpg
            │   ├── img_002.jpg
            ... 
            └── annotations.json
        
        annotations.json format:
        {
          "img_001.jpg": {"rl": 245.3, "type": "white_marking", "condition": "day_dry"},
          "img_002.jpg": {"rl": 120.5, "type": "yellow_marking", "condition": "night_wet"},
          ...
        }
        """
        dataset = []
        dataset_path = Path(dataset_dir)
        
        # Load annotations
        annotations = {}
        if annotation_file:
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)
        
        # Index images
        image_dir = dataset_path / "images"
        if image_dir.exists():
            for img_file in sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.png")):
                anno = annotations.get(img_file.name, {})
                
                dataset.append({
                    "image_path": str(img_file),
                    "ground_truth_rl": anno.get("rl", None),
                    "marking_type": anno.get("type", "unknown"),
                    "condition": anno.get("condition", "day_dry"),
                    "split": anno.get("split", "train")  # train/val/test
                })
        
        return dataset

class MetricsCalculator:
    """Calculate evaluation metrics for model validation."""
    
    @staticmethod
    def mae(predictions: np.ndarray, ground_truth: np.ndarray) -> float:
        """Mean Absolute Error."""
        return float(np.mean(np.abs(predictions - ground_truth)))
    
    @staticmethod
    def rmse(predictions: np.ndarray, ground_truth: np.ndarray) -> float:
        """Root Mean Squared Error."""
        return float(np.sqrt(np.mean((predictions - ground_truth) ** 2)))
    
    @staticmethod
    def r2_score(predictions: np.ndarray, ground_truth: np.ndarray) -> float:
        """R² coefficient of determination."""
        ss_res = np.sum((ground_truth - predictions) ** 2)
        ss_tot = np.sum((ground_truth - np.mean(ground_truth)) ** 2)
        return float(1 - (ss_res / ss_tot))
    
    @staticmethod
    def relative_error(predictions: np.ndarray, ground_truth: np.ndarray) -> np.ndarray:
        """Relative error percentage."""
        return np.abs((predictions - ground_truth) / (ground_truth + 1e-6)) * 100
    
    @staticmethod
    def compliance_accuracy(predictions: np.ndarray, ground_truth: np.ndarray,
                            threshold: float = 100.0) -> float:
        """
        Measure how often model agrees with compliance decision.
        
        Args:
            predictions: Model predictions (RL values)
            ground_truth: Ground truth RL values
            threshold: IRC minimum RL threshold
        
        Returns:
            Accuracy (0-1)
        """
        pred_pass = predictions >= threshold
        true_pass = ground_truth >= threshold
        return float(np.mean(pred_pass == true_pass))
    
    @staticmethod
    def print_evaluation_report(predictions: np.ndarray, ground_truth: np.ndarray,
                                task_name: str = "Validation") -> None:
        """Print formatted evaluation report."""
        mae = MetricsCalculator.mae(predictions, ground_truth)
        rmse = MetricsCalculator.rmse(predictions, ground_truth)
        r2 = MetricsCalculator.r2_score(predictions, ground_truth)
        accuracy = MetricsCalculator.compliance_accuracy(predictions, ground_truth)
        
        print(f"\n{'═' * 60}")
        print(f"  {task_name.upper()} EVALUATION METRICS")
        print(f"{'═' * 60}")
        print(f"  Mean Absolute Error (MAE)  : {mae:>10.2f} mcd/m²/lux")
        print(f"  Root Mean Squared Error    : {rmse:>10.2f} mcd/m²/lux")
        print(f"  R² Score                   : {r2:>10.3f}")
        print(f"  Compliance Accuracy        : {accuracy:>10.1%}")
        print(f"{'═' * 60}\n")

class HyperparameterTuner:
    """Hyperparameter optimization utilities."""
    
    @staticmethod
    def suggest_default_params() -> Dict[str, Any]:
        """Suggest default hyperparameters for model training."""
        return {
            "learning_rate": 1e-3,
            "batch_size": 32,
            "num_epochs": 100,
            "optimizer": "adam",
            "loss_function": "mse",
            "early_stopping_patience": 15,
            "validation_split": 0.2,
            "augmentation": {
                "horizontal_flip": True,
                "brightness_jitter": 0.2,
                "contrast_jitter": 0.2,
                "gaussian_noise": 0.01,
            }
        }
    
    @staticmethod
    def grid_search_ranges() -> Dict[str, List]:
        """Define ranges for grid search."""
        return {
            "learning_rate": [1e-4, 5e-4, 1e-3, 5e-3],
            "batch_size": [16, 32, 64],
            "num_epochs": [50, 100, 200],
            "dropout_rate": [0.2, 0.3, 0.5],
        }

class ConfusionMatrixBuilder:
    """Build confusion matrices for compliance classification."""
    
    @staticmethod
    def build_compliance_matrix(predictions: np.ndarray, ground_truth: np.ndarray,
                               threshold: float = 100.0) -> Dict[str, int]:
        """
        Build compliance confusion matrix (Pass/Fail).
        
        Returns:
            {'TP': true_positives, 'FP': false_positives, ...}
        """
        pred_pass = predictions >= threshold
        true_pass = ground_truth >= threshold
        
        tp = np.sum((pred_pass) & (true_pass))
        tn = np.sum((~pred_pass) & (~true_pass))
        fp = np.sum((pred_pass) & (~true_pass))
        fn = np.sum((~pred_pass) & (true_pass))
        
        return {
            "TP": int(tp),  # Correctly predicted PASS
            "TN": int(tn),  # Correctly predicted FAIL
            "FP": int(fp),  # Incorrectly predicted PASS (false alarm)
            "FN": int(fn),  # Incorrectly predicted FAIL (missed defect)
        }
    
    @staticmethod
    def print_confusion_matrix(cm: Dict[str, int]) -> None:
        """Print formatted confusion matrix."""
        print(f"\n{'Confusion Matrix':^30}")
        print(f"{'─' * 30}")
        print(f"  {'':>10} {'Pass':<10} {'Fail':<10}")
        print(f"  {'Predicted':>10}")
        print(f"    {'Pass':<10} {cm['TP']:<10} {cm['FP']:<10}")
        print(f"    {'Fail':<10} {cm['FN']:<10} {cm['TN']:<10}")
        print(f"{'─' * 30}")
        
        # Calculate metrics
        sensitivity = cm['TP'] / (cm['TP'] + cm['FN']) if (cm['TP'] + cm['FN']) > 0 else 0
        specificity = cm['TN'] / (cm['TN'] + cm['FP']) if (cm['TN'] + cm['FP']) > 0 else 0
        accuracy = (cm['TP'] + cm['TN']) / sum(cm.values())
        
        print(f"  Sensitivity (Recall)    : {sensitivity:.1%}")
        print(f"  Specificity             : {specificity:.1%}")
        print(f"  Accuracy                : {accuracy:.1%}")

class CalibrationValidator:
    """Validate and improve calibration model."""
    
    @staticmethod
    def analyze_residuals(predictions: np.ndarray, ground_truth: np.ndarray):
        """Analyze prediction residuals for model bias."""
        residuals = ground_truth - predictions
        
        print(f"\nResidual Analysis:")
        print(f"  Mean bias      : {np.mean(residuals):>8.2f}")
        print(f"  Std deviation  : {np.std(residuals):>8.2f}")
        print(f"  Min error      : {np.min(residuals):>8.2f}")
        print(f"  Max error      : {np.max(residuals):>8.2f}")
        print(f"  % within ±10%% : {(np.abs(residuals/ground_truth) < 0.1).sum() / len(residuals) * 100:.1f}%")
        
        return residuals
    
    @staticmethod
    def identify_failure_modes(predictions: np.ndarray, ground_truth: np.ndarray,
                              conditions: List[str]) -> Dict[str, float]:
        """
        Identify conditions where model performs poorly.
        
        Args:
            predictions: Model predictions
            ground_truth: Ground truth values
            conditions: List of condition labels (e.g., "night_wet")
        
        Returns:
            MAE per condition
        """
        unique_conditions = set(conditions)
        errors_by_condition = {}
        
        for cond in unique_conditions:
            mask = np.array(conditions) == cond
            if mask.sum() > 0:
                mae = np.mean(np.abs(predictions[mask] - ground_truth[mask]))
                errors_by_condition[cond] = float(mae)
        
        # Sort by error
        sorted_errors = sorted(errors_by_condition.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nMAE by Condition:")
        for cond, mae in sorted_errors:
            print(f"  {cond:<20} : {mae:>8.2f}")
        
        return dict(sorted_errors)

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE: How to use these utilities
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("ReflectScan AI - Utilities Module")
    print("\nExample usage:")
    print("  from utils import MetricsCalculator")
    print("  mae = MetricsCalculator.mae(predictions, ground_truth)")
    print("  MetricsCalculator.print_evaluation_report(predictions, ground_truth)")
