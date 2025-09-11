"""
Mathematical Expression Evaluation Engine
==========================================

A robust Python-based mathematical expression evaluation engine designed for educational platforms,
specifically built for the Mathematics Society's online assessment system. This engine handles
complex mathematical expression comparison, normalization, and equivalence checking with support
for both standard mathematical notation and LaTeX formatting.

Author: Mathematics Society Development Team
Version: 4.0
"""

from __future__ import annotations

import logging
import math
import random
import re
from typing import Optional, Tuple, Union

import sympy as sp
from sympy import Eq
from sympy.core.relational import Relational
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
from sympy.printing.str import sstr as sympy_str

try:
    # latex2sympy2 is the preferred parser
    from latex2sympy2 import latex2sympy, latex2latex

    LATEX2SYMPY_AVAILABLE = True
except ImportError:
    LATEX2SYMPY_AVAILABLE = False

# Configure logging for the math engine
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

if not LATEX2SYMPY_AVAILABLE:
    logger.warning("latex2sympy2 not available. LaTeX parsing will fall back to SymPy where possible.")


# Utilities
def _is_latex_expression(expr_str: str) -> bool:
    """
    Detect if an input is likely LaTeX. This is a best-effort heuristic.
    """
    if "$" in expr_str or r"\(" in expr_str or r"\[" in expr_str:
        return True
    latex_patterns = [
        r"\\frac\{",  # Fractions
        r"\\sqrt\{",  # Square roots
        r"\\left[\(\[\{]",
        r"\\right[\)\]\}]",
        r"\\[a-zA-Z]+",  # commands like \sin, \cos, \log, \cdot, \times, etc.
        r"\^{",  # superscripts
        r"_{",  # subscripts
    ]
    for pat in latex_patterns:
        if re.search(pat, expr_str):
            return True
    return False


def _ensure_sympy_expr(obj) -> sp.Expr:
    """
    Convert a latex2sympy result into a SymPy Expr if it isn't already.
    latex2sympy2 often returns a SymPy object; if it returns a string, sympify it.
    """
    if isinstance(obj, sp.Expr):
        return obj
    try:
        return sp.sympify(obj)
    except Exception:
        # Last ditch: return a Symbol with the string, but this shouldn't happen normally
        return sp.Symbol(str(obj))


