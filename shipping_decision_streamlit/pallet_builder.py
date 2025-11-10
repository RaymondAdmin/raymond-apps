"""
Pallet Builder Module
Distributes boxes across pallets and calculates final pallet configurations
"""

from typing import List, Dict
from product_loader import Box, Product
from calculator import ShipmentCalculator, FreightCalculator


class Pallet:
    """Represents a single pallet with boxes"""
    
    def __init__(self, pallet_number: int, pallet_weight: float = 50):
        self.pallet_number = pallet_number
        self.pallet_weight = pallet_weight
        self.boxes: List[Box] = []
        self.box_quantities: Dict[str, int] = {}  # Track quantities by box description
    
    def add_box(self, box: Box, product_sku: str):
        """Add a box to this pallet"""
        self.boxes.append(box)
        
        # Track quantity
        box_key = f"{product_sku} Box {box.sequence}"
        self.box_quantities[box_key] = self.box_quantities.get(box_key, 0) + 1
    
    def total_product_weight(self) -> float:
        """Total weight of products (excluding pallet)"""
        return sum(box.weight for box in self.boxes)
    
    def total_weight(self) -> float:
        """Total weight including pallet"""
        return self.total_product_weight() + self.pallet_weight
    
    def dimensions(self) -> tuple:
        """
        Calculate pallet dimensions (L, W, H)
        
        Logic:
        - Start with standard pallet base (48×48 is most common, 40×48 for smaller loads)
        - Boxes can overhang on ONE dimension, not both
        - Height is sum of box heights + 5" pallet base
        """
        if not self.boxes:
            return (40, 48, 5)  # Empty pallet
        
        max_box_length = max(box.length for box in self.boxes)
        max_box_width = max(box.width for box in self.boxes)
        total_height = sum(box.height for box in self.boxes) + 5  # Add pallet height
        
        # Determine pallet base size
        # Use 48×40 (GMA standard) as default
        # Use 48×48 if load needs the extra width
        if max_box_width > 40:
            pallet_base_l = 48
            pallet_base_w = 48
        else:
            pallet_base_l = 48
            pallet_base_w = 40
        
        # Calculate final dimensions with overhang rules
        # Can overhang on one dimension, not both
        final_length = max(max_box_length, pallet_base_l)
        final_width = max(max_box_width, pallet_base_w)
        
        # If both dimensions overhang, use the larger overhang and constrain the other
        length_overhang = max_box_length - pallet_base_l
        width_overhang = max_box_width - pallet_base_w
        
        if length_overhang > 0 and width_overhang > 0:
            # Both would overhang - pick the dimension with more overhang
            if length_overhang > width_overhang:
                # Let length overhang, constrain width to pallet
                final_length = max_box_length
                final_width = pallet_base_w
            else:
                # Let width overhang, constrain length to pallet
                final_length = pallet_base_l
                final_width = max_box_width
        
        return (final_length, final_width, total_height)
    
    def volume(self) -> float:
        """Calculate total volume in cubic inches"""
        dims = self.dimensions()
        return dims[0] * dims[1] * dims[2]
    
    def freight_class(self) -> int:
        """Calculate freight class for this pallet"""
        density = FreightCalculator.calculate_density(self.total_weight(), self.volume())
        return FreightCalculator.get_freight_class(density)
    
    def __repr__(self):
        dims = self.dimensions()
        return f"Pallet {self.pallet_number}: {len(self.boxes)} boxes, {self.total_weight():.0f} lbs, {dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\""


