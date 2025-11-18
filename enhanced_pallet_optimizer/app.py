import streamlit as st
import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import Box, Product
from pallet_builder import PalletBuilder

st.set_page_config(page_title="Pallet Optimizer", page_icon="📦", layout="wide")

st.title("📦 Pallet Optimization System")

# Sidebar for product configuration
st.sidebar.header("Product Configuration")

product_sku = st.sidebar.text_input("Product SKU", value="RPP-3828")
product_description = st.sidebar.text_input("Product Description", value="Panel Mover")
quantity = st.sidebar.number_input("Quantity", min_value=1, value=3, step=1)

pallet_size = st.sidebar.selectbox(
    "Pallet Size",
    options=["GMA_40", "GMA_48", "EUR"],
    index=0,
    help="GMA_40: 48×40\" (most common), GMA_48: 48×48\" (square), EUR: 47.24×39.37\" (European)"
)

st.sidebar.markdown("---")
st.sidebar.header("Box Specifications")

num_boxes = st.sidebar.number_input("Number of box types", min_value=1, max_value=5, value=2, step=1)

boxes = []
for i in range(num_boxes):
    st.sidebar.markdown(f"**Box {i+1}**")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        length = st.number_input(f"Length (in)", min_value=1.0, value=42.0 if i == 0 else 16.0, step=0.5, key=f"len_{i}")
        width = st.number_input(f"Width (in)", min_value=1.0, value=31.0 if i == 0 else 13.0, step=0.5, key=f"wid_{i}")
    
    with col2:
        height = st.number_input(f"Height (in)", min_value=1.0, value=6.0 if i == 0 else 10.0, step=0.5, key=f"hgt_{i}")
        weight = st.number_input(f"Weight (lbs)", min_value=0.1, value=59.0 if i == 0 else 24.0, step=0.5, key=f"wgt_{i}")
    
    boxes.append(Box(
        length=length,
        width=width,
        height=height,
        weight=weight,
        sequence=i+1
    ))

# Build button
if st.sidebar.button("🚀 Build Pallets", type="primary"):
    # Create product
    product = Product(
        sku=product_sku,
        description=product_description,
        boxes=boxes
    )
    
    # Build pallets
    with st.spinner("Building optimal pallet configuration..."):
        builder = PalletBuilder(pallet_size=pallet_size)
        pallets = builder.build_pallets(product, quantity=quantity)
    
    # Store in session state
    st.session_state.pallets = pallets
    st.session_state.builder = builder
    st.session_state.product = product

# Display results
if 'pallets' in st.session_state:
    pallets = st.session_state.pallets
    builder = st.session_state.builder
    product = st.session_state.product
    
    # Summary
    st.success(f"✅ Optimized configuration: **{len(pallets)} pallet(s)** for {quantity} units")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Boxes", sum(p.box_count() for p in pallets))
    with col2:
        st.metric("Total Weight", f"{sum(p.total_weight() for p in pallets):.0f} lbs")
    with col3:
        st.metric("Product Weight", f"{sum(p.product_weight() for p in pallets):.0f} lbs")
    
    # Show each pallet
    for pallet in pallets:
        summary = builder.get_pallet_summary(pallet)
        
        with st.expander(f"📦 Pallet {summary['pallet_number']}", expanded=True):
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Dimensions", 
                         f"{summary['dimensions']['length']:.0f}×{summary['dimensions']['width']:.0f}×{summary['dimensions']['height']:.0f}\"")
            with col2:
                st.metric("Total Weight", f"{summary['weight']['total']:.0f} lbs")
            with col3:
                st.metric("Freight Class", summary['freight']['freight_class'])
            with col4:
                grade_color = {
                    "A - Excellent": "🟢",
                    "B - Good": "🟢", 
                    "C - Acceptable": "🟡",
                    "D - Poor": "🟠",
                    "F - Dangerous": "🔴"
                }
                grade = summary['stability']['grade']
                st.metric("Stability", f"{grade_color.get(grade, '⚪')} {grade.split(' - ')[0]}")
            
            # Detailed tabs
            tab1, tab2, tab3 = st.tabs(["📊 Freight Details", "🔒 Stability Analysis", "📦 Box Placement"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Weight & Volume**")
                    st.write(f"• Product: {summary['weight']['product']:.0f} lbs")
                    st.write(f"• Pallet: {summary['weight']['pallet']:.0f} lbs")
                    st.write(f"• Total: {summary['weight']['total']:.0f} lbs")
                    st.write(f"• Density: {summary['freight']['density']:.2f} lbs/cu ft")
                
                with col2:
                    st.write("**Freight Classification**")
                    st.write(f"• Class: {summary['freight']['freight_class']}")
                    if summary['freight']['penalty_applied']:
                        st.warning("⚠️ 75\" Rule Applied")
                        st.write(f"• Actual: {summary['freight']['actual_volume_cf']:.1f} cu ft")
                        st.write(f"• Calculated: {summary['freight']['calculated_volume_cf']:.1f} cu ft")
                    else:
                        st.write(f"• Volume: {summary['freight']['actual_volume_cf']:.1f} cu ft")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Stability Metrics**")
                    st.write(f"• Grade: {summary['stability']['grade']}")
                    st.write(f"• COG Height: {summary['stability']['cog_percentage']:.1f}% of total")
                    st.write(f"• Bottom Weight: {summary['stability']['bottom_weight_pct']:.1f}%")
                    st.write(f"• Safe to Ship: {'✅ YES' if summary['stability']['safe_to_ship'] else '❌ NO'}")
                
                with col2:
                    if summary['stability']['warnings']:
                        st.warning("**⚠️ Warnings**")
                        for warning in summary['stability']['warnings']:
                            st.write(f"• {warning}")
                    else:
                        st.success("**✅ No Warnings**")
            
            with tab3:
                layers = pallet.layers()
                
                for layer_num in sorted(layers.keys()):
                    st.write(f"**Layer {layer_num + 1}** (Z: {layers[layer_num][0].z:.0f}\")")
                    
                    for pb in layers[layer_num]:
                        dims = pb.box.rotated_dimensions(pb.rotation)
                        rotation_str = " (rotated)" if pb.rotation.value != 0 else ""
                        
                        st.write(
                            f"• Box {pb.box.sequence}: "
                            f"{dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\" "
                            f"@ ({pb.x:.0f}, {pb.y:.0f}) "
                            f"- {pb.box.weight:.0f} lbs{rotation_str}"
                        )

else:
    st.info("👈 Configure your product and click 'Build Pallets' to start")
    
    # Show example
    with st.expander("📖 Example: RPP-3828 Panel Mover"):
        st.write("""
        **Product:** Panel Mover with 8" Poly Casters
        
        **Boxes per unit:**
        - Box 1: 42×31×6", 59 lbs
        - Box 2: 16×13×10", 24 lbs
        
        **Quantity:** 3 units (6 total boxes, 249 lbs)
        
        This example demonstrates:
        - Multi-box products
        - Height grouping optimization
        - Freight class calculation with 75" rule
        - Stability analysis
        """)
