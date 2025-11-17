"""
Enhanced Data Models for Pallet Optimization
Includes position tracking, rotation support, and metadata
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class Rotation(Enum):
    """Box rotation options"""
    NONE = 0      # Original orientation (L×W×H)
    ROTATE_90 = 90   # Rotated 90° (W×L×H)


@dataclass
class Box:
    """
    Represents a single box/package
    
    Attributes:
        length: Length in inches (longest dimension horizontally)
        width: Width in inches (shorter dimension horizontally)
        height: Height in inches (vertical dimension)
        weight: Weight in pounds
        sequence: Box sequence number for multi-box products (1, 2, 3...)
        product_sku: Product SKU this box belongs to
    """
    length: float
    width: float
    height: float
    weight: float
    sequence: int = 1
    product_sku: str = ""
    
    def volume(self) -> float:
        """Calculate volume in cubic inches"""
        return self.length * self.width * self.height
    
    def footprint(self) -> float:
        """Calculate base area (length × width)"""
        return self.length * self.width
    
    def rotated_dimensions(self, rotation: Rotation) -> tuple:
        """
        Get dimensions after rotation
        Returns: (length, width, height) after rotation
        """
        if rotation == Rotation.ROTATE_90:
            return (self.width, self.length, self.height)
        return (self.length, self.width, self.height)
    
    def __repr__(self):
        return f"Box({self.length:.1f}×{self.width:.1f}×{self.height:.1f}\", {self.weight:.1f}lbs)"


@dataclass
class PlacedBox:
    """
    Represents a box with its position on a pallet
    
    Attributes:
        box: The Box object
        x, y, z: Position coordinates (bottom-back-left corner)
        rotation: Rotation applied to the box
        layer: Layer number this box belongs to (0-indexed)
    """
    box: Box
    x: float
    y: float
    z: float
    rotation: Rotation = Rotation.NONE
    layer: int = 0
    
    def get_bounds(self) -> tuple:
        """
        Get the 3D bounding box of this placed box
        Returns: (x_min, x_max, y_min, y_max, z_min, z_max)
        """
        dims = self.box.rotated_dimensions(self.rotation)
        return (
            self.x, self.x + dims[0],  # x range
            self.y, self.y + dims[1],  # y range
            self.z, self.z + dims[2]   # z range
        )
    
    def overlaps(self, other: 'PlacedBox') -> bool:
        """Check if this box overlaps with another placed box"""
        b1 = self.get_bounds()
        b2 = other.get_bounds()
        
        # Check if there's NO overlap (easier logic)
        no_overlap = (
            b1[1] <= b2[0] or b2[1] <= b1[0] or  # Separated in X
            b1[3] <= b2[2] or b2[3] <= b1[2] or  # Separated in Y
            b1[5] <= b2[4] or b2[5] <= b1[4]     # Separated in Z
        )
        
        return not no_overlap
    
    def __repr__(self):
        dims = self.box.rotated_dimensions(self.rotation)
        return f"PlacedBox({dims[0]:.1f}×{dims[1]:.1f}×{dims[2]:.1f}\" @ ({self.x:.1f},{self.y:.1f},{self.z:.1f}))"


@dataclass
class Product:
    """
    Represents a product with one or more boxes
    
    Attributes:
        sku: Product SKU
        description: Product description
        boxes: List of Box objects that make up one unit
    """
    sku: str
    description: str
    boxes: List[Box]
    
    def box_count(self) -> int:
        """Number of boxes per unit"""
        return len(self.boxes)
    
    def total_weight(self) -> float:
        """Total weight of one unit (all boxes combined)"""
        return sum(box.weight for box in self.boxes)
    
    def total_volume(self) -> float:
        """Total volume of one unit (all boxes combined)"""
        return sum(box.volume() for box in self.boxes)
    
    def max_height(self) -> float:
        """Tallest box in the product"""
        return max(box.height for box in self.boxes) if self.boxes else 0
    
    def __repr__(self):
        return f"Product({self.sku}, {self.box_count()} boxes, {self.total_weight():.1f}lbs)"


class StabilityGrade(Enum):
    """Stability rating for a pallet"""
    A = "A - Excellent"      # Very stable, ship with confidence
    B = "B - Good"           # Stable, normal shipping
    C = "C - Acceptable"     # Adequate, monitor
    D = "D - Poor"           # Unstable, needs attention
    F = "F - Dangerous"      # Do not ship


@dataclass
class StabilityReport:
    """
    Stability analysis for a pallet
    
    Contains all metrics needed to assess if a pallet is safe to ship
    """
    center_of_gravity_height: float  # Inches from pallet base
    cog_percentage: float            # % of total height
    weight_in_bottom_half: float     # % of weight in bottom 50% of height
    top_heavy: bool                  # COG above 60% of height
    grade: StabilityGrade
    warnings: List[str]
    
    def is_safe_to_ship(self) -> bool:
        """Returns True if pallet is safe to ship"""
        return self.grade in [StabilityGrade.A, StabilityGrade.B, StabilityGrade.C]
    
    def summary(self) -> str:
        """Human-readable summary"""
        lines = [
            f"Stability Grade: {self.grade.value}",
            f"Center of Gravity: {self.cog_percentage:.1f}% of height",
            f"Bottom Weight: {self.weight_in_bottom_half:.1f}%"
        ]
        if self.warnings:
            lines.append("⚠️  Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        return "\n".join(lines)


@dataclass
class PalletConfiguration:
    """
    Complete configuration for a single pallet
    
    Contains all placed boxes and calculated properties
    """
    pallet_number: int
    placed_boxes: List[PlacedBox]
    pallet_base_length: float  # inches
    pallet_base_width: float   # inches
    pallet_height: float = 5.0  # Standard pallet height
    pallet_weight: float = 50.0  # Standard pallet weight in lbs
    
    def box_count(self) -> int:
        """Number of boxes on this pallet"""
        return len(self.placed_boxes)
    
    def product_weight(self) -> float:
        """Weight of products only (excluding pallet)"""
        return sum(pb.box.weight for pb in self.placed_boxes)
    
    def total_weight(self) -> float:
        """Total weight including pallet"""
        return self.product_weight() + self.pallet_weight
    
    def dimensions(self) -> tuple:
        """
        Calculate actual pallet dimensions (L, W, H)
        Returns: (length, width, total_height) in inches
        """
        if not self.placed_boxes:
            return (self.pallet_base_length, self.pallet_base_width, self.pallet_height)
        
        # Find maximum extents
        max_x = max(pb.get_bounds()[1] for pb in self.placed_boxes)
        max_y = max(pb.get_bounds()[3] for pb in self.placed_boxes)
        max_z = max(pb.get_bounds()[5] for pb in self.placed_boxes)
        
        # Apply overhang rules (can overhang on one axis, not both)
        length = max(max_x, self.pallet_base_length)
        width = max(max_y, self.pallet_base_width)
        
        length_overhang = max_x - self.pallet_base_length
        width_overhang = max_y - self.pallet_base_width
        
        # If both overhang, pick the dimension with more overhang
        if length_overhang > 0 and width_overhang > 0:
            if length_overhang > width_overhang:
                width = self.pallet_base_width
            else:
                length = self.pallet_base_length
        
        total_height = max_z
        
        return (length, width, total_height)
    
    def volume(self) -> float:
        """Calculate total volume in cubic inches"""
        dims = self.dimensions()
        return dims[0] * dims[1] * dims[2]
    
    def layers(self) -> Dict[int, List[PlacedBox]]:
        """Group boxes by layer number"""
        layer_map = {}
        for pb in self.placed_boxes:
            if pb.layer not in layer_map:
                layer_map[pb.layer] = []
            layer_map[pb.layer].append(pb)
        return layer_map
    
    def __repr__(self):
        dims = self.dimensions()
        return f"Pallet {self.pallet_number}: {self.box_count()} boxes, {self.total_weight():.0f}lbs, {dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}\""
