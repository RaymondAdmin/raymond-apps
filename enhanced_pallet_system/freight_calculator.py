"""
Freight Calculations - NMFC Class and Density
Includes 75" height rule and standard freight class table
"""

from typing import Dict


class FreightCalculator:
    """
    Calculate freight class based on NMFC (National Motor Freight Classification) rules
    """
    
    # NMFC Freight Class Table (2025 standards)
    # Maps density (lbs/cu ft) to freight class
    FREIGHT_CLASS_TABLE = [
        (0.0, 500),      # < 1 lbs/cu ft
        (1.0, 400),      # 1-2
        (2.0, 300),      # 2-4
        (4.0, 250),      # 4-6
        (6.0, 175),      # 6-8
        (8.0, 125),      # 8-10
        (10.0, 100),     # 10-12
        (12.0, 92.5),    # 12-15
        (15.0, 85),      # 15-22.5
        (22.5, 70),      # 22.5-30
        (30.0, 65),      # 30-35
        (35.0, 60),      # 35-50
        (50.0, 50),      # 50+
    ]
    
    # NMFC Critical Rules
    HEIGHT_PENALTY_THRESHOLD = 75  # inches - if >= 75", calculate as if 96"
    CALCULATION_HEIGHT = 96        # inches - height to use for penalty calculation
    PHYSICAL_HEIGHT_LIMIT = 96     # inches - absolute maximum (91" product + 5" pallet)
    
    @staticmethod
    def calculate_density(weight_lbs: float, volume_cubic_inches: float) -> float:
        """
        Calculate density in pounds per cubic foot
        
        Args:
            weight_lbs: Total weight in pounds
            volume_cubic_inches: Total volume in cubic inches
            
        Returns:
            Density in lbs/cu ft
        """
        if volume_cubic_inches <= 0:
            return 0.0
        
        # Convert cubic inches to cubic feet (1728 cubic inches = 1 cubic foot)
        volume_cubic_feet = volume_cubic_inches / 1728
        
        return weight_lbs / volume_cubic_feet
    
    @staticmethod
    def get_freight_class(density: float) -> int:
        """
        Get freight class based on density
        
        Uses NMFC standard freight class table
        
        Args:
            density: Density in lbs/cu ft
            
        Returns:
            Freight class number (50-500)
        """
        for threshold, freight_class in FreightCalculator.FREIGHT_CLASS_TABLE:
            if density < threshold or threshold == FreightCalculator.FREIGHT_CLASS_TABLE[-1][0]:
                return int(freight_class)
        
        return 50  # Densest possible
    
    @staticmethod
    def calculate_freight_class_with_75_rule(
        weight_lbs: float,
        length_inches: float,
        width_inches: float,
        actual_height_inches: float
    ) -> Dict:
        """
        Calculate freight class applying the 75" height penalty rule
        
        CRITICAL NMFC RULE:
        - Physical limit: Can pack up to 96" tall (91" product + 5" pallet)
        - Cost calculation: If height >= 75", calculate freight class AS IF 96" tall
        - Purpose: Penalty for tall/unstable shipments
        
        Args:
            weight_lbs: Total pallet weight (including pallet)
            length_inches: Pallet length
            width_inches: Pallet width
            actual_height_inches: Actual pallet height
            
        Returns:
            Dict with:
            - freight_class: The freight class number
            - density: Calculated density
            - actual_volume: Real volume in cubic feet
            - calculated_volume: Volume used for class calculation
            - penalty_applied: Whether 75" rule was applied
            - notes: Explanation if penalty applied
        """
        # Calculate actual volume
        actual_volume_inches = length_inches * width_inches * actual_height_inches
        actual_volume_cf = actual_volume_inches / 1728
        actual_density = weight_lbs / actual_volume_cf if actual_volume_cf > 0 else 0
        
        # Apply 75" rule if applicable
        penalty_applied = actual_height_inches >= FreightCalculator.HEIGHT_PENALTY_THRESHOLD
        
        if penalty_applied:
            # Calculate as if 96" tall (penalty for tall loads)
            calc_volume_inches = length_inches * width_inches * FreightCalculator.CALCULATION_HEIGHT
            calc_volume_cf = calc_volume_inches / 1728
            calc_density = weight_lbs / calc_volume_cf if calc_volume_cf > 0 else 0
            freight_class = FreightCalculator.get_freight_class(calc_density)
            
            notes = (
                f"⚠️ 75\" Rule Applied: Height {actual_height_inches:.0f}\" >= 75\", "
                f"calculated at {FreightCalculator.CALCULATION_HEIGHT}\" for freight class. "
                f"This increases freight class from what it would be at actual height."
            )
        else:
            # Use actual dimensions
            calc_volume_inches = actual_volume_inches
            calc_volume_cf = actual_volume_cf
            calc_density = actual_density
            freight_class = FreightCalculator.get_freight_class(calc_density)
            notes = "Standard calculation - no height penalty"
        
        return {
            'freight_class': freight_class,
            'density': calc_density,
            'actual_density': actual_density,
            'actual_volume_cf': actual_volume_cf,
            'calculated_volume_cf': calc_volume_cf,
            'penalty_applied': penalty_applied,
            'notes': notes
        }
    
    @staticmethod
    def dimensional_weight(length: float, width: float, height: float, divisor: int = 139) -> float:
        """
        Calculate dimensional weight for parcel shipping
        
        Formula: (L × W × H) / divisor
        
        Args:
            length, width, height: Dimensions in inches
            divisor: Carrier-specific divisor (FedEx/UPS domestic = 139, international = 139)
            
        Returns:
            Dimensional weight in pounds
        """
        return (length * width * height) / divisor
    
    @staticmethod
    def explain_freight_class(freight_class: int) -> str:
        """
        Provide human-readable explanation of freight class
        
        Args:
            freight_class: The freight class number
            
        Returns:
            Explanation string
        """
        explanations = {
            500: "Class 500: Very low density (< 1 lb/cu ft) - pillows, ping pong balls",
            400: "Class 400: Low density (1-2 lbs/cu ft) - deer antlers, light packaging",
            300: "Class 300: Low-medium density (2-4 lbs/cu ft) - wood chairs, model boats",
            250: "Class 250: Medium density (4-6 lbs/cu ft) - bamboo furniture, mattresses",
            175: "Class 175: Medium density (6-8 lbs/cu ft) - clothing, couches",
            125: "Class 125: Medium-high density (8-10 lbs/cu ft) - small appliances",
            100: "Class 100: High density (10-12 lbs/cu ft) - boat covers, wine cases",
            92.5: "Class 92.5: High density (12-15 lbs/cu ft) - computers, monitors",
            85: "Class 85: Very high density (15-22.5 lbs/cu ft) - crated machinery",
            70: "Class 70: Very high density (22.5-30 lbs/cu ft) - automobile engines",
            65: "Class 65: Extremely dense (30-35 lbs/cu ft) - bottled beverages",
            60: "Class 60: Extremely dense (35-50 lbs/cu ft) - car parts",
            50: "Class 50: Maximum density (50+ lbs/cu ft) - steel, bricks"
        }
        
        return explanations.get(freight_class, f"Class {freight_class}: See NMFC guidelines")


