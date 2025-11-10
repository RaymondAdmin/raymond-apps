"""
Product Loader Module
Parses Raymond Products packaging CSV and provides product data lookup
"""

import csv
from typing import Dict, List, Optional


class Box:
    """Represents a single box/package"""
    def __init__(self, sequence: int, length: float, width: float, height: float, weight: float):
        self.sequence = sequence
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        
    def __repr__(self):
        return f"Box(seq={self.sequence}, {self.length}×{self.width}×{self.height}, {self.weight} lbs)"
    
    def volume(self) -> float:
        """Calculate volume in cubic inches"""
        return self.length * self.width * self.height
    
    def max_dimension(self) -> float:
        """Return the largest dimension"""
        return max(self.length, self.width, self.height)


class Product:
    """Represents a product with all its boxes"""
    def __init__(self, sku: str, description: str):
        self.sku = sku
        self.description = description
        self.boxes: List[Box] = []
        
    def add_box(self, box: Box):
        """Add a box to this product"""
        self.boxes.append(box)
        # Keep boxes sorted by sequence
        self.boxes.sort(key=lambda b: b.sequence)
    
    def total_weight(self) -> float:
        """Total weight of all boxes for one unit"""
        return sum(box.weight for box in self.boxes)
    
    def total_volume(self) -> float:
        """Total volume of all boxes for one unit (cubic inches)"""
        return sum(box.volume() for box in self.boxes)
    
    def box_count(self) -> int:
        """Number of boxes per unit"""
        return len(self.boxes)
    
    def has_oversized_box(self) -> bool:
        """Check if any box has a dimension > 67 inches"""
        return any(box.max_dimension() > 67 for box in self.boxes)
    
    def __repr__(self):
        return f"Product({self.sku}, {self.box_count()} boxes, {self.total_weight()} lbs)"


class ProductCatalog:
    """Catalog of all products"""
    def __init__(self):
        self.products: Dict[str, Product] = {}
    
    def add_product(self, product: Product):
        """Add a product to the catalog"""
        self.products[product.sku] = product
    
    def get_product(self, sku: str) -> Optional[Product]:
        """Get a product by SKU"""
        return self.products.get(sku)
    
    def load_from_csv(self, csv_path: str):
        """Load products from Raymond Products CSV format"""
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                sku = row['default_code'].strip()
                description = row['description'].strip()
                sequence = int(row['Sequence'])
                length = float(row['Length 1'])
                width = float(row['Width 1'])
                height = float(row['Height 1'])
                weight = float(row['Weight 1'])
                
                # Get or create product
                if sku not in self.products:
                    self.products[sku] = Product(sku, description)
                
                # Add box to product
                box = Box(sequence, length, width, height, weight)
                self.products[sku].add_box(box)
        
        return self
    
    def __len__(self):
        return len(self.products)
    
    def __repr__(self):
        return f"ProductCatalog({len(self)} products)"
