"""
Streamlit Web App for Raymond Products Shipping Decision System
"""

import streamlit as st

# Direct imports (no relative imports needed)
from product_loader import ProductCatalog
from decision_engine import DecisionEngine, ShippingDecision
from pallet_builder import PalletBuilder, PalletReport


# Page configuration
st.set_page_config(
    page_title="Raymond Products - Shipping Decision",
    page_icon="📦",
    layout="wide"
)

# Initialize session state for catalog
if 'catalog' not in st.session_state:
    st.session_state.catalog = None
    st.session_state.catalog_loaded = False

# Title
st.title("📦 Raymond Products Shipping Decision System")
st.markdown("---")

# Sidebar for CSV upload
with st.sidebar:
    st.header("Configuration")
    
    uploaded_file = st.file_uploader(
        "Upload Product Catalog CSV",
        type=['csv'],
        help="Upload the Raymond Products packaging CSV file"
    )
    
    if uploaded_file is not None:
        try:
            # Save uploaded file temporarily
            temp_path = "/tmp/products.csv"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load catalog
            if not st.session_state.catalog_loaded:
                with st.spinner("Loading product catalog..."):
                    catalog = ProductCatalog()
                    catalog.load_from_csv(temp_path)
                    st.session_state.catalog = catalog
                    st.session_state.catalog_loaded = True
                    st.success(f"✓ Loaded {len(catalog)} products")
            else:
                st.success(f"✓ Catalog loaded ({len(st.session_state.catalog)} products)")
        except Exception as e:
            st.error(f"Error loading catalog: {e}")
            st.session_state.catalog_loaded = False
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool determines whether shipments should go via:
    - **Small Parcel** (UPS/FedEx)
    - **Freight** (LTL carriers)
    
    And provides pallet configurations for freight shipments.
    """)

# Main content
if st.session_state.catalog_loaded:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Product search with autocomplete
        product_list = sorted(st.session_state.catalog.products.keys())
        sku = st.selectbox(
            "Select Product SKU",
            options=product_list,
            help="Start typing to search for a product"
        )
    
    with col2:
        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            step=1
        )
    
    # Show product info
    if sku:
        product = st.session_state.catalog.get_product(sku)
        if product:
            with st.expander("📋 Product Details", expanded=False):
                st.write(f"**Description:** {product.description}")
                st.write(f"**Boxes per unit:** {product.box_count()}")
                st.write(f"**Weight per unit:** {product.total_weight():.1f} lbs")
                
                # Show box details
                for box in product.boxes:
                    st.write(f"- Box {box.sequence}: {box.length}×{box.width}×{box.height}\", {box.weight} lbs")
    
    # Calculate button
    if st.button("🚚 Calculate Shipping Method", type="primary", use_container_width=True):
        if sku and quantity > 0:
            product = st.session_state.catalog.get_product(sku)
            
            if product:
                with st.spinner("Calculating optimal shipping method..."):
                    # Make decision
                    decision = DecisionEngine.evaluate(product, quantity)
                    
                    # Display decision
                    st.markdown("---")
                    st.header("Results")
                    
                    # Decision badge
                    if decision.decision == ShippingDecision.FREIGHT:
                        st.error(f"🚛 **FREIGHT SHIPPING REQUIRED**")
                    elif decision.decision == ShippingDecision.SMALL_PARCEL:
                        st.success(f"📦 **SMALL PARCEL SHIPPING**")
                    else:
                        st.warning(f"⚠️ **BORDERLINE - REVIEW RECOMMENDED**")
                    
                    # Details
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Boxes", decision.details['total_boxes'])
                    with col2:
                        st.metric("Total Weight", f"{decision.details['total_weight']:.1f} lbs")
                    with col3:
                        st.metric("Dim Weight", f"{decision.details['dimensional_weight']:.1f} lbs")
                    with col4:
                        st.metric("Billable Weight", f"{decision.details['billable_weight']:.1f} lbs")
                    
                    # Reasoning
                    with st.expander("📊 Decision Reasoning", expanded=True):
                        for reason in decision.reasons:
                            st.write(f"• {reason}")
                    
                    # If freight, show pallet configuration
                    if decision.decision == ShippingDecision.FREIGHT:
                        st.markdown("---")
                        st.subheader("🏗️ Pallet Configuration")
                        
                        pallets = PalletBuilder.build_pallets(product, quantity)
                        
                        # Summary metrics
                        total_weight = sum(p.total_weight() for p in pallets)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Pallets", len(pallets))
                        with col2:
                            st.metric("Total Weight", f"{total_weight:.0f} lbs")
                        with col3:
                            avg_class = sum(p.freight_class() for p in pallets) / len(pallets)
                            st.metric("Avg Freight Class", f"{avg_class:.1f}")
                        
                        # Individual pallet details
                        for pallet in pallets:
                            with st.expander(f"Pallet {pallet.pallet_number}", expanded=True):
                                dims = pallet.dimensions()
                                volume = pallet.volume() / 1728  # Convert to cubic feet
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Contents:**")
                                    for box_desc, qty in sorted(pallet.box_quantities.items()):
                                        box_key_parts = box_desc.split(' Box ')
                                        seq = int(box_key_parts[1])
                                        box = next(b for b in pallet.boxes if b.sequence == seq)
                                        st.write(f"- {box_desc}")
                                        st.write(f"  └ {box.length:.1f}×{box.width:.1f}×{box.height:.1f}\", {box.weight:.0f} lbs, qty {qty}")
                                
                                with col2:
                                    st.write("**Pallet Specs:**")
                                    st.write(f"- Dimensions: {dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\"")
                                    st.write(f"- Volume: {volume:.1f} cu ft")
                                    st.write(f"- Product Weight: {pallet.total_product_weight():.0f} lbs")
                                    st.write(f"- Pallet Weight: {pallet.pallet_weight:.0f} lbs")
                                    st.write(f"- **Total Weight: {pallet.total_weight():.0f} lbs**")
                                    st.write(f"- **Freight Class: {pallet.freight_class()}**")
                    
                    # If small parcel, show box list
                    elif decision.decision == ShippingDecision.SMALL_PARCEL:
                        st.markdown("---")
                        st.subheader("📦 Small Parcel Shipment")
                        
                        st.write(f"Ship as {decision.details['total_boxes']} separate package(s):")
                        
                        box_num = 1
                        for i in range(quantity):
                            for box in product.boxes:
                                with st.expander(f"Package {box_num}: {product.sku} Box {box.sequence}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Dimensions:** {box.length:.1f}×{box.width:.1f}×{box.height:.1f}\"")
                                    with col2:
                                        st.write(f"**Weight:** {box.weight:.0f} lbs")
                                box_num += 1
            else:
                st.error("Product not found in catalog")
        else:
            st.error("Please select a product and enter quantity")

else:
    # Landing page when no catalog loaded
    st.info("👈 Please upload a product catalog CSV file to get started")
    
    st.markdown("### How to Use")
    st.markdown("""
    1. Upload your product catalog CSV file using the sidebar
    2. Select a product SKU from the dropdown
    3. Enter the quantity you want to ship
    4. Click "Calculate Shipping Method" to get recommendations
    
    The system will determine if your shipment should go via small parcel or freight,
    and provide detailed pallet configurations for freight shipments.
    """)
    
    st.markdown("### CSV Format Required")
    st.code("""
    default_code,description,Sequence,Length 1,Width 1,Height 1,Weight 1
    RPP-3828,Panel Mover,1,42,31,6,59
    RPP-3828,Panel Mover,2,16,13,10,24
    """)
