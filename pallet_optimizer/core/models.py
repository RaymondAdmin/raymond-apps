"""
Data models for pallet optimization
"""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Box:
    """Represents a single box with dimensions and weight"""
    sequence: int
    length: float
    width: float
    height: float
    weight: float
    product_sku: str = ""
    
    @property
    def dims(self):
        """Return dimensions as tuple for palletier compatibility"""
        return (self.length, self.width, self.height)
    
    @property
    def vol(self):
        """Volume in cubic inches"""
        return self.length * self.width * self.height
    
    def __repr__(self):
        return f"Box({self.product_sku} Seq{self.sequence}: {self.length}×{self.width}×{self.height}\", {self.weight}lbs)"


@dataclass
class Product:
    """Represents a product with one or more boxes"""
    sku: str
    description: str
    boxes: List[Box]
    
    def box_count(self) -> int:
        """Number of boxes per unit"""
        return len(self.boxes)
    
    def total_weight(self) -> float:
        """Total weight per unit"""
        return sum(box.weight for box in self.boxes)
    
    def __repr__(self):
        return f"Product({self.sku}: {self.box_count()} boxes, {self.total_weight()}lbs)"


@dataclass
class PlacedBox:
    """Box with placement coordinates"""
    box: Box
    x: float
    y: float
    z: float
    orientation: Tuple[float, float, float]  # Actual dims in this orientation
    
    def __repr__(self):
        return f"PlacedBox({self.box.product_sku} @ ({self.x},{self.y},{self.z}))"


@dataclass
class PalletConfig:
    """Complete pallet configuration"""
    pallet_number: int
    dimensions: Tuple[float, float, float]  # L, W, H
    weight_product: float
    weight_pallet: float
    boxes: List[PlacedBox]
    freight_class: int
    freight_class_note: str
    volume_cuft: float
    utilization: float
    
    @property
    def weight_total(self) -> float:
        return self.weight_product + self.weight_pallet
    
    def __repr__(self):
        return (f"Pallet {self.pallet_number}: "
                f"{len(self.boxes)} boxes, "
                f"{self.weight_total:.0f}lbs, "
                f"Class {self.freight_class}")
