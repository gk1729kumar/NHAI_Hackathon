#!/usr/bin/env python3
"""
ReflectScan AI - Reporting & Export Module
Generates comprehensive reports, exports data, and creates visualizations.
"""

import cv2
import numpy as np
import pandas as pd
import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from analyzer import AnalysisResult, MarkingDetector, PreprocessingEngine

class ReportGenerator:
    """Generates text reports for individual analyses."""
    
    @staticmethod
    def generate_console_report(result: 'AnalysisResult') -> str:
        """Generate formatted console report."""
        sep = "═" * 70
        lines = [
            "",
            sep,
            "   ReflectScan AI – Retroreflectivity Analysis Report",
            "   NHAI 6th Innovation Hackathon | Production Prototype",
            sep,
            f"  📋 Analysis Date      : {result.timestamp}",
            f"  🛣️  Marking Type       : {result.marking_type}",
            f"  🌤️  Condition          : {result.condition}",
            f"  📍 Image Source       : {result.image_path or 'Synthetic'}",
            f"  {('  GPS Position       : ' + f'{result.location_gps}') if result.location_gps else ''}",
            "─" * 70,
            "  📊 DETECTION METRICS:",
            f"    Mean Luminance    : {result.metrics.mean_luminance:.1f} / 255",
            f"    Max Luminance     : {result.metrics.max_luminance:.1f} / 255",
            f"    Std Deviation     : {result.metrics.std_luminance:.1f}",
            f"    Detection Coverage: {result.metrics.coverage_pct:.2f}% of frame",
            f"    Marking Area      : {result.metrics.marking_area_pixels:,} pixels",
            f"    Signal-to-Noise   : {result.metrics.snr_ratio:.2f}",
            f"    Saturation Flag   : {'YES ⚠️' if result.metrics.saturation_flag else 'No'}",
            f"    Image Quality     : {result.metrics.quality_score:.1%}",
            "─" * 70,
            "  🎯 RETROREFLECTIVITY MEASUREMENT:",
            f"    Estimated RL      : {result.estimated_rl:>7.1f} mcd/m²/lux",
            f"    IRC Minimum       : {result.min_required:>7d} mcd/m²/lux",
            f"    Compliance Ratio  : {result.compliance_ratio:>7.2f}× minimum",
            f"    Condition Health  : {result.health}",
            f"    STATUS            : {result.status}",
            "─" * 70,
            "  🔧 MAINTENANCE RECOMMENDATION:",
            f"    {result.recommendation}",
            sep,
            ""
        ]
        
        # Filter empty lines
        return "\n".join([l for l in lines if l.strip() != "" or l == ""])
    
    @staticmethod
    def generate_json_report(results: List['AnalysisResult']) -> str:
        """Generate JSON export."""
        data = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "total_analyses": len(results),
                "passed": sum(1 for r in results if "PASS" in r.status),
                "failed": sum(1 for r in results if "FAIL" in r.status),
            },
            "analyses": [
                {
                    "timestamp": r.timestamp,
                    "marking_type": r.marking_type,
                    "condition": r.condition,
                    "estimated_rl": r.estimated_rl,
                    "min_required": r.min_required,
                    "compliance_ratio": r.compliance_ratio,
                    "status": r.status,
                    "health": r.health,
                    "location_gps": r.location_gps,
                    "metrics": {
                        "mean_luminance": r.metrics.mean_luminance,
                        "max_luminance": r.metrics.max_luminance,
                        "coverage_pct": r.metrics.coverage_pct,
                        "quality_score": r.metrics.quality_score,
                    }
                }
                for r in results
            ]
        }
        return json.dumps(data, indent=2)

