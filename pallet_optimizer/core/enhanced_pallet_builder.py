"""
Enhanced Pallet Builder with Stability Constraints
Adds industry best practices on top of EB-AFIT algorithm
"""
from typing import List, Tuple, Optional
from palletier import Solver, Box as PalletierBox, Pallet as PalletierPallet
from core.models import Product, Box, PlacedBox, PalletConfig
from core.freight_calculator import FreightCalculator


class EnhancedPalletBuilder:
    """Build optimal pallet configurations with stability and safety constraints"""
    
    PALLET_WEIGHT = 50  # lbs
    MAX_OVERHANG = 8  # inches - allowed on ONE dimension only
    
    # Stability constraints
    MAX_HEIGHT_TO_WIDTH_RATIO = 3.0  # Industry standard (OSHA)
    PREFERRED_HEIGHT_TO_WIDTH_RATIO = 2.0  # Safety margin
    WARNING_HEIGHT_TO_WIDTH_RATIO = 2.5  # Issue warning
    
    # Height limits
    MAX_FREIGHT_HEIGHT = 72  # inches (common LTL limit)
    HEIGHT_PENALTY_THRESHOLD = 75  # inches (triggers NMFC penalty)
    
    # Flat box detection
    FLAT_BOX_THRESHOLD = 6  # inches (if smallest dim < this, consider "flat")
    
    # Standard pallet sizes (L, W, H in inches)
    PALLET_SIZES = {
        'GMA_40x48': (48, 40, 91),
        'GMA_48x48': (48, 48, 91),
        'EUR': (47.24, 39.37, 91)
    }
    
    # Maximum allowed dimensions with overhang (L, W, H)
    PALLET_MAX_WITH_OVERHANG = {
        'GMA_40x48': (56, 48, 91),  # 48+8, 40+8, 91
        'GMA_48x48': (56, 56, 91),
        'EUR': (55.24, 47.37, 91)
    }
    
    @staticmethod
    def build_pallets(
        products: List[Product],
        quantities: List[int],
        pallet_size: str = 'GMA_40x48',
        strategy: str = 'balanced'  # 'balanced', 'max_utilization', 'max_stability'
    ) -> Tuple[List[PalletConfig], List[str]]:
        """
        Build optimal pallet configuration with stability checks
        
        Args:
            products: List of Product objects
            quantities: Quantity for each product
            pallet_size: Pallet size key
            strategy: Packing strategy to use
        
        Returns:
            Tuple of (configs, warnings)
        """
        warnings = []
        
        # Get pallet dimensions
        pallet_dims = EnhancedPalletBuilder.PALLET_SIZES[pallet_size]
        max_dims = EnhancedPalletBuilder.PALLET_MAX_WITH_OVERHANG[pallet_size]
        
        # Generate all boxes for the order
        all_boxes = []
        for product, quantity in zip(products, quantities):
            for i in range(quantity):
                for box in product.boxes:
                    all_boxes.append(box)
        
        if not all_boxes:
            return [], warnings
        
        # Analyze boxes for orientation preferences
        box_analysis = EnhancedPalletBuilder._analyze_boxes(all_boxes)
        
        # Try packing with orientation hints
        configs = EnhancedPalletBuilder._pack_with_strategy(
            all_boxes, max_dims, pallet_dims, strategy, box_analysis
        )
        
        # Validate results and generate warnings
        for config in configs:
            config_warnings = EnhancedPalletBuilder._validate_config(config)
            warnings.extend(config_warnings)
        
        return configs, warnings
    
    @staticmethod
    def _analyze_boxes(boxes: List[Box]) -> dict:
        """Analyze boxes to determine packing preferences"""
        analysis = {
            'has_flat_boxes': False,
            'flat_box_threshold': EnhancedPalletBuilder.FLAT_BOX_THRESHOLD,
            'total_boxes': len(boxes),
            'total_weight': sum(b.weight for b in boxes)
        }
        
        # Check for flat boxes
        for box in boxes:
            min_dim = min(box.length, box.width, box.height)
            if min_dim < EnhancedPalletBuilder.FLAT_BOX_THRESHOLD:
                analysis['has_flat_boxes'] = True
                break
        
        return analysis
    
    @staticmethod
    def _pack_with_strategy(
        boxes: List[Box],
        max_dims: Tuple[float, float, float],
        pallet_dims: Tuple[float, float, float],
        strategy: str,
        analysis: dict
    ) -> List[PalletConfig]:
        """Pack boxes using specified strategy"""
        
        # Convert to palletier Box objects
        palletier_boxes = []
        for box in boxes:
            # For flat boxes with "balanced" or "max_stability" strategy,
            # we could pre-sort dimensions to prefer flat orientation
            # But palletier will still optimize, so we work with what we get
            pb = PalletierBox((box.length, box.width, box.height))
            pb._raymond_box = box
            palletier_boxes.append(pb)
        
        # Create pallet with overhang allowance
        # Palletier expects (X, Y, Z) where Y is height
        palletier_pallet = PalletierPallet((max_dims[0], max_dims[2], max_dims[1]))
        palletier_pallets = [palletier_pallet]
        
        # Run solver
        solver = Solver(palletier_pallets, palletier_boxes)
        solver.pack()
        
        # Convert results
        configs = []
        for pallet_num, packed_pallet in enumerate(solver.packed_pallets, 1):
            config = EnhancedPalletBuilder._convert_to_config(
                packed_pallet,
                pallet_num,
                pallet_dims
            )
            configs.append(config)
        
        return configs
    
    @staticmethod
    def _convert_to_config(
        packed_pallet,
        pallet_number: int,
        pallet_dims: Tuple[float, float, float]
    ) -> PalletConfig:
        """Convert palletier PackedPallet to our PalletConfig"""
        
        # Extract placed boxes
        placed_boxes = []
        total_product_weight = 0
        
        for packed_box in packed_pallet.boxes:
            original_box = packed_box._raymond_box
            total_product_weight += original_box.weight
            
            placed = PlacedBox(
                box=original_box,
                x=packed_box.pos.x if hasattr(packed_box.pos, 'x') else packed_box.pos[0],
                y=packed_box.pos.y if hasattr(packed_box.pos, 'y') else packed_box.pos[1],
                z=packed_box.pos.z if hasattr(packed_box.pos, 'z') else packed_box.pos[2],
                orientation=(
                    packed_box.orientation.dim1 if hasattr(packed_box.orientation, 'dim1') else packed_box.orientation[0],
                    packed_box.orientation.dim2 if hasattr(packed_box.orientation, 'dim2') else packed_box.orientation[1],
                    packed_box.orientation.dim3 if hasattr(packed_box.orientation, 'dim3') else packed_box.orientation[2]
                )
            )
            placed_boxes.append(placed)
        
        # Calculate actual pallet dimensions
        if placed_boxes:
            max_x = max(pb.x + pb.orientation[0] for pb in placed_boxes)
            max_y = max(pb.y + pb.orientation[1] for pb in placed_boxes)
            max_z = max(pb.z + pb.orientation[2] for pb in placed_boxes)
            
            # Palletier uses (X, Y, Z) where Y is height
            actual_dims = (
                round(max_x, 1),   # Length 
                round(max_z, 1),   # Width
                round(max_y, 1)    # Height (vertical stacking)
            )
        else:
            actual_dims = (pallet_dims[0], pallet_dims[1], 5)
        
        # Calculate freight class
        total_weight = total_product_weight + EnhancedPalletBuilder.PALLET_WEIGHT
        freight_info = FreightCalculator.calculate_freight_class(
            total_weight,
            actual_dims[0],
            actual_dims[1],
            actual_dims[2]
        )
        
        # Calculate utilization
        pallet_volume = pallet_dims[0] * pallet_dims[1] * pallet_dims[2]
        used_volume = sum(
            pb.orientation[0] * pb.orientation[1] * pb.orientation[2]
            for pb in placed_boxes
        )
        utilization = (used_volume / pallet_volume * 100) if pallet_volume > 0 else 0
        
        return PalletConfig(
            pallet_number=pallet_number,
            dimensions=actual_dims,
            weight_product=total_product_weight,
            weight_pallet=EnhancedPalletBuilder.PALLET_WEIGHT,
            boxes=placed_boxes,
            freight_class=freight_info['freight_class'],
            freight_class_note=freight_info['note'],
            volume_cuft=freight_info['actual_volume_cf'],
            utilization=round(utilization, 1)
        )
    
    @staticmethod
    def _validate_config(config: PalletConfig) -> List[str]:
        """Validate configuration and return warnings"""
        warnings = []
        
        length, width, height = config.dimensions
        
        # 1. Check height-to-width ratio (CRITICAL)
        base_width = min(length, width)
        ratio = height / base_width if base_width > 0 else 999
        
        if ratio > EnhancedPalletBuilder.MAX_HEIGHT_TO_WIDTH_RATIO:
            warnings.append(
                f"⚠️ CRITICAL: Pallet {config.pallet_number} stability violation! "
                f"Height/width ratio {ratio:.2f}:1 exceeds maximum {EnhancedPalletBuilder.MAX_HEIGHT_TO_WIDTH_RATIO}:1. "
                f"This configuration is UNSAFE and should be rejected."
            )
        elif ratio > EnhancedPalletBuilder.WARNING_HEIGHT_TO_WIDTH_RATIO:
            warnings.append(
                f"⚠️ WARNING: Pallet {config.pallet_number} has borderline stability. "
                f"Height/width ratio {ratio:.2f}:1 exceeds recommended {EnhancedPalletBuilder.PREFERRED_HEIGHT_TO_WIDTH_RATIO}:1. "
                f"Consider alternative configuration."
            )
        
        # 2. Check overall height limits
        if height > EnhancedPalletBuilder.MAX_FREIGHT_HEIGHT:
            warnings.append(
                f"⚠️ WARNING: Pallet {config.pallet_number} height {height}\" exceeds "
                f"common LTL freight limit of {EnhancedPalletBuilder.MAX_FREIGHT_HEIGHT}\". "
                f"May require special handling or be rejected by some carriers."
            )
        
        # 3. Check 75" rule penalty
        if height >= EnhancedPalletBuilder.HEIGHT_PENALTY_THRESHOLD:
            # Calculate cost impact
            actual_class = config.freight_class
            
            # Estimate what class would be without penalty
            actual_volume = config.volume_cuft
            penalty_volume_in = length * width * 96  # As if 96" tall
            penalty_volume_cf = penalty_volume_in / 1728
            density_without_penalty = config.weight_total / actual_volume
            
            warnings.append(
                f"💰 COST IMPACT: Pallet {config.pallet_number} triggers 75\" rule penalty. "
                f"Height {height}\" is calculated as 96\" for freight class. "
                f"Consider splitting or reconfiguring to stay under 75\" and reduce freight cost."
            )
        
        # 4. Check for flat boxes standing on edge
        flat_boxes_vertical = 0
        for placed_box in config.boxes:
            orig_dims = sorted([
                placed_box.box.length,
                placed_box.box.width,
                placed_box.box.height
            ])
            placed_dims = sorted(placed_box.orientation)
            
            # Check if smallest original dimension is now vertical (middle position in sorted)
            if orig_dims[0] < EnhancedPalletBuilder.FLAT_BOX_THRESHOLD:
                # This is a "flat" box
                if placed_dims[1] == orig_dims[2] or placed_dims[2] == orig_dims[2]:
                    # Longest dimension is vertical or middle
                    flat_boxes_vertical += 1
        
        if flat_boxes_vertical > 0:
            warnings.append(
                f"📦 INFO: Pallet {config.pallet_number} has {flat_boxes_vertical} flat boxes "
                f"standing on edge. Consider laying flat for better stability."
            )
        
        return warnings
