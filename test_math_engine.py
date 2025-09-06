#!/usr/bin/env python3
"""
Math Engine Test Script
=======================

This script tests the mathematical expression evaluation engine
to ensure it's working correctly with various types of inputs.
"""

import sys
import os

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.math_engine import compare_mathematical_expressions, normalize_expression_for_storage

def test_basic_equivalence():
    """Test basic mathematical equivalence."""
    print("=== Testing Basic Equivalence ===")
    
    test_cases = [
        ("2*x + 3", "3 + 2*x", True),
        ("x^2 + 2*x + 1", "(x + 1)^2", True),
        ("a + b", "b + a", True),
        ("2x", "2*x", True),
        ("x + 1", "x + 2", False),
    ]
    
    for expr1, expr2, expected in test_cases:
        result = compare_mathematical_expressions(expr1, expr2)
        status = "✓" if result == expected else "✗"
        print(f"{status} {expr1} == {expr2}: {result} (expected: {expected})")
    print()

def test_latex_handling():
    """Test LaTeX expression handling."""
    print("=== Testing LaTeX Handling ===")
    
    test_cases = [
        (r"c\left(a+b\right)", "c*(a+b)", True),
        (r"\frac{a}{b}", "a/b", True),
        (r"x^{2}", "x^2", True),
        (r"2x + \frac{3}{4}y^{2}", "2*x + (3/4)*y^2", True),
    ]
    
    for latex_expr, standard_expr, expected in test_cases:
        result = compare_mathematical_expressions(latex_expr, standard_expr)
        status = "✓" if result == expected else "✗"
        print(f"{status} {latex_expr} == {standard_expr}: {result} (expected: {expected})")
    print()

def test_normalization():
    """Test expression normalization for storage."""
    print("=== Testing Expression Normalization ===")
    
    expressions = [
        "2*x + 3",
        r"c\left(a+b\right)",
        "x^2 + 2*x + 1",
        r"\frac{a+b}{c}",
    ]
    
    for expr in expressions:
        normalized = normalize_expression_for_storage(expr)
        print(f"Original: {expr}")
        print(f"Normalized: {normalized}")
        print()

def main():
    """Run all tests."""
    print("Mathematics Society - Math Engine Test")
    print("=" * 50)
    print()
    
    try:
        test_basic_equivalence()
        test_latex_handling()
        test_normalization()
        
        print("=" * 50)
        print("All tests completed! Check the results above.")
        
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
