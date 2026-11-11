"""
Reasoning Topology Lab (RTL) v0.1
Network mathematics and graph analysis.

Stage 1: Deterministic Structural Validation

Python: 3.11+
External dependencies: None

This module provides:
- 3x3 matrix validation and operations
- Matrix rank and determinant
- Canonical topology eigenvalues
- Cayley-Hamilton identity validation
- Directed graph reachability
- Single-node fault injection
- Deterministic structural analysis

Mathematical properties are NOT treated as direct
measurements of LLM reasoning quality.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any, Sequence


Matrix = list[list[int]]
NodeIDs = list[str]

MATRIX_SIZE = 3
DEFAULT_TOLERANCE = 1e-9

CANONICAL_MATRICES: dict[str, Matrix] = {
    "single": [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ],
    "sequential": [
        [0, 1, 0],
        [0, 0, 1],
        [0, 0, 0],
    ],
    "cyclic": [
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0],
    ],
}


# --------------------------------------------------
# Matrix validation
# --------------------------------------------------

def validate_matrix(matrix: Sequence[Sequence[int]]) -> None:
    """
    Validate a binary 3x3 directed adjacency matrix.

    Raises:
        ValueError: If the matrix violates RTL v0.1 rules.
    """
    if not isinstance(matrix, (list, tuple)):
        raise ValueError("Matrix must be a sequence of rows.")

    if len(matrix) != MATRIX_SIZE:
        raise ValueError("Matrix must contain exactly 3 rows.")

    for i, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)):
            raise ValueError(f"Row {i} must be a sequence.")

        if len(row) != MATRIX_SIZE:
            raise ValueError(
                f"Row {i} must contain exactly 3 elements."
            )

        for j, value in enumerate(row):
            if type(value) is not int or value not in (0, 1):
                raise ValueError(
                    f"Matrix entry [{i}][{j}] must be 0 or 1."
                )

            if i == j and value != 0:
                raise ValueError(
                    "Self-loops are not permitted in RTL v0.1."
                )


def validate_nodes(
    node_ids: Sequence[str],
    active_nodes: Sequence[str],
) -> None:
    """Validate node identifiers and active-node membership."""
    if len(node_ids) != MATRIX_SIZE:
        raise ValueError("Exactly three node IDs are required.")

    if any(
        not isinstance(node, str) or not node
        for node in node_ids
    ):
        raise ValueError("Node IDs must be nonempty strings.")

    if len(set(node_ids)) != MATRIX_SIZE:
        raise ValueError("Node IDs must be unique.")

    if len(set(active_nodes)) != len(active_nodes):
        raise ValueError("Active nodes must be unique.")

    if not set(active_nodes).issubset(set(node_ids)):
        raise ValueError("Unknown active node.")


# --------------------------------------------------
# Matrix arithmetic
# --------------------------------------------------

def identity_matrix(size: int = MATRIX_SIZE) -> Matrix:
    """Return an identity matrix."""
    return [
        [1 if i == j else 0 for j in range(size)]
        for i in range(size)
    ]


def matrix_multiply(
    a: Sequence[Sequence[int]],
    b: Sequence[Sequence[int]],
) -> Matrix:
    """Multiply two 3x3 matrices."""
    validate_matrix_shape(a)
    validate_matrix_shape(b)

    return [
        [
            sum(a[i][k] * b[k][j] for k in range(MATRIX_SIZE))
            for j in range(MATRIX_SIZE)
        ]
        for i in range(MATRIX_SIZE)
    ]


def validate_matrix_shape(
    matrix: Sequence[Sequence[int]],
) -> None:
    """Validate only the 3x3 shape."""
    if (
        len(matrix) != MATRIX_SIZE
        or any(len(row) != MATRIX_SIZE for row in matrix)
    ):
        raise ValueError("Expected a 3x3 matrix.")


def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    """Calculate a nonnegative integer matrix power."""
    validate_matrix_shape(matrix)

    if type(exponent) is not int or exponent < 0:
        raise ValueError("Exponent must be a nonnegative integer.")

    result = identity_matrix()
    base = [list(row) for row in matrix]

    while exponent > 0:
        if exponent % 2 == 1:
            result = matrix_multiply(result, base)

        base = matrix_multiply(base, base)
        exponent //= 2

    return result


def matrix_trace(matrix: Matrix) -> int:
    """Calculate the trace of a 3x3 matrix."""
    validate_matrix_shape(matrix)
    return sum(matrix[i][i] for i in range(MATRIX_SIZE))


def matrix_determinant(matrix: Matrix) -> int:
    """Calculate the exact determinant of a 3x3 matrix."""
    validate_matrix_shape(matrix)

    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]

    return (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )


def matrix_rank(matrix: Matrix) -> int:
    """
    Calculate the rank of a 3x3 matrix.

    Uses exact integer minors for RTL v0.1
    binary adjacency matrices.
    """
    validate_matrix_shape(matrix)

    if matrix_determinant(matrix) != 0:
        return 3

    for r1 in range(3):
        for r2 in range(r1 + 1, 3):
            for c1 in range(3):
                for c2 in range(c1 + 1, 3):
                    minor = (
                        matrix[r1][c1] * matrix[r2][c2]
                        - matrix[r1][c2] * matrix[r2][c1]
                    )

                    if minor != 0:
                        return 2

    if any(value != 0 for row in matrix for value in row):
        return 1

    return 0


# --------------------------------------------------
# Eigenvalues
# --------------------------------------------------

def canonical_eigenvalues(
    topology_id: str,
    matrix: Matrix,
) -> list[complex]:
    """
    Return analytical eigenvalues for canonical RTL
    v0.1 topologies.

    This is deliberately not a general eigenvalue solver.

    The topology ID and matrix must match exactly.
    """
    validate_matrix(matrix)

    if topology_id not in CANONICAL_MATRICES:
        raise ValueError(
            f"Unsupported canonical topology: {topology_id}"
        )

    if matrix != CANONICAL_MATRICES[topology_id]:
        raise ValueError(
            "Matrix does not match its canonical topology."
        )

    if topology_id in ("single", "sequential"):
        return [0j, 0j, 0j]

    imaginary = math.sqrt(3) / 2

    return [
        complex(1.0, 0.0),
        complex(-0.5, imaginary),
        complex(-0.5, -imaginary),
    ]


def serialize_eigenvalues(
    eigenvalues: Sequence[complex],
) -> list[list[float]]:
    """Serialize complex values as [real, imaginary]."""
    return [
        [float(value.real), float(value.imag)]
        for value in eigenvalues
    ]


# --------------------------------------------------
# Cayley-Hamilton identity
# --------------------------------------------------

def cayley_hamilton_residual(matrix: Matrix) -> float:
    """
    Calculate the maximum absolute residual of:

    A^3 - c1*A^2 + c2*A - c3*I = 0

    where:
        c1 = tr(A)
        c2 = (tr(A)^2 - tr(A^2)) / 2
        c3 = det(A)
    """
    validate_matrix(matrix)

    a2 = matrix_power(matrix, 2)
    a3 = matrix_power(matrix, 3)

    c1 = matrix_trace(matrix)
    c2_numerator = c1 * c1 - matrix_trace(a2)

    if c2_numerator % 2 != 0:
        raise ArithmeticError(
            "Characteristic coefficient is not integral."
        )

    c2 = c2_numerator // 2
    c3 = matrix_determinant(matrix)

    identity = identity_matrix()
    residuals = []

    for i in range(MATRIX_SIZE):
        for j in range(MATRIX_SIZE):
            value = (
                a3[i][j]
                - c1 * a2[i][j]
                + c2 * matrix[i][j]
                - c3 * identity[i][j]
            )
            residuals.append(abs(value))

    return float(max(residuals))


def verify_cayley_hamilton(
    matrix: Matrix,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """Check the Cayley-Hamilton residual against tolerance."""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Tolerance must be finite and nonnegative.")

    return cayley_hamilton_residual(matrix) <= tolerance


# --------------------------------------------------
# Graph reachability
# --------------------------------------------------

def reachability_matrix(
    matrix: Matrix,
    node_ids: NodeIDs,
    active_nodes: NodeIDs,
) -> Matrix:
    """
    Calculate reflexive directed reachability.

    Inactive nodes have zero rows and columns.
    Active nodes reach themselves by a path of length zero.
    """
    validate_matrix(matrix)
    validate_nodes(node_ids, active_nodes)

    active = set(active_nodes)
    result = [[0] * MATRIX_SIZE for _ in range(MATRIX_SIZE)]

    for start_index, start_node in enumerate(node_ids):
        if start_node not in active:
            continue

        visited = {start_index}
        queue = deque([start_index])

        while queue:
            current = queue.popleft()

            for next_index, edge in enumerate(matrix[current]):
                if edge != 1:
                    continue

                if node_ids[next_index] not in active:
                    continue

                if next_index not in visited:
                    visited.add(next_index)
                    queue.append(next_index)

        for reachable_index in visited:
            result[start_index][reachable_index] = 1

    return result


def reachability_metrics(
    matrix: Matrix,
    node_ids: NodeIDs,
    active_nodes: NodeIDs,
) -> dict[str, Any]:
    """Calculate reachability and connectivity metrics."""
    reach = reachability_matrix(
        matrix,
        node_ids,
        active_nodes,
    )

    indices = [
        i for i, node in enumerate(node_ids)
        if node in set(active_nodes)
    ]

    n_active = len(indices)
    possible_pairs = n_active * (n_active - 1)

    reachable_pairs = sum(
        reach[i][j]
        for i in indices
        for j in indices
        if i != j
    )

    if possible_pairs == 0:
        ratio = 1.0
    else:
        ratio = reachable_pairs / possible_pairs

    return {
        "active_node_count": n_active,
        "reachable_pairs": reachable_pairs,
        "possible_pairs": possible_pairs,
        "reachability_ratio": ratio,
        "strongly_connected": (
            reachable_pairs == possible_pairs
        ),
        "reachability_matrix": reach,
    }


# --------------------------------------------------
# Fault injection
# --------------------------------------------------

def remove_node(
    active_nodes: NodeIDs,
    failed_node: str,
) -> NodeIDs:
    """
    Remove one active node without mutating the input.

    The original adjacency matrix is preserved.
    """
    if failed_node not in active_nodes:
        raise ValueError(
            f"Cannot remove inactive node: {failed_node}"
        )

    return [
        node for node in active_nodes
        if node != failed_node
    ]


def simulate_node_failure(
    matrix: Matrix,
    node_ids: NodeIDs,
    active_nodes: NodeIDs,
    failed_node: str,
) -> dict[str, Any]:
    """Run one independent node-failure experiment."""
    validate_matrix(matrix)
    validate_nodes(node_ids, active_nodes)

    survivors = remove_node(active_nodes, failed_node)

    metrics = reachability_metrics(
        matrix,
        node_ids,
        survivors,
    )

    return {
        "failed_node": failed_node,
        "surviving_nodes": metrics["active_node_count"],
        "reachable_pairs": metrics["reachable_pairs"],
        "reachability_ratio": metrics["reachability_ratio"],
        "strongly_connected": metrics["strongly_connected"],
    }


def simulate_all_single_node_failures(
    matrix: Matrix,
    node_ids: NodeIDs,
    active_nodes: NodeIDs,
) -> list[dict[str, Any]]:
    """
    Independently remove every initially active node.

    Every trial starts from the original active-node set.
    """
    validate_matrix(matrix)
    validate_nodes(node_ids, active_nodes)

    return [
        simulate_node_failure(
            matrix,
            node_ids,
            active_nodes,
            failed_node,
        )
        for failed_node in active_nodes
    ]


# --------------------------------------------------
# Complete topology analysis
# --------------------------------------------------

def analyze_topology(
    topology_id: str,
    matrix: Matrix,
    node_ids: NodeIDs,
    active_nodes: NodeIDs,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Analyze one canonical RTL topology.

    Returns JSON-serializable deterministic results.
    """
    validate_matrix(matrix)
    validate_nodes(node_ids, active_nodes)

    # Also verifies canonical matrix identity.
    eigenvalues = canonical_eigenvalues(
        topology_id,
        matrix,
    )

    reach = reachability_metrics(
        matrix,
        node_ids,
        active_nodes,
    )

    residual = cayley_hamilton_residual(matrix)

    fault_results = simulate_all_single_node_failures(
        matrix,
        node_ids,
        active_nodes,
    )

    return {
        "topology_id": topology_id,
        "adjacency_matrix": [
            list(row) for row in matrix
        ],
        "active_nodes": list(active_nodes),
        "matrix_rank": matrix_rank(matrix),
        "determinant": matrix_determinant(matrix),
        "eigenvalues": serialize_eigenvalues(eigenvalues),
        "cayley_hamilton_residual": residual,
        "cayley_hamilton_valid": (
            residual <= tolerance
        ),
        "reachable_pairs": reach["reachable_pairs"],
        "reachability_ratio": reach["reachability_ratio"],
        "strongly_connected": reach["strongly_connected"],
        "reachability_matrix": reach["reachability_matrix"],
        "fault_results": fault_results,
    }


if __name__ == "__main__":
    node_ids = ["N1", "N2", "N3"]

    active_sets = {
        "single": ["N1"],
        "sequential": ["N1", "N2", "N3"],
        "cyclic": ["N1", "N2", "N3"],
    }

    for topology_id, matrix in CANONICAL_MATRICES.items():
        result = analyze_topology(
            topology_id,
            matrix,
            node_ids,
            active_sets[topology_id],
        )

        print(f"\nTopology: {topology_id}")
        print(f"Rank: {result['matrix_rank']}")
        print(f"Determinant: {result['determinant']}")
        print(f"Eigenvalues: {result['eigenvalues']}")
        print(
            "Reachability ratio:",
            result["reachability_ratio"],
        )
        print(
            "Cayley-Hamilton valid:",
            result["cayley_hamilton_valid"],
        )
        print("Fault results:", result["fault_results"])
