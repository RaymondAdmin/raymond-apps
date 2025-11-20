"""
Load products from CSV file
"""
import pandas as pd
from typing import Dict
from core.models import Box, Product


class ProductLoader:
    """Load product catalog from Raymond packaging CSV"""
    
    @staticmethod
    def load_from_csv(csv_path: str) -> Dict[str, Product]:
        """
        Load products from CSV file
        
        Expected columns:
            - default_code (SKU)
            - description
            - Sequence (box number)
            - Length 1 (inches)
            - Width 1 (inches)
            - Height 1 (inches)
            - Weight 1 (lbs)
        
        Returns:
            Dict mapping SKU -> Product
        """
        df = pd.read_csv(csv_path)
        
        products = {}
        
        # Group by SKU
        for sku, group in df.groupby('default_code'):
            # Get product description (same for all rows)
            description = group.iloc[0]['description']
            
            # Create boxes for this product
            boxes = []
            for _, row in group.iterrows():
                box = Box(
                    sequence=int(row['Sequence']),
                    length=float(row['Length 1']),
                    width=float(row['Width 1']),
                    height=float(row['Height 1']),
                    weight=float(row['Weight 1']),
                    product_sku=sku
                )
                boxes.append(box)
            
            # Sort boxes by sequence
            boxes.sort(key=lambda b: b.sequence)
            
            # Create product
            product = Product(
                sku=sku,
                description=description,
                boxes=boxes
            )
            
            products[sku] = product
        
        return products
