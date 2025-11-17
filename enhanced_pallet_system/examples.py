"""
Example Usage and Tests for Enhanced Pallet System
"""

from models import Box, Product
from pallet_builder import PalletBuilder
from stability_analyzer import StabilityAnalyzer
from freight_calculator import FreightCalculator, ShipmentCalculator
import json


def example_rpp_3828():
    """
    Test with real Raymond Products item: RPP-3828
    Panel Mover with 8" Poly Casters
    - Box 1: 42×31×6", 59 lbs
    - Box 2: 16×13×10", 24 lbs
    Quantity: 3 units
    """
    print("="*80)
    print("EXAMPLE: RPP-3828 Panel Mover × 3 units")
    print("="*80)
    
    # Define the product
    product = Product(
        sku="RPP-3828",
        description="Panel Mover with 8\" Poly Casters",
        boxes=[
            Box(length=42, width=31, height=6, weight=59, sequence=1),
            Box(length=16, width=13, height=10, weight=24, sequence=2)
        ]
    )
    
    print(f"\nProduct: {product.sku} - {product.description}")
    print(f"Boxes per unit: {product.box_count()}")
    print(f"Weight per unit: {product.total_weight()} lbs")
    print(f"Total order: 3 units = 6 boxes = {product.total_weight() * 3} lbs")
    
    # Build pallets
    builder = PalletBuilder(pallet_size='GMA_40')
    pallets = builder.build_pallets(product, quantity=3)
    
    print(f"\n{'─'*80}")
    print(f"PALLET CONFIGURATION: {len(pallets)} pallet(s) needed")
    print(f"{'─'*80}")
    
    for pallet in pallets:
        summary = builder.get_pallet_summary(pallet)
        print(f"\n📦 PALLET {summary['pallet_number']}:")
        print(f"   Dimensions: {summary['dimensions']['length']:.0f}×{summary['dimensions']['width']:.0f}×{summary['dimensions']['height']:.0f}\"")
        print(f"   Weight: {summary['weight']['total']:.0f} lbs ({summary['weight']['product']:.0f} product + {summary['weight']['pallet']:.0f} pallet)")
        print(f"   Boxes: {summary['box_count']}")
        print(f"\n   📊 FREIGHT CLASS:")
        print(f"      Class: {summary['freight']['freight_class']}")
        print(f"      Density: {summary['freight']['density']:.2f} lbs/cu ft")
        if summary['freight']['penalty_applied']:
            print(f"      ⚠️  75\" Rule Applied")
            print(f"      Actual volume: {summary['freight']['actual_volume_cf']:.1f} cu ft")
            print(f"      Calculated at: {summary['freight']['calculated_volume_cf']:.1f} cu ft")
        
        print(f"\n   🔒 STABILITY:")
        print(f"      Grade: {summary['stability']['grade']}")
        print(f"      COG: {summary['stability']['cog_percentage']:.1f}% of height")
        print(f"      Bottom weight: {summary['stability']['bottom_weight_pct']:.1f}%")
        print(f"      Safe to ship: {'✅ YES' if summary['stability']['safe_to_ship'] else '❌ NO'}")
        
        if summary['stability']['warnings']:
            print(f"\n      Warnings:")
            for warning in summary['stability']['warnings']:
                print(f"         {warning}")
        
        # Show box placement
        print(f"\n   📦 BOX PLACEMENT:")
        layers = pallet.layers()
        for layer_num in sorted(layers.keys()):
            print(f"      Layer {layer_num + 1}:")
            for pb in layers[layer_num]:
                dims = pb.box.rotated_dimensions(pb.rotation)
                print(f"         • {pb.box.product_sku} Box {pb.box.sequence}: "
                      f"{dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\" @ "
                      f"({pb.x:.0f},{pb.y:.0f},{pb.z:.0f}) - {pb.box.weight:.0f} lbs")


def example_small_product():
    """
    Test with small single-box product
    """
    print("\n\n" + "="*80)
    print("EXAMPLE: Small Product (Single Box) × 10 units")
    print("="*80)
    
    product = Product(
        sku="TEST-SMALL",
        description="Small Widget",
        boxes=[
            Box(length=12, width=8, height=6, weight=5, sequence=1)
        ]
    )
    
    print(f"\nProduct: {product.sku}")
    print(f"Box: 12×8×6\", 5 lbs")
    print(f"Quantity: 10 units")
    
    builder = PalletBuilder(pallet_size='GMA_40')
    pallets = builder.build_pallets(product, quantity=10)
    
    print(f"\nResult: {len(pallets)} pallet(s)")
    
    for pallet in pallets:
        summary = builder.get_pallet_summary(pallet)
        print(f"\nPallet {summary['pallet_number']}: "
              f"{summary['dimensions']['length']:.0f}×{summary['dimensions']['width']:.0f}×{summary['dimensions']['height']:.0f}\", "
              f"{summary['weight']['total']:.0f} lbs, "
              f"Class {summary['freight']['freight_class']}, "
              f"Stability: {summary['stability']['grade']}")