class ExpressionNormalizer:
    """
    A latex2sympy-first mathematical expression normalizer with robust SymPy canonicalization.
    """

    def __init__(self):
        self.transformations = (
            standard_transformations + (implicit_multiplication_application,) + (convert_xor,)
        )
        # Local dictionary for SymPy parse_expr fallback
        self.local_dict = {
            # core math
            "log": sp.log,
            "ln": sp.log,
            "exp": sp.exp,
            "sqrt": sp.sqrt,
            "sin": sp.sin,
            "cos": sp.cos,
            "tan": sp.tan,
            "asin": sp.asin,
            "acos": sp.acos,
            "atan": sp.atan,
            "sinh": sp.sinh,
            "cosh": sp.cosh,
            "tanh": sp.tanh,
            "abs": sp.Abs,
            # constants
            "e": sp.E,
            "pi": sp.pi,
            # calculus
            "Integral": sp.Integral,
            "Derivative": sp.Derivative,
            # piecewise / others
            "Piecewise": sp.Piecewise,
            "Heaviside": sp.Heaviside,
            "floor": sp.floor,
            "ceiling": sp.ceiling,
            "Ceiling": sp.ceiling,
            "Max": sp.Max,
            "Min": sp.Min,
            # boolean/relational
            "Eq": sp.Eq,
            "Ne": sp.Ne,
            "Lt": sp.Lt,
            "Gt": sp.Gt,
            "Le": sp.Le,
            "Ge": sp.Ge,
        }

    # -----------------------
    # Public API (unchanged)
    # -----------------------

    def normalize_expression(self, expression_str: str) -> str:
        """
        Convert expression to canonical form for comparison. Returns a stable string.
        """
        try:
            expr = self._parse_to_sympy(expression_str)
            expr = self._canonicalize(expr)
            return self._to_stable_string(expr)
        except Exception as e:
            logger.warning(f"normalize_expression: failed for '{expression_str}': {e}")
            return self._basic_string_normalization(expression_str)

    def expressions_equivalent(self, expr1: str, expr2: str) -> bool:
        """
        Check if two expressions are mathematically equivalent.
        This handles equations, expressions, and most analytic forms.
        """
        try:
            e1 = self._parse_to_sympy(expr1)
            e2 = self._parse_to_sympy(expr2)

            # If either is a Relational/Eq, convert to difference form for robust handling
            diff = self._difference_form(e1, e2)
            if diff is None:
                # If we couldn't derive a numeric diff, fall back to structural comparison
                return self._structural_equivalence(e1, e2)

            # Try exact/symbolic checks
            if self._is_zero_symbolically(diff):
                return True

            # Numeric probing as a fallback
            return self._numeric_equivalence(diff)
        except Exception as e:
            logger.error(f"expressions_equivalent: comparison failed: {e}")
            # Fall back to basic normalized string compare
            n1 = self._basic_string_normalization(expr1)
            n2 = self._basic_string_normalization(expr2)
            return n1 == n2

    def get_canonical_form(self, expression_str: str) -> str:
        """
        Get the canonical form for storage using a strict SymPy-based normalization.
        """
        try:
            expr = self._parse_to_sympy(expression_str)
            expr = self._canonicalize(expr)
            return self._to_stable_string(expr)
        except Exception as e:
            logger.warning(f"get_canonical_form: failed for '{expression_str}': {e}")
            return self._basic_string_normalization(expression_str)

    # -----------------------
    # Parsing
    # -----------------------

    def _parse_to_sympy(self, expression_str: str) -> sp.Expr | Relational:
        """
        Parse a string into a SymPy expression with latex2sympy as the primary parser.
        Falls back to SymPy's parse_expr for non-LaTeX inputs or when latex2sympy fails.
        Returns either Expr or Relational (Eq/Lt/Le/Gt/Ge).
        """
        s = expression_str.strip()

        # First, try latex2sympy if available
        if LATEX2SYMPY_AVAILABLE:
            try:
                # latex2sympy can handle pure LaTeX and many math forms
                expr = latex2sympy(s)
                expr = _ensure_sympy_expr(expr)
                return expr
            except Exception as e:
                logger.debug(f"_parse_to_sympy: latex2sympy failed: {e}")

        # If it's likely LaTeX but latex2sympy failed, attempt a quick LaTeX cleanup, retry once
        if LATEX2SYMPY_AVAILABLE and _is_latex_expression(s):
            try:
                cleaned = self._minimal_latex_cleanup(s)
                expr = latex2sympy(cleaned)
                expr = _ensure_sympy_expr(expr)
                return expr
            except Exception as e:
                logger.debug(f"_parse_to_sympy: latex2sympy retry failed: {e}")

        # Fallback to SymPy parse_expr for ASCII math
        try:
            # Support equations like "x^2 = 4"
            if "=" in s and "==" not in s:
                left, right = s.split("=", 1)
                left_expr = parse_expr(
                    left,
                    local_dict=self.local_dict,
                    transformations=self.transformations,
                )
                right_expr = parse_expr(
                    right,
                    local_dict=self.local_dict,
                    transformations=self.transformations,
                )
                return sp.Eq(left_expr, right_expr)

            expr = parse_expr(
                s,
                local_dict=self.local_dict,
                transformations=self.transformations,
            )
            return expr
        except Exception as e:
            # Last ditch: sympify
            logger.debug(f"_parse_to_sympy: parse_expr failed: {e}")
            try:
                return sp.sympify(s)
            except Exception:
                raise

    def _minimal_latex_cleanup(self, s: str) -> str:
        """
        Light-weight LaTeX cleanup to help latex2sympy succeed.
        """
        # Remove math mode markers
        s = s.replace(r"\(", "").replace(r"\)", "").replace(r"\[", "").replace(r"\]", "")
        s = s.replace("$$", "").replace("$", "")

        # Normalize \left and \right
        s = s.replace(r"\left", "").replace(r"\right", "")

        # Common aliases
        s = s.replace(r"\ln", r"\log")
        s = s.replace(r"\cdot", "*").replace(r"\times", "*").replace(r"\div", "/")

        # Remove \mathrm{} etc. (keep inner content)
        s = re.sub(r"\\mathrm\{([^}]+)\}", r"\1", s)
        s = re.sub(r"\\operatorname\{([^}]+)\}", r"\1", s)

        return s

    # -----------------------
    # Canonicalization
    # -----------------------

    def _canonicalize(self, expr: Union[sp.Expr, Relational]) -> Union[sp.Expr, Relational]:
        """
        Canonicalize an expression or relational into a stable, simplified form.
        - For relations Eq(a, b), we simplify both sides.
        - For expressions, we apply a robust pipeline of SymPy simplifications.
        """
        if isinstance(expr, Relational):
            # Canonicalize both sides of the relation
            lhs = self._canonicalize_expr(expr.lhs)
            rhs = self._canonicalize_expr(expr.rhs)
            # For storage/printing, keep as Eq if equality else keep relational type
            if isinstance(expr, Eq):
                return sp.Eq(lhs, rhs)
            else:
                return expr.func(lhs, rhs)

        return self._canonicalize_expr(expr)

    def _canonicalize_expr(self, expr: sp.Expr) -> sp.Expr:
        """
        A robust SymPy canonicalization pipeline.
        Order matters: we try to get stable, simplified, and factored/collected forms.
        """
        try:
            e = sp.sympify(expr)

            # Basic algebraic simplifications
            e = sp.simplify(e)

            # Rational function handling: together + cancel
            e = sp.together(e)
            e = sp.cancel(e)

            # Logarithms and exponentials: expand/collect/combine
            try:
                e = sp.expand_log(e, force=True)
                e = sp.logcombine(e, force=True)
            except Exception:
                pass

            # Powers and products
            e = sp.powsimp(e, force=True, deep=True)
            e = sp.powdenest(e, force=True)

            # Expand then factor terms where it yields a more canonical look
            e = sp.expand_mul(e)
            e = sp.factor_terms(e)

            # Final simplify
            e = sp.simplify(e)

            # Sort terms consistently
            if hasattr(e, "as_ordered_terms"):
                e = sp.Add(*sorted(e.as_ordered_terms(), key=lambda t: sympy_str(t, order="lex"))) if e.is_Add else e

            return e
        except Exception:
            return expr

    def _to_stable_string(self, expr: Union[sp.Expr, Relational]) -> str:
        """
        Convert to a stable string representation. We prefer SymPy's string printer with lex order.
        """
        try:
            if isinstance(expr, Relational):
                return f"{sympy_str(self._canonicalize_expr(expr.lhs), order='lex')} {expr.rel_op} {sympy_str(self._canonicalize_expr(expr.rhs), order='lex')}"
            return sympy_str(expr, order="lex")
        except Exception:
            return str(expr)

    # -----------------------
    # Equivalence helpers
    # -----------------------

    def _difference_form(
        self, e1: Union[sp.Expr, Relational], e2: Union[sp.Expr, Relational]
    ) -> Optional[sp.Expr]:
        """
        Return a difference expression whose zero-ness implies equivalence.
        - Expr vs Expr: return e1 - e2
        - Eq vs Eq: return (lhs1 - rhs1) - (lhs2 - rhs2)
        - Eq vs Expr: return (lhs - rhs) - e
        - Relational with != or inequalities: None (not handled as equivalence)
        """
        try:
            if isinstance(e1, Relational) and isinstance(e2, Relational):
                if isinstance(e1, Eq) and isinstance(e2, Eq):
                    return self._canonicalize_expr((e1.lhs - e1.rhs) - (e2.lhs - e2.rhs))
                # For non-equality relations, we won't assert equivalence here
                return None

            if isinstance(e1, Relational) and isinstance(e1, Eq) and isinstance(e2, sp.Expr):
                return self._canonicalize_expr((e1.lhs - e1.rhs) - e2)

            if isinstance(e2, Relational) and isinstance(e2, Eq) and isinstance(e1, sp.Expr):
                return self._canonicalize_expr(e1 - (e2.lhs - e2.rhs))

            if isinstance(e1, sp.Expr) and isinstance(e2, sp.Expr):
                return self._canonicalize_expr(e1 - e2)

            return None
        except Exception:
            return None

    def _is_zero_symbolically(self, expr: sp.Expr) -> bool:
        """
        Determine if an expression simplifies to zero using symbolic means.
        """
        try:
            e = self._canonicalize_expr(expr)
            if e == 0:
                return True

            e = sp.simplify(e)
            if e == 0:
                return True

            e = sp.together(e)
            e = sp.cancel(e)
            e = sp.simplify(e)
            return e == 0
        except Exception:
            return False

    def _numeric_equivalence(self, diff: sp.Expr, trials: int = 8, tol: float = 1e-9) -> bool:
        """
        Numeric probing over random points for robustness when symbolic methods don't settle it.
        Skips points that cause domain errors (division by zero, log of negative in real mode, etc.).
        """
        symbols = sorted(list(diff.free_symbols), key=lambda s: s.name)
        if not symbols:
            # It's a constant non-zero if we got here, just check numerically
            try:
                val = complex(diff.evalf())
                return abs(val) < tol
            except Exception:
                return False

        # Construct sample points
        domain = list(range(-5, 6))
        for _ in range(trials * 3):  # allow retries for domain errors
            subs_map = {}
            for sym in symbols:
                # Avoid zero for denominators if possible
                cand = random.choice(domain)
                # Ensure some variability and avoid repeated zeros
                if cand == 0:
                    cand = random.choice([1, -1, 2, -2, 3, -3])
                subs_map[sym] = cand

            try:
                val = diff.subs(subs_map)
                # If it remains symbolic, try a float evaluation
                val = complex(val.evalf())
                if math.isnan(val.real) or math.isnan(val.imag) or math.isinf(val.real) or math.isinf(val.imag):
                    continue
                if abs(val) > tol:
                    return False
                trials -= 1
                if trials <= 0:
                    return True
            except Exception:
                # Likely a domain error; retry
                continue

        # If we failed to get enough valid samples, be conservative
        return False

    def _structural_equivalence(self, e1: Union[sp.Expr, Relational], e2: Union[sp.Expr, Relational]) -> bool:
        """
        Last-resort check: compare canonicalized stable strings.
        """
        try:
            c1 = self._canonicalize(e1)
            c2 = self._canonicalize(e2)
            return self._to_stable_string(c1) == self._to_stable_string(c2)
        except Exception:
            return False

    # -----------------------
    # Fallbacks
    # -----------------------

    def _basic_string_normalization(self, expr_str: str) -> str:
        """
        Very conservative fallback string normalization.
        """
        s = expr_str.strip()
        # remove math mode if present
        s = s.replace(r"\(", "").replace(r"\)", "").replace(r"\[", "").replace(r"\]", "")
        s = s.replace("$$", "").replace("$", "")
        # normalize white space and to lower for stability
        s = re.sub(r"\s+", "", s).lower()
        # simple caret->** normalization
        s = s.replace("^", "**")
        # protect function names when inserting multiplication
        function_names = [
            "log",
            "ln",
            "exp",
            "sqrt",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "sinh",
            "cosh",
            "tanh",
        ]
        for fn in function_names:
            s = s.replace(f"{fn}(", f"__FN__{fn}__(")
        # 2x -> 2*x
        s = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", s)
        # x(y) -> x*(y), but not for functions which we protected
        s = re.sub(r"([a-zA-Z])\(", r"\1*(", s)
        for fn in function_names:
            s = s.replace(f"__FN__{fn}__(", f"{fn}(")
        return s


