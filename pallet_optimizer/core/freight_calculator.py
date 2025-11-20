"""
NMFC Freight Class Calculator with 75" rule
"""


class FreightCalculator:
    """Calculate freight class based on density with NMFC rules"""
    
    # NMFC Class thresholds (density in lbs/cu ft)
    DENSITY_TO_CLASS = [
        (50, 50),
        (35, 55),
        (30, 60),
        (22.5, 65),
        (15, 70),
        (13.5, 77.5),
        (12, 85),
        (10.5, 92.5),
        (9, 100),
        (8, 110),
        (7, 125),
        (6, 150),
        (5, 175),
        (4, 200),
        (3, 250),
        (2, 300),
        (1, 400),
        (0, 500)
    ]
    
    @staticmethod
    def calculate_freight_class(
        weight_lbs: float,
        length_in: float,
        width_in: float,
        height_in: float
    ) -> dict:
        """
        Calculate freight class with 75" rule
        
        CRITICAL RULE: If pallet height >= 75", calculate density AS IF height were 96"
        This is an NMFC penalty to discourage tall/unstable shipments
        
        Returns:
            dict with:
                - freight_class: int
                - density: float
                - actual_volume_cf: float
                - calculated_volume_cf: float
                - penalty_applied: bool
                - note: str
        """
        actual_height = height_in
        
        # Apply 75" rule
        if actual_height >= 75:
            calc_height = 96
            penalty_applied = True
            note = "75\" rule: Class calculated at 96\" height"
        else:
            calc_height = actual_height
            penalty_applied = False
            note = ""
        
        # Calculate volumes
        actual_volume_in = length_in * width_in * actual_height
        calc_volume_in = length_in * width_in * calc_height
        
        actual_volume_cf = actual_volume_in / 1728
        calc_volume_cf = calc_volume_in / 1728
        
        # Calculate density using calc_volume
        density = weight_lbs / calc_volume_cf if calc_volume_cf > 0 else 0
        
        # Map density to freight class
        freight_class = FreightCalculator._density_to_class(density)
        
        return {
            'freight_class': freight_class,
            'density': density,
            'actual_volume_cf': actual_volume_cf,
            'calculated_volume_cf': calc_volume_cf,
            'penalty_applied': penalty_applied,
            'note': note
        }
    
    @staticmethod
    def _density_to_class(density: float) -> int:
        """Map density to NMFC freight class"""
        for threshold, freight_class in FreightCalculator.DENSITY_TO_CLASS:
            if density >= threshold:
                return int(freight_class)
        return 500  # Lowest class for very light items
