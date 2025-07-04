"""
Few-shot examples and adversarial techniques for enhanced problem generation.

This module provides curated examples and techniques to improve the quality
and difficulty of generated math problems as part of Phase 3 enhancements.
"""

from typing import Dict, List, Optional

# Few-shot examples organized by subject and difficulty level
FEW_SHOT_EXAMPLES = {
    "Algebra (High School)": {
        "Quadratic Equations and Functions": [
            {
                "problem": "A projectile is launched from the ground with an initial velocity of 64 feet per second. Its height h(t) in feet after t seconds is given by h(t) = -16t² + 64t. However, due to air resistance, the actual height is reduced by 2% for every second after launch. Find the exact time when the projectile hits the ground, accounting for air resistance.",
                "answer": "t = 2/(0.98^t + 1) ≈ 3.92 seconds",
                "hints": {
                    "0": "Set up the equation with air resistance: h(t) = (-16t² + 64t) × (0.98)^t = 0",
                    "1": "This creates a transcendental equation that cannot be solved algebraically",
                    "2": "Use numerical methods or graphing to find where the function equals zero",
                    "3": "The solution involves finding the intersection of exponential decay and quadratic motion",
                },
            }
        ],
        "Systems of Linear Equations": [
            {
                "problem": "A company produces three products A, B, and C. The profit per unit is $3, $5, and $4 respectively. Due to resource constraints: 2A + 3B + C ≤ 100, A + 2B + 3C ≤ 120, and A + B + C ≤ 50. However, there's a hidden constraint: the total production cost follows the equation 4A + 6B + 5C = 200 + 0.1(A²+ B² + C²). Find the production levels that maximize profit while satisfying all constraints.",
                "answer": "A = 10, B = 15, C = 20 (approximately, requires optimization techniques)",
                "hints": {
                    "0": "This is a nonlinear optimization problem disguised as a linear system",
                    "1": "The quadratic term in the cost constraint makes this non-trivial",
                    "2": "Use Lagrange multipliers or substitute to eliminate one variable",
                    "3": "The optimal solution lies at the boundary of the feasible region",
                },
            }
        ],
    },
    "Calculus": {
        "Integration Techniques": [
            {
                "problem": "Evaluate the integral ∫₀^π sin(x)cos(x)e^(sin²(x)) dx. The integrand appears to have a simple antiderivative, but there's a subtle trap.",
                "answer": "π/2 × (e - 1)",
                "hints": {
                    "0": "Don't be fooled by the apparent u-substitution with u = sin(x)",
                    "1": "The presence of both sin(x) and cos(x) suggests integration by parts might be needed",
                    "2": "Consider the substitution u = sin²(x), then du = 2sin(x)cos(x)dx",
                    "3": "The limits of integration change: when x = 0, u = 0; when x = π, u = 0 again",
                    "4": "This creates a path integral that requires careful analysis of the domain",
                },
            }
        ],
        "Multivariable Calculus": [
            {
                "problem": "Find the maximum value of f(x,y) = xy subject to the constraint x² + y² = 1, but with the additional condition that x and y must satisfy the implicit equation x³ + y³ = xy + 1/2.",
                "answer": "Maximum value is 1/2 at (1/√2, 1/√2)",
                "hints": {
                    "0": "This problem has two constraints, making it more complex than standard Lagrange multipliers",
                    "1": "First check if the constraints are compatible by solving the system",
                    "2": "The cubic constraint significantly restricts the feasible region on the unit circle",
                    "3": "Use parametric representation of the circle and substitute into the cubic constraint",
                    "4": "The solution requires solving a high-degree polynomial equation",
                },
            }
        ],
    },
    "Linear Algebra": {
        "Eigenvalues and Eigenvectors": [
            {
                "problem": "Consider the matrix A = [[2, 1, 0], [1, 2, 1], [0, 1, 2]]. Find the eigenvalues, but then determine the eigenvalues of the matrix B = A³ - 3A² + 2A - I, where I is the identity matrix. Express your answer in terms of the original eigenvalues of A.",
                "answer": "If λ are eigenvalues of A, then eigenvalues of B are λ³ - 3λ² + 2λ - 1",
                "hints": {
                    "0": "First find the eigenvalues of A using the characteristic polynomial",
                    "1": "A is a tridiagonal matrix with a special structure",
                    "2": "The eigenvalues of A are 2 + 2cos(kπ/4) for k = 1, 2, 3",
                    "3": "Use the property that if λ is an eigenvalue of A, then p(λ) is an eigenvalue of p(A)",
                    "4": "Evaluate p(λ) = λ³ - 3λ² + 2λ - 1 for each eigenvalue of A",
                },
            }
        ]
    },
    "Number Theory": {
        "Modular Arithmetic": [
            {
                "problem": "Find the last three digits of 7^(7^(7^7)). The tower of exponents makes direct computation impossible.",
                "answer": "343",
                "hints": {
                    "0": "We need to find 7^(7^(7^7)) mod 1000",
                    "1": "Use Euler's theorem: if gcd(a,n) = 1, then a^φ(n) ≡ 1 (mod n)",
                    "2": "Since 1000 = 8 × 125, use Chinese Remainder Theorem",
                    "3": "First find 7^(7^7) mod φ(1000) = φ(8) × φ(125) = 4 × 100 = 400",
                    "4": "Then compute 7^(7^7) mod 400, which requires finding 7^7 mod φ(400)",
                },
            }
        ]
    },
    "Real Analysis": {
        "Sequences and Series": [
            {
                "problem": "Consider the series Σ(n=1 to ∞) sin(n)/n^p. For which values of p does this series converge? The presence of sin(n) makes standard convergence tests insufficient.",
                "answer": "Converges for p > 0, conditionally for 0 < p ≤ 1, absolutely for p > 1",
                "hints": {
                    "0": "The oscillating nature of sin(n) requires Dirichlet's test or Abel's test",
                    "1": "Consider the partial sums of sin(n) using complex exponentials",
                    "2": "The key insight is that Σsin(n) has bounded partial sums",
                    "3": "Apply Dirichlet's test with a_n = 1/n^p and b_n = sin(n)",
                    "4": "For absolute convergence, need |sin(n)/n^p| ≤ 1/n^p, so need p > 1",
                },
            }
        ]
    },
}

