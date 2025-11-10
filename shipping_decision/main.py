"""
Main CLI Interface
Command-line tool for testing the shipping decision system
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shipping_decision.product_loader import ProductCatalog
from shipping_decision.decision_engine import DecisionEngine, ShippingDecision
from shipping_decision.pallet_builder import PalletBuilder, PalletReport


def main():
    """Main entry point for CLI"""
    
    print("=" * 70)
    print("RAYMOND PRODUCTS - SHIPPING DECISION SYSTEM")
    print("=" * 70)
    print()
    
    # Load product catalog
    print("Loading product catalog...")
    catalog = ProductCatalog()
    csv_path = "/mnt/user-data/uploads/Final_-_Raymond_Product_Packaging_for_Upload_-_Final.csv"
    
    try:
        catalog.load_from_csv(csv_path)
        print(f"✓ Loaded {len(catalog)} products")
    except FileNotFoundError:
        print(f"✗ Error: Could not find CSV file at {csv_path}")
        return
    except Exception as e:
        print(f"✗ Error loading catalog: {e}")
        return
    
    print()
    
    # Interactive loop
    while True:
        print("-" * 70)
        sku = input("Enter product SKU (or 'quit' to exit): ").strip()
        
        if sku.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Look up product
        product = catalog.get_product(sku)
        if not product:
            print(f"✗ Product '{sku}' not found in catalog")
            continue
        
        print(f"✓ Found: {product.description}")
        print(f"  Boxes per unit: {product.box_count()}")
        print(f"  Weight per unit: {product.total_weight():.1f} lbs")
        print()
        
        # Get quantity
        try:
            quantity_input = input("Enter quantity: ").strip()
            quantity = int(quantity_input)
            if quantity <= 0:
                print("✗ Quantity must be greater than 0")
                continue
        except ValueError:
            print("✗ Invalid quantity")
            continue
        
        print()
        print("=" * 70)
        
        # Make decision
        decision = DecisionEngine.evaluate(product, quantity)
        
        print(f"DECISION: {decision.decision}")
        print()
        print("Reasoning:")
        for reason in decision.reasons:
            print(f"  • {reason}")
        print()
        print("Details:")
        print(f"  Total boxes: {decision.details['total_boxes']}")
        print(f"  Total weight: {decision.details['total_weight']:.1f} lbs")
        print(f"  Dimensional weight: {decision.details['dimensional_weight']:.1f} lbs")
        print(f"  Billable weight: {decision.details['billable_weight']:.1f} lbs")
        print()
        
        # If freight, build pallet configuration
        if decision.decision == ShippingDecision.FREIGHT:
            print("=" * 70)
            print("PALLET CONFIGURATION")
            print("=" * 70)
            print()
            
            pallets = PalletBuilder.build_pallets(product, quantity)
            report = PalletReport.generate(product, quantity, pallets)
            print(report)
        
        # If small parcel, list boxes
        elif decision.decision == ShippingDecision.SMALL_PARCEL:
            print("=" * 70)
            print("SMALL PARCEL SHIPMENT")
            print("=" * 70)
            print()
            print(f"Ship as {decision.details['total_boxes']} separate package(s):")
            print()
            
            box_num = 1
            for i in range(quantity):
                for box in product.boxes:
                    print(f"  Package {box_num}: {product.sku} Box {box.sequence}")
                    print(f"    Dimensions: {box.length:.1f}×{box.width:.1f}×{box.height:.1f}\"")
                    print(f"    Weight: {box.weight:.0f} lbs")
                    print()
                    box_num += 1
        
        print()


def quick_test(sku: str, quantity: int):
    """Quick test function for a specific product/quantity"""
    
    catalog = ProductCatalog()
    csv_path = "/mnt/user-data/uploads/Final_-_Raymond_Product_Packaging_for_Upload_-_Final.csv"
    catalog.load_from_csv(csv_path)
    
    product = catalog.get_product(sku)
    if not product:
        print(f"Product {sku} not found")
        return
    
    print(f"Testing: {quantity}x {sku}")
    print()
    
    decision = DecisionEngine.evaluate(product, quantity)
    print(f"Decision: {decision.decision}")
    
    if decision.decision == ShippingDecision.FREIGHT:
        pallets = PalletBuilder.build_pallets(product, quantity)
        report = PalletReport.generate(product, quantity, pallets)
        print()
        print(report)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        # Command line mode: python main.py RPP-3828 3
        sku = sys.argv[1]
        quantity = int(sys.argv[2])
        quick_test(sku, quantity)
    else:
        # Interactive mode
        main()
