# Raymond Products - Shipping Decision System

A proof-of-concept system for determining optimal shipping methods (Small Parcel vs Freight) and generating pallet configurations for Raymond Products' industrial material handling equipment.

## Problem Statement

Raymond Products manufactures industrial carts, racks, and material handling equipment with complex shipping requirements:
- Products range from small parts (2 lbs) to large equipment (160+ lbs)
- Many products ship in multiple boxes with specific dimensions
- Decision between small parcel and freight shipping is not always obvious
- Pallet configuration for freight shipments requires careful planning
- Oversized dimensions (>67" height limit) require special handling

This system automates the decision-making process and provides pallet configuration recommendations.

## Features

- **Intelligent Shipping Decision**: Automatically determines Small Parcel vs Freight based on:
  - Total weight (150 lb threshold)
  - Number of boxes (4 box threshold)
  - Individual box dimensions (96" max for parcel)
  - Dimensional weight calculations
  - Oversized box detection (>91" height)

- **Freight Class Calculation**: Accurate NMFC freight class determination based on density
  - **CRITICAL RULE:** Pallets 75" or taller are calculated AS IF they were 96" tall
  - This NMFC rule discourages tall/unstable shipments by increasing freight class
  - Physical limit is still 96" (91" + 5" pallet), but cost calculated at 96" for anything ≥75"

- **Pallet Configuration**: 
  - Distributes boxes evenly across pallets
  - Respects 91" height constraint (96" total - 5" pallet)
  - Handles oversized boxes that can't be stacked
  - Calculates final pallet dimensions including overhang
  - Adds 50 lbs per pallet to weight calculations
  - Shows both actual and calculated dimensions when 75" rule applies

- **Multi-Box Product Support**: Correctly handles products that ship in multiple boxes per unit

## Installation

### Prerequisites
- Python 3.8 or higher
- No external dependencies (uses Python standard library only)

### Setup
```bash
# Clone the repository
git clone https://github.com/your-org/shipping-decision.git
cd shipping-decision

# No pip install needed - pure Python!
```

## Usage

### Command Line (Quick Test)
```bash
# Test a specific product and quantity
python3 shipping_decision/main.py RPP-3828 3
```

### Interactive Mode
```bash
# Run interactive CLI
python3 shipping_decision/main.py

# Follow the prompts:
# - Enter product SKU
# - Enter quantity
# - View shipping recommendation
```

### As a Python Module
```python
from shipping_decision import ProductCatalog, DecisionEngine, PalletBuilder

# Load product catalog
catalog = ProductCatalog()
catalog.load_from_csv('path/to/products.csv')

# Get a product
product = catalog.get_product('RPP-3828')

# Make shipping decision
decision = DecisionEngine.evaluate(product, quantity=3)
print(f"Decision: {decision.decision}")

# If freight, build pallets
if decision.decision == "FREIGHT":
    pallets = PalletBuilder.build_pallets(product, quantity=3)
    for pallet in pallets:
        print(f"Pallet {pallet.pallet_number}: {pallet.total_weight()} lbs")
```

## CSV Format

The system expects a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| default_code | Product SKU |
| description | Product description |
| Sequence | Box sequence number (1, 2, 3...) for multi-box products |
| Length 1 | Box length in inches |
| Width 1 | Box width in inches |
| Height 1 | Box height in inches |
| Weight 1 | Box weight in pounds |

**Multi-box products**: Use the same SKU on multiple rows with different sequence numbers.

Example:
```csv
default_code,description,Sequence,Length 1,Width 1,Height 1,Weight 1
RPP-3828,Panel Mover,1,42,31,6,59
RPP-3828,Panel Mover,2,16,13,10,24
```

## Project Structure

```
shipping_decision/
├── __init__.py           # Package initialization
├── product_loader.py     # CSV parsing and product data structures
├── calculator.py         # Freight class and dimensional weight calculations
├── decision_engine.py    # Parcel vs Freight decision logic
├── pallet_builder.py     # Pallet configuration and distribution
├── main.py              # CLI interface
└── README.md            # This file
```

## Decision Logic

### Small Parcel Criteria
- Total weight ≤ 150 lbs
- Total boxes ≤ 4
- All boxes ≤ 96" max dimension
- Individual box weight ≤ 150 lbs

### Freight Criteria
Any of the following triggers freight:
- Total weight > 150 lbs
- Total boxes > 4
- Any box dimension > 96"
- Any box weight > 150 lbs
- Dimensional weight > 150 lbs

### Borderline (100-150 lbs)
Flagged for manual review - could go either way depending on distance and urgency.

## Critical Freight Rules

### The 75" Height Rule (NMFC Regulation)

**Physical vs. Calculation Height:**
- **Physical Limit:** Can pack up to 96" total height (91" product + 5" pallet base)
- **Freight Class Calculation:** Any pallet ≥ 75" tall is calculated AS IF it were 96" tall

**Why This Rule Exists:**
- Discourages tall/unstable shipments (safety concern)
- Tall pallets are more likely to tip during transit
- Carriers charge premium rates via higher freight class

**Financial Impact Example:**

*Scenario: 80" tall pallet, 48×40 base, 400 lbs total weight*

**WITHOUT the rule (if carriers charged at actual height):**
- Volume: 48 × 40 × 80 = 153,600 cu in = 88.9 cu ft
- Density: 400 lbs ÷ 88.9 cu ft = 4.5 lbs/cu ft
- Freight Class: **250**

**WITH the 75" rule (actual calculation):**
- Volume: 48 × 40 × 96 = 184,320 cu in = 106.7 cu ft
- Density: 400 lbs ÷ 106.7 cu ft = 3.7 lbs/cu ft
- Freight Class: **300**

**Result:** Moving from Class 250 to Class 300 typically increases shipping cost by 15-20%

**Key Insight:** You can still physically ship tall loads up to 96", but you'll pay as if it's 96" tall even if it's only 75"-95". The pricing penalty begins at 75".

## Freight Class Table

| Density (lbs/cu ft) | Freight Class |
|---------------------|---------------|
| < 1 | 500 |
| 1-2 | 400 |
| 2-4 | 300 |
| 4-6 | 250 |
| 6-8 | 175 |
| 8-10 | 125 |
| 10-12 | 100 |
| 12-15 | 92.5 |
| 15-22.5 | 85 |
| 22.5-30 | 70 |
| 30-35 | 65 |
| 35-50 | 60 |
| 50+ | 50 |

## Example Output

```
Order: 3x RPP-3828
Product: Panel Mover with 8" Poly Casters

RECOMMENDATION: FREIGHT - 1 Pallet

PALLET 1:
  - RPP-3828 Box 1 (42.0×31.0×6.0", 59 lbs) - qty 3
  - RPP-3828 Box 2 (16.0×13.0×10.0", 24 lbs) - qty 3
  Pallet Dimensions: 42×31×53"
  Total Weight: 299 lbs (249 product + 50 pallet)
  Freight Class: 175

TOTAL SHIPMENT: 1 pallet, 299 lbs
```

## Future Enhancements

Potential improvements for production use:
- Integration with carrier APIs (FedEx, UPS, XPO)
- Real-time rate shopping
- 3D bin packing optimization
- Cost comparison (parcel vs freight)
- Odoo ERP integration
- Web interface
- BOL generation
- Label printing

## Testing

Run comprehensive tests:
```bash
# Test small product
python3 shipping_decision/main.py RPP-0302-1 1    # Expect: SMALL_PARCEL

# Test medium product at threshold
python3 shipping_decision/main.py RPP-3828 3      # Expect: FREIGHT

# Test oversized product
python3 shipping_decision/main.py RPP-920L 2      # Expect: FREIGHT (multiple pallets)

# Test high quantity small parts
python3 shipping_decision/main.py RPP-0302-1 50   # Expect: FREIGHT (too many boxes)
```

## License

Internal use - Raymond Products / North Star Cart Company

## Authors

- Nate (Raymond Products) - Product requirements and testing
- Claude (Anthropic) - Implementation

## Version

0.1.0 - Proof of Concept
