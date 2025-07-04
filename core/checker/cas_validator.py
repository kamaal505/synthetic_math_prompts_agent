"""
Computer Algebra System (CAS) verification module using SymPy.

This module provides programmatic verification of mathematical solutions
for applicable problem types as part of Phase 3 enhancements.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple, Union

try:
    import sympy as sp
    from sympy import (
        E,
        Eq,
        I,
        cos,
        diff,
        exp,
        expand,
        factor,
        integrate,
        log,
        pi,
        simplify,
        sin,
        solve,
        sqrt,
        symbols,
        sympify,
        tan,
    )
    from sympy.parsing.sympy_parser import parse_expr

    SYMPY_AVAILABLE = True
    SymPyBasic = sp.Basic
except ImportError:
    SYMPY_AVAILABLE = False
    sp = None
    SymPyBasic = Any

logger = logging.getLogger(__name__)


class CASValidator:
    """
    Computer Algebra System validator using SymPy for mathematical verification.
    """

    def __init__(self):
        """Initialize the CAS validator."""
        if not SYMPY_AVAILABLE:
            logger.warning("SymPy not available. CAS validation will be disabled.")
            self.constants = {}
            self.common_vars = None
        else:
            # Common mathematical constants and functions
            self.constants = {
                "pi": sp.pi,
                "e": sp.E,
                "i": sp.I,
                "inf": sp.oo,
                "infinity": sp.oo,
            }
            # Common variable symbols
            self.common_vars = symbols("x y z t a b c n k m p q r s u v w")

    def is_available(self) -> bool:
        """Check if SymPy is available for CAS validation."""
        return SYMPY_AVAILABLE

    def parse_mathematical_expression(self, expr_str: str) -> Optional[SymPyBasic]:
        """
        Parse a mathematical expression string into a SymPy expression.

        Args:
            expr_str: String representation of mathematical expression

        Returns:
            SymPy expression or None if parsing fails
        """
        if not SYMPY_AVAILABLE:
            return None

        try:
            # Clean the expression string
            cleaned_expr = self._clean_expression_string(expr_str)

            # Try to parse the expression
            expr = parse_expr(cleaned_expr, transformations="all")
            return expr

        except Exception as e:
            logger.debug(f"Failed to parse expression '{expr_str}': {str(e)}")
            return None

    def _clean_expression_string(self, expr_str: str) -> str:
        """
        Clean and normalize expression string for SymPy parsing.

        Args:
            expr_str: Raw expression string

        Returns:
            Cleaned expression string
        """
        # Remove common formatting
        cleaned = expr_str.strip()

        # Replace common mathematical notation
        replacements = [
            (r"\^", "**"),  # Convert ^ to **
            (r"ln\(", "log("),  # Convert ln to log
            (r"√", "sqrt"),  # Convert √ to sqrt
            (r"∞", "oo"),  # Convert ∞ to oo
            (r"π", "pi"),  # Convert π to pi
            (r"∈", "in"),  # Convert ∈ to in
        ]

        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned)

        return cleaned

    def verify_algebraic_equation(
        self, problem: str, given_answer: str, computed_answer: str
    ) -> Dict[str, Any]:
        """
        Verify algebraic equation solutions.

        Args:
            problem: The problem statement
            given_answer: The provided correct answer
            computed_answer: The computed answer to verify

        Returns:
            Dictionary with verification results
        """
        if not SYMPY_AVAILABLE:
            return {
                "verified": False,
                "method": "cas_unavailable",
                "reason": "SymPy not available for CAS verification",
            }

        try:
            # Parse both answers
            given_expr = self.parse_mathematical_expression(given_answer)
            computed_expr = self.parse_mathematical_expression(computed_answer)

            if given_expr is None or computed_expr is None:
                return {
                    "verified": False,
                    "method": "parsing_failed",
                    "reason": "Could not parse one or both expressions",
                }

            # Check for algebraic equivalence
            difference = simplify(given_expr - computed_expr)

            if difference == 0:
                return {
                    "verified": True,
                    "method": "algebraic_equivalence",
                    "reason": "Expressions are algebraically equivalent",
                    "confidence": 1.0,
                }

            # Check if they're equivalent under simplification
            simplified_given = simplify(given_expr)
            simplified_computed = simplify(computed_expr)

            if simplified_given.equals(simplified_computed):
                return {
                    "verified": True,
                    "method": "simplified_equivalence",
                    "reason": "Expressions are equivalent after simplification",
                    "confidence": 0.95,
                }

            # Check numerical equivalence for specific values
            numerical_check = self._check_numerical_equivalence(
                given_expr, computed_expr
            )
            if numerical_check["equivalent"]:
                return {
                    "verified": True,
                    "method": "numerical_equivalence",
                    "reason": f"Expressions are numerically equivalent: {numerical_check['reason']}",
                    "confidence": numerical_check["confidence"],
                }

            return {
                "verified": False,
                "method": "algebraic_comparison",
                "reason": f"Expressions are not equivalent. Difference: {difference}",
                "confidence": 0.0,
            }

        except Exception as e:
            logger.error(f"CAS verification failed: {str(e)}")
            return {
                "verified": False,
                "method": "cas_error",
                "reason": f"CAS verification error: {str(e)}",
            }

    def _check_numerical_equivalence(
        self, expr1: SymPyBasic, expr2: SymPyBasic, tolerance: float = 1e-10
    ) -> Dict[str, Any]:
        """
        Check numerical equivalence by substituting test values.

        Args:
            expr1: First expression
            expr2: Second expression
            tolerance: Numerical tolerance for comparison

        Returns:
            Dictionary with equivalence check results
        """
        try:
            # Get free symbols from both expressions
            symbols_set = expr1.free_symbols.union(expr2.free_symbols)

            if not symbols_set:
                # No variables, direct numerical comparison
                val1 = float(expr1.evalf())
                val2 = float(expr2.evalf())

                if abs(val1 - val2) < tolerance:
                    return {
                        "equivalent": True,
                        "reason": f"Constant values are equal: {val1} ≈ {val2}",
                        "confidence": 1.0,
                    }
                else:
                    return {
                        "equivalent": False,
                        "reason": f"Constant values differ: {val1} vs {val2}",
                        "confidence": 0.0,
                    }

            # Test with multiple random values
            test_values = [0, 1, -1, 2, -2, 0.5, -0.5, sp.pi / 4, sp.sqrt(2)]
            equivalent_count = 0
            total_tests = 0

            for test_val in test_values:
                try:
                    # Create substitution dictionary
                    subs_dict = {sym: test_val for sym in symbols_set}

                    val1 = complex(expr1.subs(subs_dict).evalf())
                    val2 = complex(expr2.subs(subs_dict).evalf())

                    if abs(val1 - val2) < tolerance:
                        equivalent_count += 1

                    total_tests += 1

                except Exception:
                    continue

            if total_tests == 0:
                return {
                    "equivalent": False,
                    "reason": "Could not evaluate expressions numerically",
                    "confidence": 0.0,
                }

            confidence = equivalent_count / total_tests

            if confidence >= 0.9:
                return {
                    "equivalent": True,
                    "reason": f"Numerically equivalent in {equivalent_count}/{total_tests} test cases",
                    "confidence": confidence,
                }
            else:
                return {
                    "equivalent": False,
                    "reason": f"Numerically different in {total_tests - equivalent_count}/{total_tests} test cases",
                    "confidence": 1.0 - confidence,
                }

        except Exception as e:
            return {
                "equivalent": False,
                "reason": f"Numerical comparison failed: {str(e)}",
                "confidence": 0.0,
            }

    def verify_calculus_problem(
        self, problem: str, given_answer: str, computed_answer: str
    ) -> Dict[str, Any]:
        """
        Verify calculus problems (derivatives, integrals, limits).

        Args:
            problem: The problem statement
            given_answer: The provided correct answer
            computed_answer: The computed answer to verify

        Returns:
            Dictionary with verification results
        """
        if not SYMPY_AVAILABLE:
            return {
                "verified": False,
                "method": "cas_unavailable",
                "reason": "SymPy not available for CAS verification",
            }

        try:
            # Check if this is a derivative problem
            if any(
                keyword in problem.lower()
                for keyword in ["derivative", "differentiate", "d/dx", "dy/dx"]
            ):
                return self._verify_derivative(problem, given_answer, computed_answer)

            # Check if this is an integral problem
            if any(
                keyword in problem.lower() for keyword in ["integral", "integrate", "∫"]
            ):
                return self._verify_integral(problem, given_answer, computed_answer)

            # Default to algebraic verification
            return self.verify_algebraic_equation(
                problem, given_answer, computed_answer
            )

        except Exception as e:
            logger.error(f"Calculus verification failed: {str(e)}")
            return {
                "verified": False,
                "method": "calculus_error",
                "reason": f"Calculus verification error: {str(e)}",
            }

    def _verify_derivative(
        self, problem: str, given_answer: str, computed_answer: str
    ) -> Dict[str, Any]:
        """Verify derivative calculations."""
        # For derivatives, check if the derivative of the given answer
        # matches the computed answer (or vice versa)
        given_expr = self.parse_mathematical_expression(given_answer)
        computed_expr = self.parse_mathematical_expression(computed_answer)

        if given_expr is None or computed_expr is None:
            return self.verify_algebraic_equation(
                problem, given_answer, computed_answer
            )

        # Check direct equivalence first
        if simplify(given_expr - computed_expr) == 0:
            return {
                "verified": True,
                "method": "derivative_direct",
                "reason": "Derivative expressions are directly equivalent",
                "confidence": 1.0,
            }

        # Check if one is the derivative of the other
        x = symbols("x")  # Assume x is the variable

        try:
            given_derivative = diff(given_expr, x)
            if simplify(given_derivative - computed_expr) == 0:
                return {
                    "verified": True,
                    "method": "derivative_check",
                    "reason": "Computed answer is the derivative of given answer",
                    "confidence": 0.9,
                }
        except Exception:
            pass

        return self.verify_algebraic_equation(problem, given_answer, computed_answer)

    def _verify_integral(
        self, problem: str, given_answer: str, computed_answer: str
    ) -> Dict[str, Any]:
        """Verify integral calculations."""
        # For integrals, check if the derivative of both answers are equivalent
        given_expr = self.parse_mathematical_expression(given_answer)
        computed_expr = self.parse_mathematical_expression(computed_answer)

        if given_expr is None or computed_expr is None:
            return self.verify_algebraic_equation(
                problem, given_answer, computed_answer
            )

        # Check direct equivalence first
        if simplify(given_expr - computed_expr) == 0:
            return {
                "verified": True,
                "method": "integral_direct",
                "reason": "Integral expressions are directly equivalent",
                "confidence": 1.0,
            }

        # Check if derivatives are equivalent (integrals differ by constant)
        x = symbols("x")

        try:
            given_derivative = diff(given_expr, x)
            computed_derivative = diff(computed_expr, x)

            if simplify(given_derivative - computed_derivative) == 0:
                return {
                    "verified": True,
                    "method": "integral_derivative_check",
                    "reason": "Integrals differ only by a constant (derivatives are equivalent)",
                    "confidence": 0.95,
                }
        except Exception:
            pass

        return self.verify_algebraic_equation(problem, given_answer, computed_answer)


def verify_with_cas(
    problem: str, given_answer: str, computed_answer: str, problem_type: str = "auto"
) -> Dict[str, Any]:
    """
    Verify mathematical answers using Computer Algebra System.

    Args:
        problem: The problem statement
        given_answer: The provided correct answer
        computed_answer: The computed answer to verify
        problem_type: Type of problem ('algebra', 'calculus', 'auto')

    Returns:
        Dictionary with verification results
    """
    validator = CASValidator()

    if not validator.is_available():
        return {
            "verified": False,
            "method": "cas_unavailable",
            "reason": "SymPy not available for CAS verification",
            "confidence": 0.0,
        }

    if problem_type == "calculus" or (
        problem_type == "auto"
        and any(
            keyword in problem.lower()
            for keyword in [
                "derivative",
                "integral",
                "limit",
                "differentiate",
                "integrate",
            ]
        )
    ):
        return validator.verify_calculus_problem(problem, given_answer, computed_answer)
    else:
        return validator.verify_algebraic_equation(
            problem, given_answer, computed_answer
        )
