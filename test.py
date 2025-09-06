import sympy as sp
import re
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
from sympy import simplify, expand, factor, symbols, Symbol

class ExpressionNormalizer:
    def __init__(self):
        # Use safe transformations
        self.transformations = (
            standard_transformations +
            (implicit_multiplication_application,) +
            (convert_xor,)
        )
        
        # Pre-define common symbols to avoid auto_symbol issues
        self.common_symbols = {}
        for letter in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.common_symbols[letter] = Symbol(letter)
    
    def normalize_expression(self, expression_str):
        """
        Convert expression to canonical form for comparison
        """
        try:
            # Clean and standardize input (including LaTeX)
            cleaned = self._preprocess_expression(expression_str)
            print(f"Preprocessed: {cleaned}")
            
            # Parse with SymPy using a simpler approach
            expr = self._safe_parse(cleaned)
            print(f"Parsed: {expr}")
            
            # Apply normalization strategies
            normalized = self._apply_normalization_strategies(expr)
            print(f"Normalized: {normalized}")
            
            return str(normalized)
        except Exception as e:
            # Fallback to string comparison if parsing fails
            print(f"Parsing failed: {e}")
            return self._basic_string_normalization(expression_str)
    
    def _preprocess_expression(self, expr_str):
        """Enhanced preprocessing to handle LaTeX and other formats"""
        # Remove whitespace
        expr_str = expr_str.strip()
        
        # Handle LaTeX formatting
        expr_str = self._clean_latex(expr_str)
        
        # Remove remaining spaces
        expr_str = expr_str.replace(' ', '')
        
        # Handle implicit multiplication: 2x -> 2*x, c(a -> c*(a
        expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)  # 2x -> 2*x
        expr_str = re.sub(r'([a-zA-Z])(\()', r'\1*\2', expr_str)   # c( -> c*(
        expr_str = re.sub(r'(\))([a-zA-Z])', r'\1*\2', expr_str)   # )x -> )*x
        expr_str = re.sub(r'(\))(\()', r'\1*\2', expr_str)         # )( -> )*(
        
        # Handle power notation: x^2 -> x**2
        expr_str = expr_str.replace('^', '**')
        
        # Handle common mathematical functions
        expr_str = re.sub(r'log\(', r'log(', expr_str)
        expr_str = re.sub(r'sin\(', r'sin(', expr_str)
        expr_str = re.sub(r'cos\(', r'cos(', expr_str)
        expr_str = re.sub(r'tan\(', r'tan(', expr_str)
        
        return expr_str
    
    def _clean_latex(self, expr_str):
        """Remove LaTeX formatting and convert to standard mathematical notation"""
        # Handle LaTeX parentheses
        expr_str = expr_str.replace(r'\left(', '(')
        expr_str = expr_str.replace(r'\right)', ')')
        expr_str = expr_str.replace(r'\left[', '[')
        expr_str = expr_str.replace(r'\right]', ']')
        expr_str = expr_str.replace(r'\left\{', '{')
        expr_str = expr_str.replace(r'\right\}', '}')
        
        # Handle LaTeX brackets and braces
        expr_str = expr_str.replace(r'\left|', '|')
        expr_str = expr_str.replace(r'\right|', '|')
        
        # Handle LaTeX fractions: \frac{a}{b} -> (a)/(b)
        expr_str = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr_str)
        
        # Handle LaTeX powers: x^{2} -> x^2
        expr_str = re.sub(r'\^{([^}]+)}', r'^(\1)', expr_str)
        
        # Handle LaTeX subscripts (convert to regular notation): x_{1} -> x1
        expr_str = re.sub(r'_\{([^}]+)\}', r'\1', expr_str)
        
        # Handle LaTeX square roots: \sqrt{x} -> sqrt(x)
        expr_str = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', expr_str)
        
        # Handle LaTeX trigonometric functions
        expr_str = expr_str.replace(r'\sin', 'sin')
        expr_str = expr_str.replace(r'\cos', 'cos')
        expr_str = expr_str.replace(r'\tan', 'tan')
        expr_str = expr_str.replace(r'\log', 'log')
        expr_str = expr_str.replace(r'\ln', 'log')  # Natural log
        
        # Handle LaTeX multiplication symbols
        expr_str = expr_str.replace(r'\cdot', '*')
        expr_str = expr_str.replace(r'\times', '*')
        
        # Handle LaTeX division
        expr_str = expr_str.replace(r'\div', '/')
        
        # Remove any remaining backslashes that might cause issues
        expr_str = re.sub(r'\\([a-zA-Z]+)', r'\1', expr_str)
        
        return expr_str
    
    def _safe_parse(self, expr_str):
        """Safely parse expression by pre-defining symbols"""
        try:
            # Method 1: Try with transformations
            return parse_expr(expr_str, transformations=self.transformations)
        except:
            try:
                # Method 2: Try with explicit symbol definition
                # Find all variables in the expression
                variables = re.findall(r'[a-zA-Z]+', expr_str)
                local_dict = {}
                for var in set(variables):
                    if var not in ['sin', 'cos', 'tan', 'log', 'exp', 'sqrt']:  # Skip function names
                        local_dict[var] = Symbol(var)
                
                return parse_expr(expr_str, local_dict=local_dict, transformations=self.transformations)
            except:
                # Method 3: Most basic parsing
                return parse_expr(expr_str)
    
    def _apply_normalization_strategies(self, expr):
        """Apply multiple normalization approaches"""
        try:
            # Strategy 1: Expand and simplify
            expanded = expand(expr)
            simplified = simplify(expanded)
            
            # Strategy 2: Collect terms and sort
            if simplified.free_symbols:
                collected = sp.collect(simplified, simplified.free_symbols, evaluate=True)
                return collected
            
            return simplified
            
        except Exception as e:
            print(f"Normalization strategy failed: {e}")
            return expr
    
    def _basic_string_normalization(self, expr_str):
        """Enhanced fallback string-based normalization"""
        # First clean LaTeX
        cleaned = self._clean_latex(expr_str)
        
        # Remove spaces and convert to lowercase
        normalized = cleaned.lower().replace(' ', '').replace('**', '^')
        
        # Handle implicit multiplication
        normalized = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', normalized)
        normalized = re.sub(r'([a-zA-Z])(\()', r'\1*\2', normalized)
        
        # Simple term reordering for addition/subtraction
        if '+' in normalized and '*' in normalized:
            try:
                # Split by + and - while keeping the operators
                parts = re.split(r'([+-])', normalized)
                
                # Clean empty parts
                parts = [p for p in parts if p.strip()]
                
                # Separate terms and operators
                terms = []
                operators = []
                
                for i, part in enumerate(parts):
                    if part in ['+', '-']:
                        operators.append(part)
                    else:
                        terms.append(part)
                
                # Sort terms (simple alphabetical sort)
                if len(terms) > 1:
                    # Pair terms with their signs
                    term_sign_pairs = []
                    for i, term in enumerate(terms):
                        sign = '+' if i == 0 else operators[i-1] if i <= len(operators) else '+'
                        term_sign_pairs.append((sign, term))
                    
                    # Sort by term (ignoring sign)
                    term_sign_pairs.sort(key=lambda x: x[1])
                    
                    # Reconstruct
                    result = ''
                    for i, (sign, term) in enumerate(term_sign_pairs):
                        if i == 0 and sign == '+':
                            result += term
                        else:
                            result += sign + term
                    
                    return result
                    
            except Exception as e:
                print(f"String normalization failed: {e}")
                pass
        
        return normalized
    
    def expressions_equivalent(self, expr1, expr2):
        """Check if two expressions are mathematically equivalent"""
        try:
            print(f"Comparing: '{expr1}' vs '{expr2}'")
            
            # Method 1: Normalize and compare strings
            norm1 = self.normalize_expression(expr1)
            norm2 = self.normalize_expression(expr2)
            print(f"Normalized forms: '{norm1}' vs '{norm2}'")
            
            if norm1 == norm2:
                print("Direct string match!")
                return True
            
            # Method 2: Symbolic comparison
            try:
                parsed1 = self._safe_parse(self._preprocess_expression(expr1))
                parsed2 = self._safe_parse(self._preprocess_expression(expr2))
                print(f"Parsed expressions: {parsed1} vs {parsed2}")
                
                # Check if difference simplifies to zero
                difference = simplify(parsed1 - parsed2)
                print(f"Difference: {difference}")
                
                is_equivalent = difference == 0
                print(f"Symbolic equivalence: {is_equivalent}")
                
                if is_equivalent:
                    return True
                    
            except Exception as e:
                print(f"Symbolic comparison failed: {e}")
            
            # Method 3: Enhanced string comparison
            basic_norm1 = self._basic_string_normalization(expr1)
            basic_norm2 = self._basic_string_normalization(expr2)
            print(f"Basic normalized: '{basic_norm1}' vs '{basic_norm2}'")
            
            string_match = basic_norm1 == basic_norm2
            print(f"String equivalence: {string_match}")
            
            return string_match
            
        except Exception as e:
            print(f"All equivalence checks failed: {e}")
            return False
    
    def get_canonical_form(self, expression_str):
        """Get the canonical form for database storage"""
        try:
            cleaned = self._preprocess_expression(expression_str)
            expr = self._safe_parse(cleaned)
            
            # Apply consistent ordering and formatting
            expanded = expand(expr)
            simplified = simplify(expanded)
            
            # Convert back to string with consistent formatting
            return str(simplified)
            
        except Exception as e:
            print(f"Canonical form generation failed: {e}")
            return self._basic_string_normalization(expression_str)