# Global instance for use throughout the application
math_normalizer = ExpressionNormalizer()


# -----------------------
# Public module functions
# -----------------------

def compare_mathematical_expressions(user_answer: str, correct_answer: str) -> bool:
    """
    Compare two mathematical expressions for equivalence.
    """
    return math_normalizer.expressions_equivalent(user_answer, correct_answer)


def normalize_expression_for_storage(expression: str) -> str:
    """
    Normalize an expression for consistent database storage.
    """
    return math_normalizer.get_canonical_form(expression)


def latex_to_sympy_string(latex_expr: str) -> str:
    """
    Convert LaTeX expression to SymPy string representation.
    Prefers latex2sympy; falls back to SymPy printers if needed.
    """
    if LATEX2SYMPY_AVAILABLE:
        try:
            expr = latex2sympy(latex_expr)
            expr = _ensure_sympy_expr(expr)
            expr = math_normalizer._canonicalize_expr(expr)
            return sympy_str(expr, order="lex")
        except Exception as e:
            logger.warning(f"LaTeX to SymPy conversion failed for '{latex_expr}': {e}")
            try:
                # If it's not actually LaTeX or latex2sympy failed, try parse_expr
                parsed = math_normalizer._parse_to_sympy(latex_expr)
                parsed = math_normalizer._canonicalize_expr(parsed)
                return sympy_str(parsed, order="lex")
            except Exception:
                return latex_expr
    else:
        logger.warning("latex2sympy2 not available for LaTeX conversion")
        try:
            parsed = math_normalizer._parse_to_sympy(latex_expr)
            parsed = math_normalizer._canonicalize_expr(parsed)
            return sympy_str(parsed, order="lex")
        except Exception:
            return latex_expr


def latex_to_simplified_latex(latex_expr: str) -> str:
    """
    Simplify a LaTeX expression and return simplified LaTeX.
    Uses latex2latex when available; otherwise parse + SymPy simplify + SymPy latex printer.
    """
    if LATEX2SYMPY_AVAILABLE:
        # First try latex2latex for quick wins
        try:
            simplified = latex2latex(latex_expr)
            return simplified
        except Exception as e:
            logger.debug(f"latex2latex simplification failed for '{latex_expr}': {e}")
        # Fallback: parse to SymPy and re-latex
        try:
            expr = latex2sympy(latex_expr)
            expr = _ensure_sympy_expr(expr)
            expr = math_normalizer._canonicalize_expr(expr)
            return sp.latex(expr)
        except Exception as e:
            logger.warning(f"LaTeX simplification failed for '{latex_expr}': {e}")
            return latex_expr
    else:
        logger.warning("latex2sympy2 not available for LaTeX simplification")
        try:
            expr = math_normalizer._parse_to_sympy(latex_expr)
            expr = math_normalizer._canonicalize_expr(expr)
            return sp.latex(expr)
        except Exception:
            return latex_expr