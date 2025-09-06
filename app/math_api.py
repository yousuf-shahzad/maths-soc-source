"""
Math API Routes
===============

API endpoints for mathematical expression testing and validation.
These routes provide a way to test mathematical expression equivalence
and normalization through simple HTTP requests.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils import compare_mathematical_expressions, normalize_expression_for_storage
from functools import wraps


def admin_required(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Create blueprint for math API
math_api = Blueprint('math_api', __name__)


@math_api.route('/api/math/test-equivalence', methods=['POST'])
@login_required
@admin_required
def test_expression_equivalence():
    """
    Test if two mathematical expressions are equivalent.
    
    Expected JSON payload:
    {
        "expr1": "2*x + 3",
        "expr2": "3 + 2*x"
    }
    
    Returns:
    {
        "equivalent": true,
        "expr1_normalized": "2*x + 3",
        "expr2_normalized": "2*x + 3"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'expr1' not in data or 'expr2' not in data:
            return jsonify({
                'error': 'Missing required fields: expr1 and expr2'
            }), 400
        
        expr1 = data['expr1']
        expr2 = data['expr2']
        
        # Test equivalence
        equivalent = compare_mathematical_expressions(expr1, expr2)
        
        # Get normalized forms
        expr1_normalized = normalize_expression_for_storage(expr1)
        expr2_normalized = normalize_expression_for_storage(expr2)
        
        return jsonify({
            'equivalent': equivalent,
            'expr1': expr1,
            'expr2': expr2,
            'expr1_normalized': expr1_normalized,
            'expr2_normalized': expr2_normalized
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in expression equivalence test: {str(e)}")
        return jsonify({
            'error': 'Internal server error during expression comparison'
        }), 500


@math_api.route('/api/math/normalize', methods=['POST'])
@login_required
@admin_required
def normalize_expression():
    """
    Normalize a mathematical expression for storage or comparison.
    
    Expected JSON payload:
    {
        "expression": "2x + 3"
    }
    
    Returns:
    {
        "original": "2x + 3",
        "normalized": "2*x + 3"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'expression' not in data:
            return jsonify({
                'error': 'Missing required field: expression'
            }), 400
        
        expression = data['expression']
        normalized = normalize_expression_for_storage(expression)
        
        return jsonify({
            'original': expression,
            'normalized': normalized
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in expression normalization: {str(e)}")
        return jsonify({
            'error': 'Internal server error during expression normalization'
        }), 500
