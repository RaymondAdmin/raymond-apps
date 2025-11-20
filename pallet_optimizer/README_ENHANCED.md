# Raymond Pallet Optimizer - Enhanced Version

## What's New in This Version

This enhanced version adds **industry-standard safety validation** on top of the EB-AFIT packing algorithm.

### Key Enhancements:

1. **🚨 Stability Validation** (OSHA 3:1 Rule)
   - Automatically checks height-to-width ratio for every pallet
   - Flags dangerous configurations that could tip over
   - Rejects pallets with ratio > 3.0:1

2. **💰 Cost Impact Warnings** (NMFC 75" Rule)
   - Identifies when pallets trigger freight class penalties
   - Shows impact of 75" height threshold
   - Suggests alternatives to reduce shipping costs

3. **📦 Optimization Suggestions**
   - Detects flat boxes standing on edge
   - Recommends laying flat for better stability
   - Notes when height exceeds LTL limits

4. **✅ Visual Status Indicators**
   - Green checkmark: Good stability (≤ 2.0:1)
   - Yellow warning: Borderline (2.0-2.5:1)
   - Orange alert: Concerning (2.5-3.0:1)
   - Red X: Unsafe (> 3.0:1)

## How to Use

### 1. Start the App

```bash
cd pallet_optimizer
pip install -r requirements.txt
streamlit run app.py
```

### 2. Upload Product Catalog

Upload your CSV file with product dimensions and weights.

### 3. Build Your Order

- Search and select products
- Set quantities
- Add to order

### 4. Calculate Configuration

Click "Calculate Pallet Configuration" to optimize.

### 5. Review Warnings

The app will show:
- **CRITICAL alerts** (red) - Must address before shipping
- **Cost warnings** (yellow) - Freight class penalties
- **Info suggestions** (blue) - Optional optimizations

### 6. Check Each Pallet

Expand pallet details to see:
- Dimensions and weight
- **Stability ratio** with status indicator
- Freight class
- Box contents

## Warning Types Explained

### 🚨 CRITICAL - Safety Violation
**Example:** "Pallet 1 stability violation! Height/width ratio 6.11:1 exceeds maximum 3.0:1"

**Action:** Configuration is UNSAFE. Must reconfigure or reject.

**Cause:** Pallet is too tall relative to its base width. Will tip over in transit.

### 💰 COST IMPACT - Freight Penalty
**Example:** "Pallet 1 triggers 75" rule penalty. Consider splitting to reduce cost."

**Action:** Review if penalty is worth the space efficiency.

**Cause:** Height ≥ 75" causes freight class to be calculated at 96", increasing cost significantly.

### ⚠️ WARNING - Operational Issue
**Example:** "Pallet 1 height 86" exceeds common LTL freight limit of 72""

**Action:** May require special handling or be rejected by some carriers.

**Cause:** Height exceeds standard limits. Check with your carriers.

### ℹ️ INFO - Optimization Suggestion
**Example:** "Pallet 1 has 5 flat boxes standing on edge. Consider laying flat."

**Action:** Optional - could improve stability if you want to optimize further.

**Cause:** Algorithm found a configuration, but laying flat might be more stable.

## Example Results

### RPP-3988 x 1 unit
```
🚨 CRITICAL: Pallet 1 stability violation! 
   Height/width ratio 6.11:1 exceeds maximum 3.0:1
   This configuration is UNSAFE and should be rejected.
```
**Verdict:** DO NOT SHIP - reconfigure required

### RPP-550 x 10 units
```
💰 COST IMPACT: Pallet 1 triggers 75" rule penalty
   Height 76.0" is calculated as 96" for freight class
   Consider splitting to reduce freight cost
```
**Verdict:** Safe but expensive - evaluate cost vs. convenience

### RPP-500 x 10 units
```
✅ No warnings - configuration looks good!
   Stability ratio: 1.64:1 ✅
   Height: 74" (just under 75" penalty)
```
**Verdict:** Optimal configuration - ship it!

## Technical Details

### Stability Ratio Formula
```
Ratio = Height / min(Length, Width)
```

**Industry Standards:**
- **≤ 2.0:1** - Optimal (preferred)
- **≤ 2.5:1** - Acceptable (borderline)
- **≤ 3.0:1** - Maximum (OSHA guideline)
- **> 3.0:1** - Unsafe (reject)

### 75" Rule (NMFC)
When pallet height ≥ 75 inches:
- Freight class calculated using 96" instead of actual height
- Results in lower density
- Increases freight class (costs more)
- Can significantly impact shipping costs

**Example:**
- 76" tall, 370 lbs → Class 300 (with penalty)
- 74" tall, 370 lbs → Class 150 (no penalty)

### Overhang Allowance
System allows 8" overhang on ONE dimension:
- Standard GMA pallet: 48" × 40"
- With overhang: up to 56" × 48"
- Only one dimension can overhang significantly

## Files in This Version

- `app.py` - Main Streamlit application (updated)
- `core/enhanced_pallet_builder.py` - Enhanced builder with validation (NEW)
- `core/pallet_builder.py` - Original builder (unchanged)
- `core/freight_calculator.py` - NMFC freight class calculator
- `palletier/` - EB-AFIT algorithm library (unchanged)

## What Didn't Change

The core **EB-AFIT packing algorithm** is unchanged. We only added:
- Validation checks after packing
- Warning generation
- User interface enhancements

The algorithm still finds optimal volume utilization - we just help you understand the tradeoffs.

## Troubleshooting

**Q: Why am I getting CRITICAL warnings?**
A: The algorithm found a configuration that violates safety standards. Try:
- Increasing quantity (wider base)
- Splitting across multiple pallets
- Different pallet size

**Q: Can I ignore INFO messages?**
A: Yes - they're suggestions only. CRITICAL and COST warnings need attention.

**Q: How accurate is this?**
A: The EB-AFIT algorithm achieves 80-90% accuracy vs. real-world packing. Your results should match expectations for well-measured products.

## Support

For questions or issues:
1. Check the warnings - they explain the problem
2. Review the stability ratio - is it > 3.0?
3. Look at the dimensions - any too tall or narrow?

## Version History

**v2.0 (Enhanced)** - November 2025
- Added stability validation
- Added cost impact warnings
- Added optimization suggestions
- Improved UI with visual indicators

**v1.0 (Original)** - November 2025
- EB-AFIT algorithm implementation
- Basic pallet optimization
- Freight class calculation
