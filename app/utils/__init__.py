"""
App Utilities Package
====================

This package contains utility modules and helper functions for the Mathematics Society application.

Modules:
--------
- math_engine: Mathematical expression evaluation and comparison utilities
"""

from .math_engine import compare_mathematical_expressions, normalize_expression_for_storage

__all__ = ['compare_mathematical_expressions', 'normalize_expression_for_storage']
