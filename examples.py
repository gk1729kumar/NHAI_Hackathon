#!/usr/bin/env python3
"""
ReflectScan AI - Quick Start Examples
Demonstrates how to use the API programmatically.
"""

import numpy as np
from analyzer import RetroreflectivityAnalyzer, ImageLoader
from synthetic_generator import SyntheticRoadGenerator, BatchDemoGenerator
from reporter import (ReportGenerator, DataExporter, ImageAnnotator,
                      MarkingDetector, PreprocessingEngine)

def example_1_single_image_analysis():
    """Example 1: Analyze a single real image."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Image Analysis")
    print("="*60)
    
    # Load real image (replace with your image path)
    try:
        image = ImageLoader.load_rgb("path/to/your/image.jpg")
        
        # Create analyzer
        analyzer = RetroreflectivityAnalyzer()
        
        # Analyze
        result = analyzer.analyze(
            image,
            condition="day_dry",
            marking_type="White Pavement Marking (In-Service)",
            image_path="path/to/your/image.jpg"
        )
        
        # Print report
        print(ReportGenerator.generate_console_report(result))
        
    except FileNotFoundError:
        print("Image not found. Replace with your actual image path.")

def example_2_synthetic_batch():
    """Example 2: Run batch analysis on synthetic images."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Synthetic Batch Analysis")
    print("="*60)
    
    # Create demo generator
    demo_gen = BatchDemoGenerator()
    test_cases = demo_gen.create_test_cases(num_sections=3)
    
    # Analyze batch
    analyzer = RetroreflectivityAnalyzer()
    results = []
    
    for condition, marking, location, image in test_cases:
        result = analyzer.analyze(image, condition, marking, location)
        results.append(result)
        print(f"\n✓ {location}: {result.status}")
    
    # Export results
    print("\n📊 Exporting results...")
    DataExporter.to_csv(results, "demo_results.csv")
    DataExporter.to_json(results, "demo_results.json")

def example_3_condition_comparison():
    """Example 3: Compare same marking across different conditions."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Environmental Condition Comparison")
    print("="*60)
    
    generator = SyntheticRoadGenerator()
    analyzer = RetroreflectivityAnalyzer()
    
    conditions = ["day_dry", "night_dry", "day_wet", "night_wet", "foggy"]
    
    print(f"\n{'Condition':<20} {'RL Value':<15} {'Compliance Ratio':<20} {'Status':<12}")
    print("─" * 70)
    
    for condition in conditions:
        image = generator.generate(condition)
        result = analyzer.analyze(image, condition, "White Pavement Marking (New)")
        
        print(f"{condition:<20} {result.estimated_rl:<15.1f} {result.compliance_ratio:<20.2f} {result.status:<12}")

def example_4_custom_parameters():
    """Example 4: Customize analysis parameters."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Parameter Configuration")
    print("="*60)
    
    from config import config
    
    # Modify calibration parameters
    print("Original brightness_coefficient:", config.calibration["brightness_coefficient"])
    
    # Simulate fine-tuning
    config.calibration["brightness_coefficient"] = 3.0
    print("Modified brightness_coefficient:", config.calibration["brightness_coefficient"])
    
    # Re-run analysis with modified parameters
    generator = SyntheticRoadGenerator()
    analyzer = RetroreflectivityAnalyzer()
    
    image = generator.generate("day_dry")
    result = analyzer.analyze(image, "day_dry", "White Pavement Marking (New)")
    
    print(f"\nWith modified coefficient:")
    print(f"  Estimated RL: {result.estimated_rl:.1f}")
    
    # Reset to original
    config.calibration["brightness_coefficient"] = 2.85

def example_5_error_handling():
    """Example 5: Proper error handling."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Error Handling Best Practices")
    print("="*60)
    
    analyzer = RetroreflectivityAnalyzer()
    
    # Test 1: Invalid image file
    print("\n1. Testing invalid file path...")
    try:
        image = ImageLoader.load_rgb("nonexistent.jpg")
    except FileNotFoundError as e:
        print(f"   ✓ Caught error: {e}")
    
    # Test 2: Invalid image validation
    print("\n2. Testing invalid image dimensions...")
    invalid_image = np.zeros((100, 100, 3), dtype=np.uint8)  # Too small
    valid, msg = ImageLoader.validate_image(invalid_image)
    if not valid:
        print(f"   ✓ Validation failed: {msg}")
    
    # Test 3: Process valid image safely
    print("\n3. Processing valid image...")
    try:
        generator = SyntheticRoadGenerator()
        image = generator.generate("day_dry")
        result = analyzer.analyze(image, "day_dry", "White Pavement Marking (New)")
        print(f"   ✓ Analysis successful: {result.status}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

def example_6_visualization():
    """Example 6: Generate annotated images and reports."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Visualization & Annotation")
    print("="*60)
    
    generator = SyntheticRoadGenerator()
    analyzer = RetroreflectivityAnalyzer()
    
    # Generate and analyze
    image = generator.generate("night_wet")
    result = analyzer.analyze(image, "night_wet", "Road Stud (RPM)")
    
    # Create detection mask
    preprocessor = PreprocessingEngine("night_wet")
    processed = preprocessor.process(image)
    detector = MarkingDetector()
    mask, _ = detector.detect(processed)
    
    # Save annotated image
    output_path = "annotated_example.jpg"
    ImageAnnotator.save_annotated(image, result, output_path, mask)
    print(f"✓ Annotated image saved to: {output_path}")
    
    # Save reports in all formats
    results = [result]
    
    print("Generating reports...")
    DataExporter.to_csv(results, "example_report.csv")
    DataExporter.to_json(results, "example_report.json")
    DataExporter.to_html(results, "example_report.html")
    
    print("✓ All reports generated!")

def example_7_programmatic_workflow():
    """Example 7: Complete programmatic workflow."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Complete Workflow")
    print("="*60)
    
    # Step 1: Generate synthetic dataset
    print("\n[1/4] Generating synthetic data...")
    demo_gen = BatchDemoGenerator()
    test_cases = demo_gen.create_test_cases(5)
    
    # Step 2: Analyze all
    print("[2/4] Analyzing images...")
    analyzer = RetroreflectivityAnalyzer()
    results = []
    
    for condition, marking, location, image in test_cases:
        result = analyzer.analyze(image, condition, marking, location)
        results.append(result)
    
    # Step 3: Generate comprehensive reports
    print("[3/4] Generating reports...")
    DataExporter.to_csv(results, "final_report.csv")
    DataExporter.to_json(results, "final_report.json")
    DataExporter.to_html(results, "final_report.html")
    
    # Step 4: Print summary
    print("[4/4] Summary:")
    passed = sum(1 for r in results if "PASS" in r.status)
    print(f"  ✓ Total sections: {len(results)}")
    print(f"  ✓ Passed: {passed}")
    print(f"  ✓ Failed: {len(results) - passed}")
    print(f"  ✓ Pass rate: {(passed/len(results)*100):.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# RUN EXAMPLES
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("█  ReflectScan AI - Example Usage Demonstrations         █")
    print("█" * 60)
    
    examples = [
        ("Single Image Analysis", example_1_single_image_analysis),
        ("Synthetic Batch", example_2_synthetic_batch),
        ("Condition Comparison", example_3_condition_comparison),
        ("Custom Parameters", example_4_custom_parameters),
        ("Error Handling", example_5_error_handling),
        ("Visualization", example_6_visualization),
        ("Complete Workflow", example_7_programmatic_workflow),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n⚠️  Example failed: {e}")
    
    print("\n" + "█" * 60)
    print("█  All examples completed!                              █")
    print("█" * 60)
