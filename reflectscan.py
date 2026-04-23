#!/usr/bin/env python3
"""
ReflectScan AI - Main CLI Application
Command-line interface for retroreflectivity analysis.

Usage:
    python reflectscan.py                    # Run demo batch scan
    python reflectscan.py <image_path>       # Analyze single image
    python reflectscan.py --batch <dir>      # Batch process directory
    python reflectscan.py --report html      # Generate reports
"""

import sys
import argparse
import os
from pathlib import Path
from tqdm import tqdm

from config import config, IRC_STANDARDS
from analyzer import RetroreflectivityAnalyzer, ImageLoader
from synthetic_generator import SyntheticRoadGenerator, BatchDemoGenerator
from reporter import (ReportGenerator, DataExporter, ImageAnnotator,
                      MarkingDetector, PreprocessingEngine, SummaryReporter)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBALS
# ─────────────────────────────────────────────────────────────────────────────

VERSION = "1.2"
APP_NAME = "ReflectScan AI"
DESCRIPTION = "Retroreflectivity Estimation for Road Marking Safety"

def print_banner():
    """Print application banner."""
    banner = f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║    {APP_NAME} v{VERSION} – {DESCRIPTION}                ║
    ║    NHAI 6th Innovation Hackathon | Production Prototype        ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def analyze_single_image(image_path: str, condition: str = "day_dry",
                        marking_type: str = "White Pavement Marking (In-Service)",
                        output_dir: str = ".") -> None:
    """Analyze a single image."""
    print(f"\n📸 Loading image: {image_path}")
    
    try:
        image = ImageLoader.load_rgb(image_path)
        valid, msg = ImageLoader.validate_image(image)
        if not valid:
            print(f"❌ Invalid image: {msg}")
            return
        
        print(f"✓ Image loaded: {image.shape[0]}x{image.shape[1]} pixels")
        
        # Analyze
        print(f"🔍 Analyzing retroreflectivity...")
        analyzer = RetroreflectivityAnalyzer()
        result = analyzer.analyze(image, condition, marking_type, image_path)
        
        # Generate report
        print(ReportGenerator.generate_console_report(result))
        
        # Save annotated image
        if output_dir:
            preprocessor = PreprocessingEngine(condition)
            processed = preprocessor.process(image)
            detector = MarkingDetector()
            mask, _ = detector.detect(processed)
            
            output_path = os.path.join(output_dir, "annotated_output.jpg")
            ImageAnnotator.save_annotated(image, result, output_path, mask)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def batch_demo_mode() -> None:
    """Run synthetic batch demo."""
    print_banner()
    print("\n🎬 Running BATCH DEMO with synthetic road images...")
    print("   Simulating survey vehicle scanning highway sections\n")
    
    demo_gen = BatchDemoGenerator()
    test_cases = demo_gen.create_test_cases(5)
    
    analyzer = RetroreflectivityAnalyzer()
    results = []
    
    print("Processing batch...\n")
    for condition, marking, location, image in tqdm(test_cases, desc="Scanning"):
        result = analyzer.analyze(image, condition, marking, location)
        results.append(result)
        print(ReportGenerator.generate_console_report(result))
    
    # Summary table
    SummaryReporter.print_batch_summary(results)
    
    # Export reports
    print("\n💾 Exporting results...")
    DataExporter.to_csv(results, "reflectscan_report.csv")
    DataExporter.to_json(results, "reflectscan_report.json")
    DataExporter.to_html(results, "reflectscan_report.html")
    
    print("\n✅ Batch demo completed!")
    print("   📊 Reports available:")
    print("      - reflectscan_report.csv")
    print("      - reflectscan_report.json")
    print("      - reflectscan_report.html")

