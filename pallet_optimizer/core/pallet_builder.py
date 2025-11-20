"""
Pallet Builder using EB-AFIT algorithm from palletier
"""
from typing import List, Tuple
from palletier import Solver, Box as PalletierBox, Pallet as PalletierPallet
from core.models import Product, Box, PlacedBox, PalletConfig
from core.freight_calculator import FreightCalculator


class PalletBuilder:
    """Build optimal pallet configurations using EB-AFIT algorithm"""
    
    PALLET_WEIGHT = 50  # lbs
    MAX_OVERHANG = 8  # inches - allowed on ONE dimension only
    
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
        pallet_size: str = 'GMA_40x48'
    ) -> List[PalletConfig]:
        """
        Build optimal pallet configuration for order
        
        Args:
            products: List of Product objects
            quantities: Quantity for each product
            pallet_size: Pallet size key ('GMA_40x48', 'GMA_48x48', 'EUR')
        
        Returns:
            List of PalletConfig objects
        """
        # Get pallet dimensions
        pallet_dims = PalletBuilder.PALLET_SIZES[pallet_size]
        
        # Generate all boxes for the order
        all_boxes = []
        for product, quantity in zip(products, quantities):
            for i in range(quantity):
                for box in product.boxes:
                    all_boxes.append(box)
        
        if not all_boxes:
            return []
        
        # Convert to palletier Box objects
        palletier_boxes = []
        for box in all_boxes:
            pb = PalletierBox((box.length, box.width, box.height))
            # Store reference to original box
            pb._raymond_box = box
            palletier_boxes.append(pb)
        
        # Create palletier Pallet with dimensions that allow overhang
        # Use the MAX dimensions (with overhang) for the solver
        max_dims = PalletBuilder.PALLET_MAX_WITH_OVERHANG[pallet_size]
        
        # Palletier expects (X, Y, Z) where Y is height
        # Pass (Length, Height, Width)
        palletier_pallets = [PalletierPallet((max_dims[0], max_dims[2], max_dims[1]))]
        
        # Run solver
        solver = Solver(palletier_pallets, palletier_boxes)
        solver.pack()
        
        # Convert results to PalletConfig objects
        configs = []
        for pallet_num, packed_pallet in enumerate(solver.packed_pallets, 1):
            config = PalletBuilder._convert_to_config(
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
        
        # packed_pallet.boxes is the list of packed boxes
        for packed_box in packed_pallet.boxes:
            # Get original box
            original_box = packed_box._raymond_box
            total_product_weight += original_box.weight
            
            # Get placement - packed_box has pos and orientation attributes
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
        
        # Calculate pallet dimensions
        # CRITICAL: Palletier ROTATES the pallet to find best orientation!
        # The packed_pallet.pallet.orientation contains the ACTUAL orientation used
        # This might be (91, 40, 48) instead of the input (48, 40, 91)!
        if placed_boxes:
            max_x = max(pb.x + pb.orientation[0] for pb in placed_boxes)
            max_y = max(pb.y + pb.orientation[1] for pb in placed_boxes)
            max_z = max(pb.z + pb.orientation[2] for pb in placed_boxes)
            
            # Use the maximum extents as the actual dimensions
            # Palletier places boxes in (X, Y, Z) where:
            # - X and Z are the base dimensions
            # - Y is the height (stacking direction)
            actual_dims = (
                round(max_x, 1),   # Length 
                round(max_z, 1),   # Width
                round(max_y, 1)    # Height (vertical stacking)
            )
        else:
            actual_dims = (pallet_dims[0], pallet_dims[1], 5)
        
        # Calculate freight class
        total_weight = total_product_weight + PalletBuilder.PALLET_WEIGHT
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
            weight_pallet=PalletBuilder.PALLET_WEIGHT,
            boxes=placed_boxes,
            freight_class=freight_info['freight_class'],
            freight_class_note=freight_info['note'],
            volume_cuft=freight_info['actual_volume_cf'],
            utilization=round(utilization, 1)
        )
