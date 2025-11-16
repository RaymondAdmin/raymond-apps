"""
Test script to verify the 75" height rule is working correctly
"""

import sys
from product_loader import Box, Product
from pallet_builder import Pallet, PalletBuilder
from calculator import FreightCalculator

def test_75_inch_rule():
    """Test that pallets >= 75" use 96" for freight class calculation"""
    
    print("=" * 70)
    print("TESTING 75\" HEIGHT RULE FOR FREIGHT CLASS CALCULATION")
    print("=" * 70)
    print()
    
    # Create test boxes that will result in tall pallets
    # Box 1: Large base, tall (will create 80" pallet when stacked)
    box1 = Box(
        sequence=1,
        length=48,
        width=40,
        height=37.5,  # Two of these = 75" + 5" pallet = 80" total
        weight=200
    )
    
    # Test Case 1: 74" pallet (just under threshold - should use actual)
    print("TEST CASE 1: 74\" Pallet (Below 75\" threshold)")
    print("-" * 70)
    
    pallet_74 = Pallet(1, pallet_weight=50)
    # Add box with 69" height (69 + 5 = 74" total)
    test_box_74 = Box(1, 48, 40, 69, 200)
    pallet_74.add_box(test_box_74, "TEST-74")
    
    dims_74 = pallet_74.dimensions()
    actual_volume_74 = dims_74[0] * dims_74[1] * dims_74[2]
    actual_cf_74 = actual_volume_74 / 1728
    actual_density_74 = pallet_74.total_weight() / actual_cf_74
    freight_class_74 = pallet_74.freight_class()
    
    print(f"Actual Dimensions: {dims_74[0]:.0f} × {dims_74[1]:.0f} × {dims_74[2]:.0f}\"")
    print(f"Actual Volume: {actual_cf_74:.1f} cu ft")
    print(f"Total Weight: {pallet_74.total_weight():.0f} lbs")
    print(f"Actual Density: {actual_density_74:.2f} lbs/cu ft")
    print(f"Freight Class: {freight_class_74}")
    print(f"✓ Should calculate using ACTUAL height (74\")")
    print()
    
    # Test Case 2: 75" pallet (at threshold - should use 96")
    print("TEST CASE 2: 75\" Pallet (AT 75\" threshold)")
    print("-" * 70)
    
    pallet_75 = Pallet(2, pallet_weight=50)
    # Add box with 70" height (70 + 5 = 75" total)
    test_box_75 = Box(1, 48, 40, 70, 200)
    pallet_75.add_box(test_box_75, "TEST-75")
    
    dims_75 = pallet_75.dimensions()
    actual_volume_75 = dims_75[0] * dims_75[1] * dims_75[2]
    actual_cf_75 = actual_volume_75 / 1728
    actual_density_75 = pallet_75.total_weight() / actual_cf_75
    
    # Calculate what it SHOULD be with 96" rule
    calc_volume_75 = dims_75[0] * dims_75[1] * 96
    calc_cf_75 = calc_volume_75 / 1728
    calc_density_75 = pallet_75.total_weight() / calc_cf_75
    
    freight_class_75 = pallet_75.freight_class()
    expected_class_75 = FreightCalculator.get_freight_class(calc_density_75)
    
    print(f"Actual Dimensions: {dims_75[0]:.0f} × {dims_75[1]:.0f} × {dims_75[2]:.0f}\"")
    print(f"Actual Volume: {actual_cf_75:.1f} cu ft → Density: {actual_density_75:.2f} lbs/cu ft")
    print(f"Calc Volume (96\"): {calc_cf_75:.1f} cu ft → Density: {calc_density_75:.2f} lbs/cu ft")
    print(f"Total Weight: {pallet_75.total_weight():.0f} lbs")
    print(f"Freight Class (Calculated): {freight_class_75}")
    print(f"Expected Class (at 96\"): {expected_class_75}")
    
    if freight_class_75 == expected_class_75:
        print("✓ PASS: Using 96\" height for calculation")
    else:
        print("✗ FAIL: NOT using 96\" height rule!")
    print()
    
    # Test Case 3: 80" pallet (above threshold - should use 96")
    print("TEST CASE 3: 80\" Pallet (Above 75\" threshold)")
    print("-" * 70)
    
    pallet_80 = Pallet(3, pallet_weight=50)
    # Add two boxes: 37.5" each = 75" + 5" pallet = 80" total
    pallet_80.add_box(box1, "TEST-80")
    pallet_80.add_box(box1, "TEST-80")
    
    dims_80 = pallet_80.dimensions()
    actual_volume_80 = dims_80[0] * dims_80[1] * dims_80[2]
    actual_cf_80 = actual_volume_80 / 1728
    actual_density_80 = pallet_80.total_weight() / actual_cf_80
    
    # Calculate what it SHOULD be with 96" rule
    calc_volume_80 = dims_80[0] * dims_80[1] * 96
    calc_cf_80 = calc_volume_80 / 1728
    calc_density_80 = pallet_80.total_weight() / calc_cf_80
    
    freight_class_80 = pallet_80.freight_class()
    expected_class_80 = FreightCalculator.get_freight_class(calc_density_80)
    
    print(f"Actual Dimensions: {dims_80[0]:.0f} × {dims_80[1]:.0f} × {dims_80[2]:.0f}\"")
    print(f"Actual Volume: {actual_cf_80:.1f} cu ft → Density: {actual_density_80:.2f} lbs/cu ft")
    print(f"Calc Volume (96\"): {calc_cf_80:.1f} cu ft → Density: {calc_density_80:.2f} lbs/cu ft")
    print(f"Total Weight: {pallet_80.total_weight():.0f} lbs")
    print(f"Freight Class (Calculated): {freight_class_80}")
    print(f"Expected Class (at 96\"): {expected_class_80}")
    
    if freight_class_80 == expected_class_80:
        print("✓ PASS: Using 96\" height for calculation")
    else:
        print("✗ FAIL: NOT using 96\" height rule!")
    print()
    
    # Test Case 4: 91" pallet (max height - should use 96")
    print("TEST CASE 4: 91\" Pallet (Maximum allowable height)")
    print("-" * 70)
    
    pallet_91 = Pallet(4, pallet_weight=50)
    # Add box with 86" height (86 + 5 = 91" total)
    test_box_91 = Box(1, 48, 40, 86, 200)
    pallet_91.add_box(test_box_91, "TEST-91")
    
    dims_91 = pallet_91.dimensions()
    actual_volume_91 = dims_91[0] * dims_91[1] * dims_91[2]
    actual_cf_91 = actual_volume_91 / 1728
    actual_density_91 = pallet_91.total_weight() / actual_cf_91
    
    # Calculate what it SHOULD be with 96" rule
    calc_volume_91 = dims_91[0] * dims_91[1] * 96
    calc_cf_91 = calc_volume_91 / 1728
    calc_density_91 = pallet_91.total_weight() / calc_cf_91
    
    freight_class_91 = pallet_91.freight_class()
    expected_class_91 = FreightCalculator.get_freight_class(calc_density_91)
    
    print(f"Actual Dimensions: {dims_91[0]:.0f} × {dims_91[1]:.0f} × {dims_91[2]:.0f}\"")
    print(f"Actual Volume: {actual_cf_91:.1f} cu ft → Density: {actual_density_91:.2f} lbs/cu ft")
    print(f"Calc Volume (96\"): {calc_cf_91:.1f} cu ft → Density: {calc_density_91:.2f} lbs/cu ft")
    print(f"Total Weight: {pallet_91.total_weight():.0f} lbs")
    print(f"Freight Class (Calculated): {freight_class_91}")
    print(f"Expected Class (at 96\"): {expected_class_91}")
    
    if freight_class_91 == expected_class_91:
        print("✓ PASS: Using 96\" height for calculation")
    else:
        print("✗ FAIL: NOT using 96\" height rule!")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("The 75\" height rule is a freight industry regulation (NMFC) that:")
    print("1. Allows physical shipments up to 96\" tall")
    print("2. But calculates freight class AS IF pallets >= 75\" are 96\" tall")
    print("3. This reduces density → increases freight class → increases cost")
    print("4. Discourages tall/unstable shipments for safety")
    print()
    print("Financial Impact: Moving from Class 250 to 300 typically costs 15-20% more")
    print("=" * 70)

if __name__ == "__main__":
    test_75_inch_rule()