class PalletBuilder:
    """Builds pallet configurations for freight shipments"""
    
    MAX_PALLET_HEIGHT = 67  # inches (72 total - 5 for pallet)
    PALLET_WEIGHT = 50  # lbs
    
    @staticmethod
    def build_pallets(product: Product, quantity: int) -> List[Pallet]:
        """
        Distribute boxes across pallets
        
        Strategy:
        1. Generate all boxes for the order
        2. Sort by weight (heaviest first for bottom placement)
        3. Distribute evenly across minimum number of pallets needed
        
        Args:
            product: The product being shipped
            quantity: Number of units
            
        Returns:
            List of Pallet objects
        """
        # Generate all boxes for this order
        all_boxes = []
        for i in range(quantity):
            for box in product.boxes:
                all_boxes.append(box)
        
        # Sort boxes by weight (heaviest first)
        all_boxes.sort(key=lambda b: b.weight, reverse=True)
        
        # Calculate how many pallets we need based on height constraint
        pallets_needed = PalletBuilder._calculate_pallets_needed(all_boxes)
        
        # Create pallets
        pallets = [Pallet(i + 1, PalletBuilder.PALLET_WEIGHT) for i in range(pallets_needed)]
        
        # Distribute boxes evenly across pallets
        if pallets_needed == 1:
            # Single pallet - just stack everything
            for box in all_boxes:
                pallets[0].add_box(box, product.sku)
        else:
            # Multiple pallets - distribute evenly by weight
            PalletBuilder._distribute_boxes_evenly(pallets, all_boxes, product.sku)
        
        return pallets
    
    @staticmethod
    def _calculate_pallets_needed(boxes: List[Box]) -> int:
        """
        Calculate minimum number of pallets needed using layer-based packing logic
        
        Logic:
        1. Check if any single box exceeds height limit (can't stack)
        2. Calculate how many boxes fit per layer on standard pallet
        3. Calculate max layers within height constraint
        4. Determine boxes per pallet = boxes_per_layer × max_layers
        5. Calculate total pallets needed
        """
        if not boxes:
            return 1
        
        # Check for oversized boxes that exceed height limit
        oversized_boxes = [box for box in boxes if box.height > PalletBuilder.MAX_PALLET_HEIGHT]
        
        if oversized_boxes:
            # Can't stack these boxes - need one pallet per box
            return len(boxes)
        
        # All boxes are same product, so use first box dimensions
        sample_box = boxes[0]
        box_length = sample_box.length
        box_width = sample_box.width
        box_height = sample_box.height
        
        # Standard pallet dimensions
        pallet_length = 48
        pallet_width = 40
        
        # Calculate boxes per layer - try both orientations
        # Orientation 1: box length along pallet length
        boxes_along_length_1 = int(pallet_length / box_length)
        boxes_along_width_1 = int(pallet_width / box_width)
        boxes_per_layer_1 = boxes_along_length_1 * boxes_along_width_1
        
        # Orientation 2: box length along pallet width (rotated 90°)
        boxes_along_length_2 = int(pallet_length / box_width)
        boxes_along_width_2 = int(pallet_width / box_length)
        boxes_per_layer_2 = boxes_along_length_2 * boxes_along_width_2
        
        # Use the orientation that fits more boxes per layer
        boxes_per_layer = max(boxes_per_layer_1, boxes_per_layer_2)
        
        # If no boxes fit side-by-side, it's 1 per layer
        if boxes_per_layer == 0:
            boxes_per_layer = 1
        
        # Calculate max layers within height constraint
        max_layers = int(PalletBuilder.MAX_PALLET_HEIGHT / box_height)
        
        if max_layers == 0:
            max_layers = 1
        
        # Calculate boxes per pallet
        boxes_per_pallet = boxes_per_layer * max_layers
        
        # Calculate total pallets needed
        total_boxes = len(boxes)
        pallets_needed = (total_boxes + boxes_per_pallet - 1) // boxes_per_pallet  # Ceiling division
        
        return max(1, pallets_needed)
    
    @staticmethod
    def _distribute_boxes_evenly(pallets: List[Pallet], boxes: List[Box], product_sku: str):
        """
        Distribute boxes evenly across pallets
        Uses round-robin approach to balance weight
        """
        # Sort pallets by current weight (for balancing)
        for i, box in enumerate(boxes):
            # Find lightest pallet
            lightest_pallet = min(pallets, key=lambda p: p.total_weight())
            
            # Check if adding this box would exceed height limit
            potential_height = sum(b.height for b in lightest_pallet.boxes) + box.height + 5
            
            if potential_height > PalletBuilder.MAX_PALLET_HEIGHT:
                # Find next available pallet
                for pallet in sorted(pallets, key=lambda p: p.total_weight()):
                    check_height = sum(b.height for b in pallet.boxes) + box.height + 5
                    if check_height <= PalletBuilder.MAX_PALLET_HEIGHT:
                        pallet.add_box(box, product_sku)
                        break
                else:
                    # No pallet has room - add to lightest anyway (edge case)
                    lightest_pallet.add_box(box, product_sku)
            else:
                lightest_pallet.add_box(box, product_sku)


class PalletReport:
    """Generates a formatted report of pallet configuration"""
    
    @staticmethod
    def generate(product: Product, quantity: int, pallets: List[Pallet]) -> str:
        """Generate a formatted report of the pallet configuration"""
        
        lines = []
        lines.append(f"Order: {quantity}x {product.sku}")
        lines.append(f"Product: {product.description}")
        lines.append("")
        lines.append(f"RECOMMENDATION: FREIGHT - {len(pallets)} Pallet{'s' if len(pallets) > 1 else ''}")
        lines.append("")
        
        for pallet in pallets:
            lines.append(f"PALLET {pallet.pallet_number}:")
            
            # Group and display boxes by type
            for box_desc, qty in sorted(pallet.box_quantities.items()):
                # Find a box to get dimensions
                box_key_parts = box_desc.split(' Box ')
                seq = int(box_key_parts[1])
                box = next(b for b in pallet.boxes if b.sequence == seq)
                
                lines.append(f"  - {box_desc} ({box.length:.1f}×{box.width:.1f}×{box.height:.1f}\", {box.weight:.0f} lbs) - qty {qty}")
            
            dims = pallet.dimensions()
            volume_cubic_inches = dims[0] * dims[1] * dims[2]
            volume_cubic_feet = volume_cubic_inches / 1728
            lines.append(f"  Pallet Dimensions: {dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\" ({volume_cubic_feet:.1f} cu ft)")
            lines.append(f"  Total Weight: {pallet.total_weight():.0f} lbs ({pallet.total_product_weight():.0f} product + {pallet.pallet_weight:.0f} pallet)")
            lines.append(f"  Freight Class: {pallet.freight_class()}")
            lines.append("")
        
        # Summary
        total_weight = sum(p.total_weight() for p in pallets)
        lines.append(f"TOTAL SHIPMENT: {len(pallets)} pallet{'s' if len(pallets) > 1 else ''}, {total_weight:.0f} lbs")
        
        return "\n".join(lines)