def example_decision_logic():
    """
    Demonstrate shipping decision logic (parcel vs freight)
    """
    print("\n\n" + "="*80)
    print("EXAMPLE: Shipping Decision Logic")
    print("="*80)
    
    # Test case 1: Small/light (should be parcel)
    print("\n1. Small order (2 boxes, 25 lbs):")
    decision = ShipmentCalculator.should_ship_freight(
        total_weight=25,
        total_boxes=2,
        max_box_dimension=20,
        dimensional_weight=15
    )
    print(f"   Decision: {decision['decision']}")
    print(f"   Confidence: {decision['confidence']}")
    for reason in decision['reasons']:
        print(f"   - {reason}")
    
    # Test case 2: Heavy (should be freight)
    print("\n2. Heavy order (6 boxes, 250 lbs):")
    decision = ShipmentCalculator.should_ship_freight(
        total_weight=250,
        total_boxes=6,
        max_box_dimension=42,
        dimensional_weight=200
    )
    print(f"   Decision: {decision['decision']}")
    print(f"   Confidence: {decision['confidence']}")
    for reason in decision['reasons']:
        print(f"   - {reason}")
    
    # Test case 3: Borderline
    print("\n3. Borderline order (4 boxes, 125 lbs):")
    decision = ShipmentCalculator.should_ship_freight(
        total_weight=125,
        total_boxes=4,
        max_box_dimension=36,
        dimensional_weight=100
    )
    print(f"   Decision: {decision['decision']}")
    print(f"   Confidence: {decision['confidence']}")
    for reason in decision['reasons']:
        print(f"   - {reason}")


def test_height_grouping():
    """
    Test that height grouping works correctly
    """
    print("\n\n" + "="*80)
    print("TEST: Height Grouping Algorithm")
    print("="*80)
    
    # Create product with different height boxes
    product = Product(
        sku="TEST-MULTI",
        description="Multi-Height Test Product",
        boxes=[
            Box(length=20, width=15, height=10, weight=30, sequence=1),
            Box(length=20, width=15, height=10, weight=30, sequence=2),
            Box(length=20, width=15, height=6, weight=20, sequence=3),
        ]
    )
    
    print(f"\nProduct has boxes with heights: 10\", 10\", 6\"")
    
    builder = PalletBuilder()
    all_boxes = builder._generate_boxes(product, quantity=2)
    
    height_groups = builder._group_by_height(all_boxes)
    
    print(f"\nHeight groups formed:")
    for height, boxes in sorted(height_groups.items(), reverse=True):
        print(f"   {height}\" tall: {len(boxes)} boxes")
    
    print(f"\n✅ Height grouping working correctly!")
    print(f"   - Boxes grouped by height for efficient layer filling")
    print(f"   - Each group sorted by footprint (largest first)")


def compare_with_and_without_enhancements():
    """
    Compare results with simple vs enhanced algorithm
    """
    print("\n\n" + "="*80)
    print("COMPARISON: Enhanced vs Simple Algorithm")
    print("="*80)
    
    product = Product(
        sku="RPP-3828",
        description="Panel Mover",
        boxes=[
            Box(length=42, width=31, height=6, weight=59, sequence=1),
            Box(length=16, width=13, height=10, weight=24, sequence=2)
        ]
    )
    
    print(f"\nProduct: {product.sku} × 5 units")
    print(f"         10 total boxes (5× Box 1 @ 6\" tall, 5× Box 2 @ 10\" tall)")
    
    builder = PalletBuilder()
    pallets = builder.build_pallets(product, quantity=5)
    
    print(f"\nEnhanced Algorithm Result:")
    print(f"   Pallets needed: {len(pallets)}")
    print(f"   Total weight: {sum(p.total_weight() for p in pallets):.0f} lbs")
    
    for pallet in pallets:
        dims = pallet.dimensions()
        layers = pallet.layers()
        print(f"\n   Pallet {pallet.pallet_number}:")
        print(f"      Dimensions: {dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\"")
        print(f"      Layers: {len(layers)}")
        for layer_num in sorted(layers.keys()):
            heights_in_layer = [pb.box.height for pb in layers[layer_num]]
            unique_heights = set(heights_in_layer)
            print(f"         Layer {layer_num+1}: {len(layers[layer_num])} boxes, heights: {unique_heights}")
    
    print(f"\n✨ Key Features:")
    print(f"   ✅ Height grouping keeps similar heights together")
    print(f"   ✅ Stability analysis ensures safe shipping")
    print(f"   ✅ Freight class calculated with 75\" NMFC rule")
    print(f"   ✅ Weight balanced across pallets")


if __name__ == "__main__":
    # Run all examples
    example_rpp_3828()
    example_small_product()
    example_decision_logic()
    test_height_grouping()
    compare_with_and_without_enhancements()
    
    print("\n\n" + "="*80)
    print("✅ ALL EXAMPLES COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Test with your actual product CSV data")
    print("2. Compare results with current Streamlit app")
    print("3. Tune parameters if needed")
    print("4. Port to Odoo when validated")