# Test the LaTeX handling specifically
if __name__ == "__main__":
    normalizer = ExpressionNormalizer()
    
    print("=== LaTeX Handling Tests ===")
    
    print("Test 1: LaTeX parentheses")
    latex_expr = r"c\left(a+b\right)"
    normal_expr = "c(a+b)"
    print(f"LaTeX: {latex_expr}")
    print(f"Normal: {normal_expr}")
    print("Result:", normalizer.expressions_equivalent(latex_expr, normal_expr))
    print()
    
    print("Test 2: LaTeX fractions")
    latex_frac = r"\frac{a}{b}"
    normal_frac = "a/b"
    print(f"LaTeX: {latex_frac}")
    print(f"Normal: {normal_frac}")
    print("Result:", normalizer.expressions_equivalent(latex_frac, normal_frac))
    print()
    
    print("Test 3: LaTeX powers")
    latex_power = r"x^{2}"
    normal_power = "x^2"
    print(f"LaTeX: {latex_power}")
    print(f"Normal: {normal_power}")
    print("Result:", normalizer.expressions_equivalent(latex_power, normal_power))
    print()
    
    print("Test 4: Complex LaTeX expression")
    latex_complex = r"2x + \frac{3}{4}y^{2}"
    normal_complex = "2*x + (3/4)*y^2"
    print(f"LaTeX: {latex_complex}")
    print(f"Normal: {normal_complex}")
    print("Result:", normalizer.expressions_equivalent(latex_complex, normal_complex))
    print()
    
    print("=== Original Tests ===")
    
    print("Test 5: Simple polynomial equivalence")
    expr_a = "2*x + 3"
    expr_b = "3 + 2*x"
    print(f"Test: {expr_a} == {expr_b}")
    print("Result:", normalizer.expressions_equivalent(expr_a, expr_b))
    print()
    
    print("Test 6: Factored vs expanded")
    expr_c = "x^2 + 2*x + 1"
    expr_d = "(x + 1)^2"
    print(f"Test: {expr_c} == {expr_d}")
    print("Result:", normalizer.expressions_equivalent(expr_c, expr_d))