class DataExporter:
    """Exports analysis results to various formats."""
    
    @staticmethod
    def to_csv(results: List['AnalysisResult'], filepath: str) -> None:
        """Export results to CSV."""
        rows = []
        for r in results:
            rows.append({
                "Timestamp": r.timestamp,
                "Marking_Type": r.marking_type,
                "Condition": r.condition,
                "Estimated_RL": r.estimated_rl,
                "Min_Required": r.min_required,
                "Compliance_Ratio": r.compliance_ratio,
                "Status": r.status,
                "Health": r.health,
                "Mean_Luminance": f"{r.metrics.mean_luminance:.1f}",
                "Coverage_PCT": f"{r.metrics.coverage_pct:.2f}",
                "Quality_Score": f"{r.metrics.quality_score:.1%}",
                "Recommendation": r.recommendation,
                "GPS": r.location_gps or "N/A",
                "Image_Path": r.image_path or "Synthetic",
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
        print(f"✅ CSV report saved: {filepath}")
    
    @staticmethod
    def to_json(results: List['AnalysisResult'], filepath: str) -> None:
        """Export results to JSON."""
        content = ReportGenerator.generate_json_report(results)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ JSON report saved: {filepath}")
    
    @staticmethod
    def to_html(results: List['AnalysisResult'], filepath: str) -> None:
        """Export results to HTML."""
        html_content = DataExporter._build_html(results)
        with open(filepath, 'w') as f:
            f.write(html_content)
        print(f"✅ HTML report saved: {filepath}")
    
    @staticmethod
    def _build_html(results: List['AnalysisResult']) -> str:
        """Build HTML report content."""
        passed = sum(1 for r in results if "PASS" in r.status)
        failed = sum(1 for r in results if "FAIL" in r.status)
        
        table_rows = ""
        for r in results:
            status_color = "green" if "PASS" in r.status else "red"
            table_rows += f"""
            <tr style="background: {'#f0fdf4' if 'PASS' in r.status else '#fef2f2'}">
                <td>{r.timestamp}</td>
                <td>{r.marking_type}</td>
                <td>{r.condition}</td>
                <td><strong>{r.estimated_rl}</strong></td>
                <td>{r.min_required}</td>
                <td>{r.compliance_ratio}</td>
                <td style="color: {status_color};"><b>{r.status}</b></td>
                <td>{r.health}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>ReflectScan AI - Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; display: flex; gap: 20px; }}
                .stat {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; }}
                .stat-value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #34495e; color: white; font-weight: bold; }}
                tr:hover {{ background: #f0f0f0; }}
                .footer {{ margin-top: 20px; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛣️ ReflectScan AI - Retroreflectivity Report</h1>
                <p>NHAI 6th Innovation Hackathon | Production Prototype</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <div class="stat">
                    <div class="stat-value">{len(results)}</div>
                    <div class="stat-label">Total Analyses</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: green;">{passed}</div>
                    <div class="stat-label">Passed ✅</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: red;">{failed}</div>
                    <div class="stat-label">Failed ❌</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{(passed/len(results)*100 if results else 0):.0f}%</div>
                    <div class="stat-label">Pass Rate</div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Marking Type</th>
                        <th>Condition</th>
                        <th>Estimated RL</th>
                        <th>Min Required</th>
                        <th>Compliance</th>
                        <th>Status</th>
                        <th>Health</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div class="footer">
                <p>Confidential: NHAI Hackathon Proposal | Powered by ReflectScan AI v1.2</p>
            </div>
        </body>
        </html>
        """
        return html

class ImageAnnotator:
    """Annotates images with analysis results."""
    
    @staticmethod
    def annotate(image: np.ndarray, result: 'AnalysisResult',
                 mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Annotate image with detection and results."""
        annotated = image.copy()
        
        # Overlay detection mask
        if mask is not None:
            overlay = np.zeros_like(image)
            overlay[mask > 0] = [0, 150, 255]  # Orange overlay
            annotated = cv2.addWeighted(annotated, 0.8, overlay, 0.2, 0)
        
        # Add results panel
        panel_height = 200
        panel = np.ones((panel_height, annotated.shape[1], 3), dtype=np.uint8) * 30
        
        # Text information
        texts = [
            (f"RL: {result.estimated_rl:.1f} mcd/m²/lux", (20, 30)),
            (f"Min: {result.min_required} | Ratio: {result.compliance_ratio}×", (20, 60)),
            (f"Status: {result.status}", (20, 90)),
            (f"Coverage: {result.metrics.coverage_pct:.1f}% | SNR: {result.metrics.snr_ratio:.2f}", (20, 120)),
            (f"Health: {result.health} | Quality: {result.metrics.quality_score:.0%}", (20, 150)),
            (result.recommendation, (20, 180)),
        ]
        
        for text, pos in texts:
            cv2.putText(panel, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Combine image and panel
        result_img = np.vstack([annotated, panel])
        return result_img
    
    @staticmethod
    def save_annotated(image: np.ndarray, result: 'AnalysisResult',
                      output_path: str, mask: Optional[np.ndarray] = None) -> None:
        """Save annotated image."""
        annotated = ImageAnnotator.annotate(image, result, mask)
        cv2.imwrite(output_path, cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        print(f"📸 Annotated image saved: {output_path}")

class SummaryReporter:
    """Generates batch summary reports."""
    
    @staticmethod
    def print_batch_summary(results: List['AnalysisResult]) -> None:
        """Print summary table for batch analysis."""
        sep = "═" * 100
        print("\n" + sep)
        print("  🛣️  HIGHWAY SURVEY SUMMARY – BATCH ANALYSIS RESULTS")
        print(sep)
        
        # Summary statistics
        passed = sum(1 for r in results if "PASS" in r.status)
        excellent = sum(1 for r in results if "Excellent" in r.health)
        critical = sum(1 for r in results if "Critical" in r.health)
        
        print(f"  📊 Total Sections: {len(results)} | Passed: {passed} ✅ | Failed: {len(results) - passed} ❌")
        print(f"  💪 Excellent: {excellent} | Critical: {critical} | Pass Rate: {(passed/len(results)*100 if results else 0):.1f}%")
        print("─" * 100)
        
        # Table header
        header = f"  {'#':<3} {'Marking Type':<30} {'Condition':<15} {'RL':<12} {'Min':<8} {'Ratio':<8} {'Status':<10} {'Health':<12}"
        print(header)
        print("─" * 100)
        
        # Table rows
        for i, r in enumerate(results, 1):
            row = f"  {i:<3} {r.marking_type[:28]:<30} {r.condition:<15} {r.estimated_rl:<12.1f} {r.min_required:<8} {r.compliance_ratio:<8.2f} {r.status:<10} {r.health:<12}"
            print(row)
        
        print(sep)
        
        # Recommendations summary
        critical_actions = [r for r in results if r.compliance_ratio < 1.0]
        urgent_actions = [r for r in results if 1.0 <= r.compliance_ratio < 1.3]
        
        if critical_actions:
            print(f"  🚨 CRITICAL: {len(critical_actions)} section(s) need IMMEDIATE attention")
            for r in critical_actions:
                print(f"      - {r.marking_type}")
        
        if urgent_actions:
            print(f"  🔔 URGENT: {len(urgent_actions)} section(s) within 30 days")
        
        if not critical_actions and not urgent_actions:
            print(f"  ✅ EXCELLENT: All sections meet IRC standards!")
        
        print(sep + "\n")