class ShipmentCalculator:
    """
    High-level shipment calculations and decision logic
    """
    
    # Decision thresholds
    PARCEL_WEIGHT_LIMIT = 150      # lbs - above this, likely freight
    PARCEL_BOX_LIMIT = 4           # boxes - above this, likely freight
    PARCEL_DIM_LIMIT = 96          # inches - max dimension for parcel
    BORDERLINE_LOWER = 100         # lbs - start of borderline zone
    BORDERLINE_UPPER = 150         # lbs - end of borderline zone
    
    @staticmethod
    def should_ship_freight(
        total_weight: float,
        total_boxes: int,
        max_box_dimension: float,
        dimensional_weight: float
    ) -> Dict:
        """
        Determine if shipment should go via freight vs parcel
        
        Args:
            total_weight: Total shipment weight in lbs
            total_boxes: Number of boxes
            max_box_dimension: Largest dimension of any box
            dimensional_weight: Calculated dim weight
            
        Returns:
            Dict with:
            - decision: "FREIGHT", "PARCEL", or "BORDERLINE"
            - reasons: List of reasons for decision
            - confidence: "HIGH", "MEDIUM", "LOW"
        """
        reasons = []
        freight_triggers = 0
        
        # Check weight
        if total_weight > ShipmentCalculator.PARCEL_WEIGHT_LIMIT:
            reasons.append(f"Total weight {total_weight:.0f} lbs exceeds {ShipmentCalculator.PARCEL_WEIGHT_LIMIT} lb limit")
            freight_triggers += 1
        
        # Check box count
        if total_boxes > ShipmentCalculator.PARCEL_BOX_LIMIT:
            reasons.append(f"{total_boxes} boxes exceeds {ShipmentCalculator.PARCEL_BOX_LIMIT} box limit")
            freight_triggers += 1
        
        # Check dimensions
        if max_box_dimension > ShipmentCalculator.PARCEL_DIM_LIMIT:
            reasons.append(f"Box dimension {max_box_dimension:.0f}\" exceeds {ShipmentCalculator.PARCEL_DIM_LIMIT}\" limit")
            freight_triggers += 1
        
        # Check dimensional weight
        if dimensional_weight > ShipmentCalculator.PARCEL_WEIGHT_LIMIT:
            reasons.append(f"Dimensional weight {dimensional_weight:.0f} lbs exceeds limit")
            freight_triggers += 1
        
        # Make decision
        if freight_triggers > 0:
            decision = "FREIGHT"
            confidence = "HIGH" if freight_triggers >= 2 else "MEDIUM"
        elif total_weight >= ShipmentCalculator.BORDERLINE_LOWER:
            decision = "BORDERLINE"
            confidence = "LOW"
            reasons.append(f"Weight in borderline range ({ShipmentCalculator.BORDERLINE_LOWER}-{ShipmentCalculator.BORDERLINE_UPPER} lbs)")
        else:
            decision = "PARCEL"
            confidence = "HIGH"
            reasons.append(f"Total weight {total_weight:.0f} lbs within parcel limits")
            reasons.append(f"{total_boxes} boxes within parcel limits")
        
        return {
            'decision': decision,
            'reasons': reasons,
            'confidence': confidence,
            'freight_triggers': freight_triggers
        }
