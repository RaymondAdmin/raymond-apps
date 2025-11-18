"""
Raymond Products Pallet Optimizer - Streamlit Application
"""
import streamlit as st
import sys
sys.path.insert(0, '/home/claude/pallet_optimizer')

from utils.product_loader import ProductLoader
from core.pallet_builder import PalletBuilder
from core.models import Product

# Page config
st.set_page_config(
    page_title="Raymond Pallet Optimizer",
    page_icon="📦",
    layout="wide"
)

# Initialize session state
if 'catalog' not in st.session_state:
    st.session_state.catalog = None
if 'order_items' not in st.session_state:
    st.session_state.order_items = []
if 'pallets' not in st.session_state:
    st.session_state.pallets = None

# Title
st.title("📦 Raymond Products Pallet Optimizer")
st.markdown("### EB-AFIT Algorithm with NMFC Freight Class Calculation")
st.markdown("---")

# Sidebar - Configuration
with st.sidebar:
    st.header("Configuration")
    
    # CSV Upload
    uploaded_file = st.file_uploader(
        "Upload Product Catalog CSV",
        type=['csv'],
        help="Upload Raymond packaging CSV file"
    )
    
    if uploaded_file is not None:
        try:
            # Save to temp file
            temp_path = "/tmp/raymond_products.csv"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load catalog
            if st.session_state.catalog is None:
                with st.spinner("Loading product catalog..."):
                    catalog = ProductLoader.load_from_csv(temp_path)
                    st.session_state.catalog = catalog
                    st.success(f"✓ Loaded {len(catalog)} products")
            else:
                st.success(f"✓ {len(st.session_state.catalog)} products loaded")
        except Exception as e:
            st.error(f"Error loading catalog: {e}")
    
    st.markdown("---")
    
    # Pallet size selector
    st.subheader("Pallet Configuration")
    pallet_size = st.selectbox(
        "Pallet Size",
        options=['GMA_40x48', 'GMA_48x48', 'EUR'],
        format_func=lambda x: {
            'GMA_40x48': 'GMA 40×48 (48"×40"×91")',
            'GMA_48x48': 'GMA 48×48 (48"×48"×91")',
            'EUR': 'EUR Pallet (47.24"×39.37"×91")'
        }[x],
        help="Select pallet size for optimization"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool uses the **EB-AFIT algorithm** to optimize pallet configurations.
    
    Features:
    - Layer-based packing
    - Mixed orientations
    - NMFC freight class with 75" rule
    - Multi-product orders
    """)

# Main content
if st.session_state.catalog is not None:
    # Product selection
    st.header("Order Configuration")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Get sorted SKU list
        sku_list = sorted(st.session_state.catalog.keys())
        selected_sku = st.selectbox(
            "Select Product",
            options=sku_list,
            help="Start typing to search"
        )
    
    with col2:
        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            step=1
        )
    
    with col3:
        if st.button("➕ Add to Order", use_container_width=True):
            if selected_sku:
                product = st.session_state.catalog[selected_sku]
                st.session_state.order_items.append({
                    'sku': selected_sku,
                    'product': product,
                    'quantity': quantity
                })
                st.rerun()
    
    # Show product info
    if selected_sku:
        product = st.session_state.catalog[selected_sku]
        with st.expander("📋 Product Details", expanded=False):
            st.write(f"**Description:** {product.description}")
            st.write(f"**Boxes per unit:** {product.box_count()}")
            st.write(f"**Weight per unit:** {product.total_weight():.1f} lbs")
            
            for box in product.boxes:
                st.write(f"- Box {box.sequence}: {box.length}×{box.width}×{box.height}\", {box.weight} lbs")
    
    # Display current order
    if st.session_state.order_items:
        st.markdown("---")
        st.subheader("Current Order")
        
        # Order table
        for idx, item in enumerate(st.session_state.order_items):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{item['sku']}**")
                st.caption(item['product'].description[:50] + "..." if len(item['product'].description) > 50 else item['product'].description)
            
            with col2:
                st.metric("Qty", item['quantity'])
            
            with col3:
                st.metric("Boxes", item['product'].box_count() * item['quantity'])
            
            with col4:
                st.metric("Weight", f"{item['product'].total_weight() * item['quantity']:.0f} lbs")
            
            with col5:
                if st.button("🗑️", key=f"remove_{idx}", use_container_width=True):
                    st.session_state.order_items.pop(idx)
                    st.session_state.pallets = None
                    st.rerun()
        
        # Calculate button
        st.markdown("---")
        if st.button("🚀 Calculate Pallet Configuration", type="primary", use_container_width=True):
            with st.spinner("Optimizing pallet configuration..."):
                # Extract products and quantities
                products = [item['product'] for item in st.session_state.order_items]
                quantities = [item['quantity'] for item in st.session_state.order_items]
                
                # Build pallets
                pallets = PalletBuilder.build_pallets(products, quantities, pallet_size)
                st.session_state.pallets = pallets
            
            st.success(f"✅ Optimized: {len(pallets)} pallet(s)")
    
    # Display results
    if st.session_state.pallets:
        st.markdown("---")
        st.header("🎯 Pallet Configuration Results")
        
        pallets = st.session_state.pallets
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_weight = sum(p.weight_total for p in pallets)
        total_boxes = sum(len(p.boxes) for p in pallets)
        avg_class = sum(p.freight_class for p in pallets) / len(pallets)
        avg_util = sum(p.utilization for p in pallets) / len(pallets)
        
        with col1:
            st.metric("Total Pallets", len(pallets))
        with col2:
            st.metric("Total Boxes", total_boxes)
        with col3:
            st.metric("Total Weight", f"{total_weight:.0f} lbs")
        with col4:
            st.metric("Avg Freight Class", f"{avg_class:.1f}")
        
        # Quick copy/paste summary
        st.markdown("---")
        st.subheader("📋 Quick Reference (Copy/Paste Ready)")
        
        summary_lines = [f"**Pallet Count:** {len(pallets)}", ""]
        for pallet in pallets:
            dims = pallet.dimensions
            note = f" {pallet.freight_class_note}" if pallet.freight_class_note else ""
            summary_lines.append(
                f"**Pallet {pallet.pallet_number}:** "
                f"{dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\"{note} @ {pallet.weight_total:.0f} lbs, "
                f"Class {pallet.freight_class}, "
                f"Utilization {pallet.utilization:.1f}%"
            )
        
        st.code("\n".join(summary_lines), language=None)
        
        # Detailed pallet breakdown
        st.markdown("---")
        st.subheader("📦 Detailed Pallet Configuration")
        
        for pallet in pallets:
            with st.expander(f"Pallet {pallet.pallet_number} - {len(pallet.boxes)} boxes", expanded=True):
                dims = pallet.dimensions
                
                # Two columns: specs and contents
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Pallet Specifications:**")
                    st.write(f"- Dimensions: {dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\"")
                    st.write(f"- Volume: {pallet.volume_cuft:.1f} cu ft")
                    st.write(f"- Utilization: {pallet.utilization:.1f}%")
                    st.write(f"- Product Weight: {pallet.weight_product:.0f} lbs")
                    st.write(f"- Pallet Weight: {pallet.weight_pallet:.0f} lbs")
                    st.write(f"- **Total Weight: {pallet.weight_total:.0f} lbs**")
                    st.write(f"- **Freight Class: {pallet.freight_class}**")
                    
                    if pallet.freight_class_note:
                        st.warning(f"⚠️ {pallet.freight_class_note}")
                
                with col2:
                    st.markdown("**Box Contents:**")
                    
                    # Group boxes by SKU and sequence
                    box_summary = {}
                    for placed in pallet.boxes:
                        key = f"{placed.box.product_sku} Box {placed.box.sequence}"
                        if key not in box_summary:
                            box_summary[key] = {
                                'box': placed.box,
                                'count': 0
                            }
                        box_summary[key]['count'] += 1
                    
                    for key, info in sorted(box_summary.items()):
                        box = info['box']
                        count = info['count']
                        st.write(f"- {key} (qty: {count})")
                        st.write(f"  └ {box.length}×{box.width}×{box.height}\", {box.weight} lbs each")

else:
    # Landing page
    st.info("👈 Please upload a product catalog CSV file to get started")
    
    st.markdown("### How to Use")
    st.markdown("""
    1. **Upload CSV** - Use the sidebar to upload your product packaging CSV
    2. **Select Products** - Choose products and quantities for your order
    3. **Add to Order** - Build up your complete order
    4. **Calculate** - Click "Calculate Pallet Configuration" to optimize
    5. **Review** - See detailed pallet configurations with freight classes
    
    The system uses the **EB-AFIT algorithm** (Enhanced from Air Force thesis) to create
    optimal pallet configurations with accurate NMFC freight class calculations.
    """)
    
    st.markdown("### CSV Format Required")
    st.code("""
default_code,description,Sequence,Length 1,Width 1,Height 1,Weight 1
RPP-3828,Panel Mover,1,42,31,6,59
RPP-3828,Panel Mover,2,16,13,10,24
RPP-550US,Small Cart,1,38,28,12,32
    """, language="csv")