# Adversarial techniques for creating challenging problems
ADVERSARIAL_TECHNIQUES = [
    "Combine concepts from different mathematical areas (e.g., number theory with calculus)",
    "Include misleading information or red herrings that seem relevant but aren't",
    "Use problems that appear to have simple solutions but require advanced techniques",
    "Create multi-step problems where each step depends on the previous in non-obvious ways",
    "Include boundary cases or special values that break common solution approaches",
    "Use problems with multiple valid approaches where the obvious one doesn't work",
    "Include constraints or conditions that significantly change the problem's difficulty",
    "Create problems where computational approaches fail and theoretical insight is needed",
    "Use familiar-looking problems with subtle modifications that change the solution method",
    "Include problems that require recognizing when standard techniques don't apply",
]

# Difficulty escalation strategies
DIFFICULTY_STRATEGIES = {
    "High School": [
        "Add realistic constraints or conditions",
        "Require multi-step reasoning with intermediate calculations",
        "Include problems that test conceptual understanding, not just computation",
    ],
    "Undergraduate": [
        "Combine multiple mathematical concepts in a single problem",
        "Require proof techniques or theoretical justification",
        "Include problems with non-standard approaches or multiple solution methods",
    ],
    "Graduate": [
        "Require deep theoretical understanding and advanced techniques",
        "Include problems that test the limits of standard methods",
        "Create problems that require novel approaches or insights",
    ],
    "Research": [
        "Include open-ended aspects or connections to current research",
        "Require synthesis of multiple advanced mathematical areas",
        "Create problems that push the boundaries of known techniques",
    ],
}


def get_few_shot_examples(
    subject: str, topic: str, max_examples: int = 2
) -> List[Dict]:
    """
    Get few-shot examples for a specific subject and topic.

    Args:
        subject: The mathematical subject
        topic: The specific topic within the subject
        max_examples: Maximum number of examples to return

    Returns:
        List of example problems with solutions and hints
    """
    subject_examples = FEW_SHOT_EXAMPLES.get(subject, {})
    topic_examples = subject_examples.get(topic, [])

    return topic_examples[:max_examples]


def get_adversarial_techniques(difficulty_level: str = None) -> List[str]:
    """
    Get adversarial techniques for creating challenging problems.

    Args:
        difficulty_level: Optional difficulty level to get specific strategies

    Returns:
        List of adversarial techniques and strategies
    """
    techniques = ADVERSARIAL_TECHNIQUES.copy()

    if difficulty_level and difficulty_level in DIFFICULTY_STRATEGIES:
        techniques.extend(DIFFICULTY_STRATEGIES[difficulty_level])

    return techniques


def build_enhanced_prompt_context(
    subject: str,
    topic: str,
    difficulty_level: Optional[str] = None,
    topic_description: Optional[str] = None,
) -> str:
    """
    Build enhanced context for problem generation prompts.

    Args:
        subject: The mathematical subject
        topic: The specific topic
        difficulty_level: The difficulty level
        topic_description: Description of the topic

    Returns:
        Enhanced prompt context string
    """
    context_parts = []

    # Add difficulty and topic context
    if difficulty_level:
        context_parts.append(f"Generate a {difficulty_level} level problem")

    if topic_description:
        context_parts.append(f"Topic focus: {topic_description}")

    # Add few-shot examples
    examples = get_few_shot_examples(subject, topic, max_examples=1)
    if examples:
        context_parts.append("\nExample of a high-quality challenging problem:")
        example = examples[0]
        context_parts.append(f"Problem: {example['problem']}")
        context_parts.append(f"Answer: {example['answer']}")
        context_parts.append(
            "Hints: " + "; ".join([f"{k}: {v}" for k, v in example["hints"].items()])
        )

    # Add adversarial techniques
    techniques = get_adversarial_techniques(difficulty_level)[
        :3
    ]  # Use top 3 techniques
    if techniques:
        context_parts.append(f"\nUse these techniques to make the problem challenging:")
        for i, technique in enumerate(techniques, 1):
            context_parts.append(f"{i}. {technique}")

    return "\n".join(context_parts)
