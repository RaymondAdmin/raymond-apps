"""
Enhanced Pallet Builder
Implements height grouping, layer optimization, and intelligent box placement
"""

from typing import List, Dict, Tuple, Optional
from models import (
    Box, PlacedBox, Product, PalletConfiguration, 
    Rotation, StabilityReport
)
from stability_analyzer import StabilityAnalyzer
from freight_calculator import FreightCalculator
import copy


class PalletBuilder:
    """
    Advanced pallet configuration builder
    
    Features:
    - Height grouping for efficient layer filling
    - Orientation optimization (tries both L×W and W×L)
    - Weight-balanced multi-pallet distribution
    - Stability validation
    - NMFC freight class calculation with 75" rule
    """
    
    # Constants
    MAX_PALLET_HEIGHT = 91  # inches (96 total - 5 pallet base)
    PALLET_BASE_HEIGHT = 5   # inches
    PALLET_WEIGHT = 50      # lbs
    
    # Standard pallet sizes (GMA standards)
    PALLET_SIZES = {
        'GMA_40': (48, 40),  # 48×40 - Most common
        'GMA_48': (48, 48),  # 48×48 - Square/wide loads
        'EUR': (47.24, 39.37)  # European standard
    }
    
    def __init__(self, pallet_size: str = 'GMA_40'):
        """
        Initialize pallet builder
        
        Args:
            pallet_size: Pallet size identifier ('GMA_40', 'GMA_48', 'EUR')
        """
        if pallet_size not in self.PALLET_SIZES:
            raise ValueError(f"Unknown pallet size: {pallet_size}. Use one of {list(self.PALLET_SIZES.keys())}")
        
        self.pallet_length, self.pallet_width = self.PALLET_SIZES[pallet_size]
        self.pallet_size_name = pallet_size
    
    def build_pallets(self, product: Product, quantity: int) -> List[PalletConfiguration]:
        """
        Main entry point: Build optimal pallet configuration for an order
        
        Args:
            product: Product definition with box specifications
            quantity: Number of units to pack
            
        Returns:
            List of PalletConfiguration objects
        """
        # Step 1: Generate all boxes for this order
        all_boxes = self._generate_boxes(product, quantity)
        
        # Step 2: Group boxes by height for efficient processing
        height_groups = self._group_by_height(all_boxes)
        
        # Step 3: Sort boxes for optimal placement
        sorted_boxes = self._sort_boxes_for_packing(all_boxes)
        
        # Step 4: Calculate minimum pallets needed
        pallets_needed = self._calculate_pallets_needed(sorted_boxes, height_groups)
        
        # Step 5: Create pallet configurations
        pallets = self._create_initial_pallets(pallets_needed)
        
        # Step 6: Distribute boxes across pallets using height-aware algorithm
        self._distribute_boxes_by_height(pallets, sorted_boxes, height_groups)
        
        # Step 7: Validate and optimize
        pallets = self._validate_and_optimize(pallets)
        
        return pallets
    
    def _generate_boxes(self, product: Product, quantity: int) -> List[Box]:
        """Generate all boxes for the order"""
        all_boxes = []
        for i in range(quantity):
            for box in product.boxes:
                # Create a copy with product SKU
                box_copy = copy.copy(box)
                box_copy.product_sku = product.sku
                all_boxes.append(box_copy)
        return all_boxes
    
    def _group_by_height(self, boxes: List[Box]) -> Dict[float, List[Box]]:
        """
        Group boxes by height for efficient layer filling
        
        This is the key optimization from freight-pallet-calc repo
        """
        groups = {}
        for box in boxes:
            h = box.height
            if h not in groups:
                groups[h] = []
            groups[h].append(box)
        
        # Sort each height group by footprint (descending)
        # Larger boxes get placed first
        for height in groups:
            groups[height].sort(key=lambda b: b.footprint(), reverse=True)
        
        return groups
    
    def _sort_boxes_for_packing(self, boxes: List[Box]) -> List[Box]:
        """
        Sort boxes for optimal packing order
        
        Priority:
        1. Height (tallest first - go on bottom)
        2. Weight (heaviest first - stability)
        3. Footprint (largest first - efficiency)
        """
        return sorted(boxes, 
                     key=lambda b: (b.height, b.weight, b.footprint()), 
                     reverse=True)
    
    def _calculate_pallets_needed(self, boxes: List[Box], height_groups: Dict[float, List[Box]]) -> int:
        """
        Calculate minimum number of pallets needed
        
        Uses height groups to accurately estimate capacity
        """
        if not boxes:
            return 1
        
        # Check for oversized boxes
        oversized = [b for b in boxes if b.height > self.MAX_PALLET_HEIGHT]
        if oversized:
            return len(boxes)  # Each needs its own pallet
        
        # Estimate capacity using height groups
        boxes_per_pallet = 0
        current_height = 0
        sorted_heights = sorted(height_groups.keys(), reverse=True)
        
        for height in sorted_heights:
            boxes_in_group = height_groups[height]
            
            # How many layers of this height fit?
            remaining_height = self.MAX_PALLET_HEIGHT - current_height
            layers_possible = int(remaining_height / height)
            
            if layers_possible == 0:
                break
            
            # How many boxes per layer?
            # Use smallest box in group for conservative estimate
            sample_box = min(boxes_in_group, key=lambda b: b.footprint())
            boxes_per_layer = self._estimate_boxes_per_layer(sample_box)
            
            # Total boxes that fit from this height group
            boxes_this_height = min(len(boxes_in_group), boxes_per_layer * layers_possible)
            boxes_per_pallet += boxes_this_height
            
            # Update height
            layers_used = (boxes_this_height + boxes_per_layer - 1) // boxes_per_layer
            current_height += layers_used * height
        
        if boxes_per_pallet == 0:
            return len(boxes)
        
        # Calculate total pallets
        pallets_needed = (len(boxes) + boxes_per_pallet - 1) // boxes_per_pallet
        return max(1, pallets_needed)
    
    def _estimate_boxes_per_layer(self, sample_box: Box) -> int:
        """
        Estimate how many boxes fit in one layer
        
        Tries both orientations and returns the better fit
        """
        # Orientation 1: Normal (L×W)
        opt1_l = int(self.pallet_length / sample_box.length)
        opt1_w = int(self.pallet_width / sample_box.width)
        count1 = opt1_l * opt1_w
        
        # Orientation 2: Rotated 90° (W×L)
        opt2_l = int(self.pallet_length / sample_box.width)
        opt2_w = int(self.pallet_width / sample_box.length)
        count2 = opt2_l * opt2_w
        
        return max(count1, count2, 1)
    
    def _create_initial_pallets(self, count: int) -> List[PalletConfiguration]:
        """Create empty pallet configurations"""
        pallets = []
        for i in range(count):
            pallet = PalletConfiguration(
                pallet_number=i + 1,
                placed_boxes=[],
                pallet_base_length=self.pallet_length,
                pallet_base_width=self.pallet_width,
                pallet_height=self.PALLET_BASE_HEIGHT,
                pallet_weight=self.PALLET_WEIGHT
            )
            pallets.append(pallet)
        return pallets
    
    def _distribute_boxes_by_height(
        self, 
        pallets: List[PalletConfiguration], 
        boxes: List[Box],
        height_groups: Dict[float, List[Box]]
    ):
        """
        Distribute boxes across pallets using height-aware algorithm
        
        Strategy:
        - Process height groups from tallest to shortest
        - Within each height group, try to form complete layers
        - Balance weight across pallets
        """
        # Track which boxes have been placed
        placed_boxes_ids = set()
        
        # Process height groups from tallest to shortest
        sorted_heights = sorted(height_groups.keys(), reverse=True)
        
        for height in sorted_heights:
            boxes_in_group = [b for b in height_groups[height] 
                             if id(b) not in placed_boxes_ids]
            
            # Try to place boxes in this height group
            for box in boxes_in_group:
                # Find best pallet for this box
                best_pallet = self._find_best_pallet_for_box(pallets, box)
                
                if best_pallet:
                    # Place the box
                    position = self._find_placement_position(best_pallet, box)
                    if position:
                        placed_box = PlacedBox(
                            box=box,
                            x=position[0],
                            y=position[1],
                            z=position[2],
                            rotation=position[3],
                            layer=position[4]
                        )
                        best_pallet.placed_boxes.append(placed_box)
                        placed_boxes_ids.add(id(box))
    
    def _find_best_pallet_for_box(
        self, 
        pallets: List[PalletConfiguration], 
        box: Box
    ) -> Optional[PalletConfiguration]:
        """
        Find the best pallet to place this box
        
        Criteria:
        1. Must have enough height remaining
        2. Prefer pallet with most remaining height (fill evenly)
        3. Consider weight balance
        """
        candidates = []
        
        for pallet in pallets:
            current_height = max([pb.get_bounds()[5] for pb in pallet.placed_boxes], 
                                default=self.PALLET_BASE_HEIGHT)
            remaining_height = self.MAX_PALLET_HEIGHT + self.PALLET_BASE_HEIGHT - current_height
            
            if remaining_height >= box.height:
                # Calculate score (prefer more remaining height and lighter pallets)
                score = remaining_height - (pallet.total_weight() / 100)
                candidates.append((pallet, score))
        
        if not candidates:
            return None
        
        # Return pallet with highest score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def _find_placement_position(
        self, 
        pallet: PalletConfiguration, 
        box: Box
    ) -> Optional[Tuple[float, float, float, Rotation, int]]:
        """
        Find optimal placement position for a box on a pallet
        
        Returns: (x, y, z, rotation, layer) or None if can't place
        
        Strategy:
        1. Determine current layer height
        2. Try to place on current layer if space available
        3. Otherwise, start new layer
        4. Try both orientations and pick best fit
        """
        if not pallet.placed_boxes:
            # First box - place at origin
            return (0, 0, self.PALLET_BASE_HEIGHT, Rotation.NONE, 0)
        
        # Find current top height and layer
        max_z = max(pb.get_bounds()[5] for pb in pallet.placed_boxes)
        current_layer = max(pb.layer for pb in pallet.placed_boxes)
        
        # Get boxes in current layer
        current_layer_boxes = [pb for pb in pallet.placed_boxes if pb.layer == current_layer]
        current_layer_height = max(pb.get_bounds()[5] for pb in current_layer_boxes)
        
        # Try to place on current layer first
        position = self._try_place_on_layer(pallet, box, current_layer, current_layer_boxes)
        if position:
            return position
        
        # Start new layer
        new_layer = current_layer + 1
        new_z = current_layer_height
        
        # Check if new layer would exceed height limit
        if new_z + box.height > self.MAX_PALLET_HEIGHT + self.PALLET_BASE_HEIGHT:
            return None  # Can't fit
        
        # Place at start of new layer
        return (0, 0, new_z, Rotation.NONE, new_layer)
    
    def _try_place_on_layer(
        self, 
        pallet: PalletConfiguration,
        box: Box,
        layer: int,
        layer_boxes: List[PlacedBox]
    ) -> Optional[Tuple[float, float, float, Rotation, int]]:
        """
        Try to place box on an existing layer
        
        Uses a simple left-to-right, front-to-back strategy
        """
        if not layer_boxes:
            return None
        
        # Get layer Z position
        layer_z = layer_boxes[0].z
        
        # Find rightmost extent
        max_x = max(pb.get_bounds()[1] for pb in layer_boxes)
        
        # Try normal orientation
        if max_x + box.length <= self.pallet_length:
            # Fits to the right
            return (max_x, 0, layer_z, Rotation.NONE, layer)
        
        # Try rotated orientation
        if max_x + box.width <= self.pallet_length:
            return (max_x, 0, layer_z, Rotation.ROTATE_90, layer)
        
        # Doesn't fit on this layer
        return None
    
    def _validate_and_optimize(
        self, 
        pallets: List[PalletConfiguration]
    ) -> List[PalletConfiguration]:
        """
        Validate pallet configurations and apply optimizations
        
        Returns optimized pallets
        """
        # Remove empty pallets
        pallets = [p for p in pallets if p.placed_boxes]
        
        # Renumber pallets
        for i, pallet in enumerate(pallets):
            pallet.pallet_number = i + 1
        
        return pallets
    
    def get_pallet_summary(self, pallet: PalletConfiguration) -> Dict:
        """
        Get complete summary of a pallet configuration
        
        Includes dimensions, weight, freight class, stability
        """
        dims = pallet.dimensions()
        
        # Calculate freight class with 75" rule
        freight_info = FreightCalculator.calculate_freight_class_with_75_rule(
            weight_lbs=pallet.total_weight(),
            length_inches=dims[0],
            width_inches=dims[1],
            actual_height_inches=dims[2]
        )
        
        # Analyze stability
        stability = StabilityAnalyzer.analyze(pallet)
        
        return {
            'pallet_number': pallet.pallet_number,
            'dimensions': {
                'length': dims[0],
                'width': dims[1],
                'height': dims[2]
            },
            'weight': {
                'product': pallet.product_weight(),
                'pallet': pallet.pallet_weight,
                'total': pallet.total_weight()
            },
            'box_count': pallet.box_count(),
            'freight': freight_info,
            'stability': {
                'grade': stability.grade.value,
                'cog_percentage': stability.cog_percentage,
                'bottom_weight_pct': stability.weight_in_bottom_half,
                'safe_to_ship': stability.is_safe_to_ship(),
                'warnings': stability.warnings
            }
        }
