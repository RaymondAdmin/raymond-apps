"""
Calculator Module
Handles freight class calculation, dimensional weight, and other shipping calculations
"""

from typing import List
from .product_loader import Box


class FreightCalculator:
    """Calculates freight class based on density"""
    
    # NMFC freight class thresholds (density in lbs/cu ft)
    # Updated for 2025 NMFC 13-tier system
    # Format: (max_density, freight_class)
    FREIGHT_CLASS_TABLE = [
        (1, 500),      # Less than 1 lb/cu ft = Class 500
        (2, 400),      # 1-2 lb/cu ft = Class 400
        (4, 300),      # 2-4 lb/cu ft = Class 300
        (6, 250),      # 4-6 lb/cu ft = Class 250
        (8, 175),      # 6-8 lb/cu ft = Class 175
        (10, 125),     # 8-10 lb/cu ft = Class 125
        (10.5, 100),   # 10-10.5 lb/cu ft = Class 100
        (12, 92.5),    # 10.5-12 lb/cu ft = Class 92.5
        (15, 85),      # 12-15 lb/cu ft = Class 85
        (22.5, 70),    # 15-22.5 lb/cu ft = Class 70
        (30, 65),      # 22.5-30 lb/cu ft = Class 65
        (35, 60),      # 30-35 lb/cu ft = Class 60
        (50, 55),      # 35-50 lb/cu ft = Class 55 (new for 2025)
        (float('inf'), 50)  # 50+ lb/cu ft = Class 50 (new for 2025)
    ]
    
    @staticmethod
    def calculate_density(weight_lbs: float, volume_cubic_inches: float) -> float:
        """Calculate density in lbs per cubic foot"""
        if volume_cubic_inches == 0:
            return 0
        cubic_feet = volume_cubic_inches / 1728  # 1728 cubic inches in a cubic foot
        return weight_lbs / cubic_feet
    
    @staticmethod
    def get_freight_class(density: float) -> int:
        """Determine freight class based on density"""
        if density <= 0:
            return 500  # Invalid/unknown density defaults to highest class
        
        for threshold, freight_class in FreightCalculator.FREIGHT_CLASS_TABLE:
            if density < threshold:
                return freight_class
        return 50  # Highest density
    
    @staticmethod
    def calculate_dimensional_weight(length: float, width: float, height: float, divisor: int = 139) -> float:
        """
        Calculate dimensional weight for small parcel carriers
        Default divisor is 139 (FedEx/UPS standard for domestic)
        """
        return (length * width * height) / divisor


class ShipmentCalculator:
    """Calculates totals for a shipment"""
    
    def __init__(self, boxes: List[Box], pallet_weight: float = 50):
        self.boxes = boxes
        self.pallet_weight = pallet_weight
    
    def total_actual_weight(self) -> float:
        """Total actual weight of all boxes"""
        return sum(box.weight for box in self.boxes)
    
    def total_dimensional_weight(self) -> float:
        """Total dimensional weight of all boxes"""
        return sum(
            FreightCalculator.calculate_dimensional_weight(box.length, box.width, box.height)
            for box in self.boxes
        )
    
    def billable_weight(self) -> float:
        """Returns the higher of actual or dimensional weight"""
        return max(self.total_actual_weight(), self.total_dimensional_weight())
    
    def total_volume(self) -> float:
        """Total volume in cubic inches"""
        return sum(box.volume() for box in self.boxes)
    
    def calculate_pallet_dimensions(self, boxes_on_pallet: List[Box]) -> tuple:
        """
        Calculate the dimensions of a pallet with given boxes
        Returns (length, width, height) in inches
        
        For now, uses a simple heuristic:
        - Width/Length: largest box footprint (assumes boxes stacked vertically)
        - Height: sum of box heights + 5" pallet base
        """
        if not boxes_on_pallet:
            return (0, 0, 0)
        
        max_length = max(box.length for box in boxes_on_pallet)
        max_width = max(box.width for box in boxes_on_pallet)
        total_height = sum(box.height for box in boxes_on_pallet) + 5  # Add pallet height
        
        return (max_length, max_width, total_height)
    
    def calculate_freight_class_for_pallet(self, boxes_on_pallet: List[Box]) -> int:
        """Calculate freight class for a specific pallet"""
        pallet_dims = self.calculate_pallet_dimensions(boxes_on_pallet)
        pallet_volume = pallet_dims[0] * pallet_dims[1] * pallet_dims[2]
        
        total_weight = sum(box.weight for box in boxes_on_pallet) + self.pallet_weight
        density = FreightCalculator.calculate_density(total_weight, pallet_volume)
        
        return FreightCalculator.get_freight_class(density)
