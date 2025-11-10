# Raymond Products - Shipping Decision System

A web-based tool for determining optimal shipping methods (Small Parcel vs Freight) and generating pallet configurations for Raymond Products' industrial material handling equipment.

## 🚀 Quick Start

### Run Locally

```bash
# Clone the repository
git clone https://github.com/RaymondAdmin/raymond-apps.git
cd raymond-apps/shipping_decision

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Deploy to Streamlit Cloud (Free)

1. **Fork/Push this repo to GitHub** (already done ✓)

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Sign in with GitHub**

4. **Click "New app"**

5. **Configure deployment:**
   - Repository: `RaymondAdmin/raymond-apps`
   - Branch: `main`
   - Main file path: `shipping_decision/app.py`

6. **Click "Deploy"**

Your app will be live at `https://[your-app-name].streamlit.app` in ~2 minutes!

## 📖 How to Use

1. **Upload your product catalog CSV** using the sidebar
2. **Select a product SKU** from the dropdown
3. **Enter the quantity** you want to ship
4. **Click "Calculate Shipping Method"** to get recommendations

The system will:
- Determine if shipment should go Small Parcel or Freight
- Provide pallet configurations for freight shipments
- Calculate freight class based on density
- Show detailed box-by-box breakdown

## 📊 Features

- **Intelligent Decision Engine**: Automatically determines shipping method based on:
  - Total weight (150 lb threshold)
  - Number of boxes (4 box threshold)
  - Box dimensions (96" max for parcel)
  - Dimensional weight calculations
  
- **Smart Pallet Packing**: Layer-based algorithm that:
  - Respects 67" height constraint
  - Accounts for standard pallet sizes (48×40)
  - Handles box overhang on one dimension
  - Distributes weight evenly across pallets

- **Accurate Freight Classification**: Uses 2025 NMFC 13-tier density scale

- **Multi-Box Product Support**: Correctly handles products shipping in multiple boxes

## 🏗️ System Architecture

```
shipping_decision/
├── app.py                  # Streamlit web interface
├── product_loader.py       # CSV parsing and product data
├── calculator.py           # Freight class calculations
├── decision_engine.py      # Parcel vs Freight logic
├── pallet_builder.py       # Pallet configuration
├── main.py                 # CLI interface (optional)
├── requirements.txt        # Python dependencies
└── README_STREAMLIT.md     # This file
```

## 📝 CSV Format

Your product catalog CSV should have these columns:

| Column | Description |
|--------|-------------|
| default_code | Product SKU |
| description | Product description |
| Sequence | Box sequence (1, 2, 3...) for multi-box products |
| Length 1 | Box length in inches |
| Width 1 | Box width in inches |
| Height 1 | Box height in inches |
| Weight 1 | Box weight in pounds |

**Example:**
```csv
default_code,description,Sequence,Length 1,Width 1,Height 1,Weight 1
RPP-3828,Panel Mover,1,42,31,6,59
RPP-3828,Panel Mover,2,16,13,10,24
```

## 🔧 Configuration

### Standard Pallet Sizes
- Default: 48×40 inches (GMA standard)
- Switches to 48×48 for wider loads

### Height Constraints
- Max pallet height: 67 inches (72" total minus 5" pallet)
- Pallet weight: 50 lbs (automatically added)

### Freight Thresholds
- Weight threshold: 150 lbs
- Box count threshold: 4 boxes
- Max parcel dimension: 96 inches
- Borderline zone: 100-150 lbs

## 📈 Example Outputs

### Small Parcel Shipment
```
Decision: SMALL_PARCEL
Total Boxes: 2
Total Weight: 83 lbs

Ship as 2 separate packages:
- Package 1: 42×31×6", 59 lbs
- Package 2: 16×13×10", 24 lbs
```

### Freight Shipment
```
Decision: FREIGHT - 1 Pallet

PALLET 1:
- RPP-3908 Box 1 (56×33×8", 127 lbs) - qty 2
Pallet Dimensions: 56×40×21" (27.2 cu ft)
Total Weight: 304 lbs (254 product + 50 pallet)
Freight Class: 92.5
```

## 🚢 Deployment Options

### Streamlit Cloud (Recommended)
- ✅ Free hosting
- ✅ Automatic updates from GitHub
- ✅ HTTPS enabled
- ✅ No server management
- ⚠️ Public by default (can add authentication)

### Alternative Hosting
- **Heroku**: Free tier available
- **Railway**: $5/month, more control
- **Render**: Free tier, good performance
- **Your own server**: Full control, requires setup

## 🔒 Security Notes

- **CSV files are NOT stored** - processed in memory only
- **No data is logged** or sent to external services
- For production use with sensitive data, consider:
  - Adding password protection
  - Deploying on private infrastructure
  - Implementing user authentication

## 🐛 Troubleshooting

**App won't start:**
```bash
# Make sure you're in the right directory
cd shipping_decision

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Try running with verbose output
streamlit run app.py --logger.level=debug
```

**CSV upload fails:**
- Check CSV has all required columns
- Ensure no special characters in file path
- Verify CSV is UTF-8 encoded

**Incorrect freight class:**
- Verify box dimensions are accurate
- Check that pallet weight (50 lbs) is appropriate
- Ensure using 2025 NMFC standards

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [NMFC Classification Guide](https://nmfta.org)
- [Freight Class Calculator](https://www.freightquote.com/freight-class-density-calculator/)

## 📄 License

Internal use - Raymond Products / North Star Cart Company

## 👥 Authors

- Nate (Raymond Products) - Requirements & Testing
- Claude (Anthropic) - Implementation

## 📧 Support

For issues or questions, open an issue on GitHub or contact your system administrator.

---

**Version:** 1.0.0 - Streamlit Web App
**Last Updated:** November 2025
