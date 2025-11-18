"""
Stability Analysis for Pallet Configurations
Implements industry-standard stability checks
"""

from typing import List
from models import PalletConfiguration, PlacedBox, StabilityReport, StabilityGrade


class StabilityAnalyzer:
    """
    Analyze pallet stability and safety
    
    Implements checks based on:
    - OSHA guidelines
    - GMA (Grocery Manufacturers Association) standards
    - Industry best practices
    """
    
    # Stability thresholds
    EXCELLENT_COG_THRESHOLD = 45  # % - COG below this = excellent
    GOOD_COG_THRESHOLD = 50       # % - COG below this = good
    ACCEPTABLE_COG_THRESHOLD = 55 # % - COG below this = acceptable
    POOR_COG_THRESHOLD = 60       # % - COG below this = poor (above = dangerous)
    
    EXCELLENT_BOTTOM_WEIGHT = 75  # % - weight in bottom 50% for excellent
    GOOD_BOTTOM_WEIGHT = 65       # % - weight in bottom 50% for good
    ACCEPTABLE_BOTTOM_WEIGHT = 60 # % - weight in bottom 50% for acceptable
    
    @staticmethod
    def analyze(pallet: PalletConfiguration) -> StabilityReport:
        """
        Perform complete stability analysis on a pallet
        
        Args:
            pallet: The pallet configuration to analyze
            
        Returns:
            StabilityReport with all metrics and recommendations
        """
        if not pallet.placed_boxes:
            return StabilityReport(
                center_of_gravity_height=0,
                cog_percentage=0,
                weight_in_bottom_half=100,
                top_heavy=False,
                grade=StabilityGrade.A,
                warnings=[]
            )
        
        # Calculate center of gravity
        cog_height, cog_percentage = StabilityAnalyzer._calculate_cog(pallet)
        
        # Calculate weight distribution
        bottom_weight_pct = StabilityAnalyzer._calculate_weight_distribution(pallet)
        
        # Check for top-heavy condition
        top_heavy = cog_percentage > StabilityAnalyzer.POOR_COG_THRESHOLD
        
        # Generate warnings
        warnings = StabilityAnalyzer._generate_warnings(
            pallet, cog_percentage, bottom_weight_pct, top_heavy
        )
        
        # Assign grade
        grade = StabilityAnalyzer._assign_grade(cog_percentage, bottom_weight_pct)
        
        return StabilityReport(
            center_of_gravity_height=cog_height,
            cog_percentage=cog_percentage,
            weight_in_bottom_half=bottom_weight_pct,
            top_heavy=top_heavy,
            grade=grade,
            warnings=warnings
        )
    
    @staticmethod
    def _calculate_cog(pallet: PalletConfiguration) -> tuple:
        """
        Calculate center of gravity height
        
        Returns: (cog_height_inches, cog_percentage)
        """
        total_weight = pallet.product_weight()
        total_height = pallet.dimensions()[2]
        
        if total_weight == 0:
            return (0, 0)
        
        # Calculate weighted height sum
        weighted_height_sum = 0
        
        for placed_box in pallet.placed_boxes:
            # COG of each box is at its center
            box_cog_z = placed_box.z + (placed_box.box.height / 2)
            weighted_height_sum += placed_box.box.weight * box_cog_z
        
        # Overall COG height
        cog_height = weighted_height_sum / total_weight
        
        # As percentage of total height
        cog_percentage = (cog_height / total_height * 100) if total_height > 0 else 0
        
        return (cog_height, cog_percentage)
    
    @staticmethod
    def _calculate_weight_distribution(pallet: PalletConfiguration) -> float:
        """
        Calculate percentage of weight in bottom 50% of pallet
        
        Returns: Percentage (0-100)
        """
        total_height = pallet.dimensions()[2]
        half_height = total_height / 2
        total_weight = pallet.product_weight()
        
        if total_weight == 0:
            return 100
        
        # Sum weight of boxes whose TOP is in bottom half
        bottom_weight = 0
        
        for placed_box in pallet.placed_boxes:
            box_top = placed_box.z + placed_box.box.height
            
            if box_top <= half_height:
                # Entire box in bottom half
                bottom_weight += placed_box.box.weight
            elif placed_box.z < half_height:
                # Box spans the halfway point - use proportional weight
                box_height = placed_box.box.height
                height_in_bottom = half_height - placed_box.z
                proportion = height_in_bottom / box_height
                bottom_weight += placed_box.box.weight * proportion
        
        return (bottom_weight / total_weight * 100) if total_weight > 0 else 0
    
    @staticmethod
    def _generate_warnings(
        pallet: PalletConfiguration,
        cog_percentage: float,
        bottom_weight_pct: float,
        top_heavy: bool
    ) -> List[str]:
        """Generate warnings based on stability metrics"""
        warnings = []
        
        # Top-heavy warning
        if top_heavy:
            warnings.append(
                f"⚠️ CRITICAL: Center of gravity at {cog_percentage:.1f}% of height "
                f"(above {StabilityAnalyzer.POOR_COG_THRESHOLD}%) - HIGH RISK OF TIPPING"
            )
        elif cog_percentage > StabilityAnalyzer.ACCEPTABLE_COG_THRESHOLD:
            warnings.append(
                f"Center of gravity at {cog_percentage:.1f}% is higher than recommended "
                f"({StabilityAnalyzer.ACCEPTABLE_COG_THRESHOLD}%)"
            )
        
        # Weight distribution warning
        if bottom_weight_pct < StabilityAnalyzer.ACCEPTABLE_BOTTOM_WEIGHT:
            warnings.append(
                f"Only {bottom_weight_pct:.1f}% of weight in bottom half "
                f"(recommended: {StabilityAnalyzer.ACCEPTABLE_BOTTOM_WEIGHT}%+)"
            )
        
        # Check for very tall pallets
        dims = pallet.dimensions()
        if dims[2] > 84:  # 7 feet
            warnings.append(
                f"Pallet height {dims[2]:.0f}\" exceeds 84\" - "
                f"consider splitting across more pallets"
            )
        
        # Check total weight
        if pallet.total_weight() > 2500:
            warnings.append(
                f"Total weight {pallet.total_weight():.0f} lbs exceeds "
                f"typical pallet capacity (2500 lbs) - verify pallet rating"
            )
        
        return warnings
    
    @staticmethod
    def _assign_grade(cog_percentage: float, bottom_weight_pct: float) -> StabilityGrade:
        """
        Assign overall stability grade
        
        Uses most conservative assessment (worst of COG and weight dist)
        """
        # Grade based on COG
        if cog_percentage > StabilityAnalyzer.POOR_COG_THRESHOLD:
            cog_grade = StabilityGrade.F
        elif cog_percentage > StabilityAnalyzer.ACCEPTABLE_COG_THRESHOLD:
            cog_grade = StabilityGrade.D
        elif cog_percentage > StabilityAnalyzer.GOOD_COG_THRESHOLD:
            cog_grade = StabilityGrade.C
        elif cog_percentage > StabilityAnalyzer.EXCELLENT_COG_THRESHOLD:
            cog_grade = StabilityGrade.B
        else:
            cog_grade = StabilityGrade.A
        
        # Grade based on weight distribution
        if bottom_weight_pct < StabilityAnalyzer.ACCEPTABLE_BOTTOM_WEIGHT:
            weight_grade = StabilityGrade.D
        elif bottom_weight_pct < StabilityAnalyzer.GOOD_BOTTOM_WEIGHT:
            weight_grade = StabilityGrade.C
        elif bottom_weight_pct < StabilityAnalyzer.EXCELLENT_BOTTOM_WEIGHT:
            weight_grade = StabilityGrade.B
        else:
            weight_grade = StabilityGrade.A
        
        # Return worst grade (most conservative)
        grades_ordered = [StabilityGrade.A, StabilityGrade.B, StabilityGrade.C, 
                         StabilityGrade.D, StabilityGrade.F]
        
        cog_index = grades_ordered.index(cog_grade)
        weight_index = grades_ordered.index(weight_grade)
        
        worst_index = max(cog_index, weight_index)
        return grades_ordered[worst_index]
    
    @staticmethod
    def suggest_improvements(report: StabilityReport, pallet: PalletConfiguration) -> List[str]:
        """
        Suggest improvements for unstable pallets
        
        Args:
            report: The stability report
            pallet: The pallet configuration
            
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        if report.grade in [StabilityGrade.D, StabilityGrade.F]:
            suggestions.append("🔴 IMMEDIATE ACTION REQUIRED")
        
        if report.top_heavy:
            suggestions.append(
                "• Reorganize: Place heaviest boxes at bottom layers"
            )
            suggestions.append(
                "• Consider: Split load across more pallets to reduce height"
            )
        
        if report.weight_in_bottom_half < StabilityAnalyzer.ACCEPTABLE_BOTTOM_WEIGHT:
            suggestions.append(
                "• Restack: Move heavier boxes to bottom 50% of pallet"
            )
        
        dims = pallet.dimensions()
        if dims[2] > 84:
            suggestions.append(
                f"• Height: Reduce from {dims[2]:.0f}\" to under 84\" for better stability"
            )
        
        if not suggestions:
            suggestions.append("✅ Pallet stability is acceptable - no changes needed")
        
        return suggestions
