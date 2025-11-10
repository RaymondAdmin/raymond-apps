"""
Decision Engine Module
Determines whether a shipment should go Small Parcel or Freight
"""

from typing import List, Tuple
from product_loader import Box, Product
from calculator import ShipmentCalculator


class ShippingDecision:
    """Represents a shipping decision with reasoning"""
    
    SMALL_PARCEL = "SMALL_PARCEL"
    FREIGHT = "FREIGHT"
    BORDERLINE = "BORDERLINE"
    
    def __init__(self, decision: str, reasons: List[str], details: dict = None):
        self.decision = decision
        self.reasons = reasons
        self.details = details or {}
    
    def __repr__(self):
        return f"ShippingDecision({self.decision}, {len(self.reasons)} reasons)"


class DecisionEngine:
    """Decides whether to ship via Small Parcel or Freight"""
    
    # Thresholds
    WEIGHT_THRESHOLD = 150  # lbs
    MAX_PARCEL_DIMENSION = 96  # inches (actually smaller for most carriers, but using conservative)
    MAX_SINGLE_BOX_WEIGHT = 150  # lbs
    MAX_PARCEL_BOX_COUNT = 4  # Beyond this, freight is usually more cost-effective
    BORDERLINE_WEIGHT = 100  # lbs - between this and WEIGHT_THRESHOLD is borderline
    
    @staticmethod
    def evaluate(product: Product, quantity: int) -> ShippingDecision:
        """
        Evaluate whether a shipment should go Small Parcel or Freight
        
        Args:
            product: The product being shipped
            quantity: Number of units
            
        Returns:
            ShippingDecision with recommendation and reasoning
        """
        # Generate all boxes for this shipment
        all_boxes = []
        for _ in range(quantity):
            all_boxes.extend(product.boxes)
        
        calc = ShipmentCalculator(all_boxes)
        
        total_boxes = len(all_boxes)
        total_weight = calc.total_actual_weight()
        total_dim_weight = calc.total_dimensional_weight()
        billable_weight = calc.billable_weight()
        
        reasons = []
        decision = ShippingDecision.SMALL_PARCEL  # Default
        
        # Check for oversized dimensions (any single box)
        for box in all_boxes:
            if box.max_dimension() > DecisionEngine.MAX_PARCEL_DIMENSION:
                reasons.append(f"Oversized box: {box.length}×{box.width}×{box.height} exceeds {DecisionEngine.MAX_PARCEL_DIMENSION}\" max")
                decision = ShippingDecision.FREIGHT
                break
        
        # Check for overweight single box
        if decision != ShippingDecision.FREIGHT:
            for box in all_boxes:
                if box.weight > DecisionEngine.MAX_SINGLE_BOX_WEIGHT:
                    reasons.append(f"Overweight box: {box.weight} lbs exceeds {DecisionEngine.MAX_SINGLE_BOX_WEIGHT} lb max")
                    decision = ShippingDecision.FREIGHT
                    break
        
        # Check total box count
        if decision != ShippingDecision.FREIGHT and total_boxes > DecisionEngine.MAX_PARCEL_BOX_COUNT:
            reasons.append(f"Too many boxes: {total_boxes} boxes exceeds {DecisionEngine.MAX_PARCEL_BOX_COUNT} box threshold")
            decision = ShippingDecision.FREIGHT
        
        # Check total actual weight
        if decision != ShippingDecision.FREIGHT and total_weight > DecisionEngine.WEIGHT_THRESHOLD:
            reasons.append(f"Total weight: {total_weight:.1f} lbs exceeds {DecisionEngine.WEIGHT_THRESHOLD} lb threshold")
            decision = ShippingDecision.FREIGHT
        
        # Check dimensional weight
        if decision != ShippingDecision.FREIGHT and total_dim_weight > DecisionEngine.WEIGHT_THRESHOLD:
            reasons.append(f"Dimensional weight: {total_dim_weight:.1f} lbs exceeds {DecisionEngine.WEIGHT_THRESHOLD} lb threshold")
            decision = ShippingDecision.FREIGHT
        
        # Borderline check
        if decision == ShippingDecision.SMALL_PARCEL and total_weight > DecisionEngine.BORDERLINE_WEIGHT:
            reasons.append(f"Borderline weight: {total_weight:.1f} lbs is between {DecisionEngine.BORDERLINE_WEIGHT}-{DecisionEngine.WEIGHT_THRESHOLD} lbs")
            decision = ShippingDecision.BORDERLINE
        
        # If no red flags, it's small parcel
        if decision == ShippingDecision.SMALL_PARCEL and not reasons:
            reasons.append(f"Under all thresholds: {total_boxes} boxes, {total_weight:.1f} lbs")
        
        details = {
            'total_boxes': total_boxes,
            'total_weight': total_weight,
            'dimensional_weight': total_dim_weight,
            'billable_weight': billable_weight,
            'quantity': quantity,
            'boxes_per_unit': product.box_count()
        }
        
        return ShippingDecision(decision, reasons, details)