def batch_directory(directory: str, condition: str = "day_dry",
                   marking_type: str = "White Pavement Marking (In-Service)",
                   output_dir: str = "results") -> None:
    """Batch process directory of images."""
    print_banner()
    print(f"\n📁 Batch processing: {directory}")
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = [f for f in Path(directory).glob('*')
                   if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"❌ No images found in {directory}")
        return
    
    print(f"Found {len(image_files)} images\n")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    analyzer = RetroreflectivityAnalyzer()
    results = []
    preprocessor = PreprocessingEngine(condition)
    detector = MarkingDetector()
    
    # Process images
    for image_file in tqdm(image_files, desc="Processing images"):
        try:
            image = ImageLoader.load_rgb(str(image_file))
            valid, _ = ImageLoader.validate_image(image)
            if not valid:
                continue
            
            result = analyzer.analyze(image, condition, marking_type, str(image_file))
            results.append(result)
            
            # Save annotated image
            processed = preprocessor.process(image)
            mask, _ = detector.detect(processed)
            output_name = image_file.stem + "_annotated.jpg"
            ImageAnnotator.save_annotated(image, result,
                                        os.path.join(output_dir, output_name), mask)
        except Exception as e:
            print(f"⚠️  Skipped {image_file.name}: {e}")
    
    # Export results
    if results:
        print("\n📊 Generating reports...")
        DataExporter.to_csv(results, os.path.join(output_dir, "batch_report.csv"))
        DataExporter.to_json(results, os.path.join(output_dir, "batch_report.json"))
        DataExporter.to_html(results, os.path.join(output_dir, "batch_report.html"))
        SummaryReporter.print_batch_summary(results)
        print(f"\n✅ Batch processing complete! Results in: {output_dir}")

def show_irc_standards() -> None:
    """Display IRC standards reference."""
    print("\n" + "═" * 70)
    print("  IRC RETROREFLECTIVITY STANDARDS (mcd/m²/lux)")
    print("═" * 70)
    for marking_type, standards in IRC_STANDARDS.items():
        print(f"\n  {marking_type}:")
        for key, value in standards.items():
            if key != "unit" and key != "category":
                print(f"    • {key.capitalize()}: {value} {standards.get('unit', 'mcd/m²/lux')}")

def show_conditions() -> None:
    """Display available conditions."""
    print("\n" + "═" * 70)
    print("  AVAILABLE TEST CONDITIONS")
    print("═" * 70)
    for cond, profile in config.conditions.items():
        print(f"\n  • {cond.upper()}")
        print(f"    Name: {profile['name']}")
        print(f"    Season: {profile['season']}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{VERSION} - {DESCRIPTION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Run demo batch scan
  %(prog)s image.jpg                    # Analyze single image
  %(prog)s --batch /path/to/images      # Process directory
  %(prog)s --single image.jpg --condition night_wet
  %(prog)s --standards                  # Show IRC standards
        """)
    
    parser.add_argument('image', nargs='?', default=None,
                       help='Image file to analyze')
    parser.add_argument('--batch', type=str,
                       help='Directory for batch processing')
    parser.add_argument('--condition', type=str, default='day_dry',
                       choices=list(config.conditions.keys()),
                       help='Environmental condition')
    parser.add_argument('--type', type=str,
                       default='White Pavement Marking (In-Service)',
                       help='Road marking type')
    parser.add_argument('--output', type=str, default='results',
                       help='Output directory')
    parser.add_argument('--report', type=str, choices=['csv', 'json', 'html', 'all'],
                       help='Report format')
    parser.add_argument('--standards', action='store_true',
                       help='Show IRC standards reference')
    parser.add_argument('--conditions', action='store_true',
                       help='Show available test conditions')
    parser.add_argument('--version', action='version',
                       version=f'{APP_NAME} v{VERSION}')
    
    args = parser.parse_args()
    
    # Show banner
    if not any([args.standards, args.conditions]):
        print_banner()
    
    # Handle various modes
    if args.standards:
        show_irc_standards()
    elif args.conditions:
        show_conditions()
    elif args.batch:
        batch_directory(args.batch, args.condition, args.type, args.output)
    elif args.image:
        analyze_single_image(args.image, args.condition, args.type, args.output)
    else:
        # Default: run demo
        batch_demo_mode()

if __name__ == "__main__":
    main()
