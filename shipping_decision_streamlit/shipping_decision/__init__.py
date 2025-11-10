"""
Raymond Products Shipping Decision System

A proof-of-concept system for determining optimal shipping methods
(Small Parcel vs Freight) and generating pallet configurations.

Modules:
    product_loader: Parse product data from CSV
    calculator: Freight class and dimensional calculations
    decision_engine: Parcel vs Freight decision logic
    pallet_builder: Pallet configuration and distribution
    main: CLI interface for testing
"""

__version__ = "0.1.0"
__author__ = "Raymond Products"

from .product_loader import ProductCatalog, Product, Box
from .calculator import FreightCalculator, ShipmentCalculator
from .decision_engine import DecisionEngine, ShippingDecision
from .pallet_builder import PalletBuilder, Pallet, PalletReport

__all__ = [
    'ProductCatalog',
    'Product',
    'Box',
    'FreightCalculator',
    'ShipmentCalculator',
    'DecisionEngine',
    'ShippingDecision',
    'PalletBuilder',
    'Pallet',
    'PalletReport',
]
