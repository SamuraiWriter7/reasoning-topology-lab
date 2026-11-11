Reasoning Topology Lab (RTL) v0.1
Deterministic structural evaluation metrics.

Python: 3.11+
External dependencies: None

Responsibilities:
- Compare calculated values with expected results
- Evaluate matrix properties
- Evaluate complex eigenvalues
- Evaluate reachability
- Evaluate single-node fault injection
- Produce structured PASS / FAIL reports

This module does not perform matrix calculations.
Those operations belong to src/network.py.

Stage 1 mathematical validation must not be
interpreted as proof of LLM reasoning performance.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


DEFAULT_TOLERANCE = 1e-9


# --------------------------------------------------
# Basic evaluation helpers
# --------------------------------------------------

def validate_tolerance(tolerance: float) -> None:
    """Require a finite, nonnegative numerical tolerance."""
    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not math.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError(
            "Tolerance must be finite and nonnegative."
        )


def numeric_equal(
    actual: float,
    expected: float,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """Compare finite numeric values using absolute tolerance."""
    validate_tolerance(tolerance)

    if (
        isinstance(actual, bool)
        or isinstance(expected, bool)
    ):
        return False

    if not isinstance(actual, (int, float)):
        return False

    if not isinstance(expected, (int, float)):
        return False

    if not math.isfinite(actual):
        return False

    if not math.isfinite(expected):
        return False

    return abs(actual - expected) <= tolerance


def exact_equal(actual: Any, expected: Any) -> bool:
    """Compare exact values while preserving type identity."""
    return (
        type(actual) is type(expected)
        and actual == expected
    )


def make_check(
    check_id: str,
    description: str,
    actual: Any,
    expected: Any,
    passed: bool,
) -> dict[str, Any]:
    """Create a JSON-serializable validation record."""
    return {
        "check_id": check_id,
        "description": description,
        "status": "PASS" if passed else "FAIL",
        "actual": actual,
        "expected": expected,
    }


# --------------------------------------------------
# Eigenvalue comparison
# --------------------------------------------------

def parse_complex_pair(value: Any) -> complex:
    """
    Convert [real, imaginary] into a complex number.

    Both components must be finite numeric values.
    """
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
    ):
        raise ValueError(
            "Eigenvalue must be [real, imaginary]."
        )

    real, imaginary = value

    for component in (real, imaginary):
        if (
            isinstance(component, bool)
            or not isinstance(component, (int, float))
            or not math.isfinite(component)
        ):
            raise ValueError(
                "Eigenvalue components must be finite numbers."
            )

    return complex(real, imaginary)


def eigenvalues_equal(
    actual: Sequence[Any],
    expected: Sequence[Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """
    Compare complex eigenvalues without relying on order.

    Eigenvalue multiplicity is preserved.

    RTL v0.1 expects exactly three eigenvalues.
    """
    validate_tolerance(tolerance)

    if (
        not isinstance(actual, (list, tuple))
        or not isinstance(expected, (list, tuple))
        or len(actual) != 3
        or len(expected) != 3
    ):
        return False

    try:
        actual_values = [
            parse_complex_pair(value)
            for value in actual
        ]
        expected_values = [
            parse_complex_pair(value)
            for value in expected
        ]
    except ValueError:
        return False

    def match_remaining(
        index: int,
        remaining: list[complex],
    ) -> bool:
        if index == len(actual_values):
            return not remaining

        current = actual_values[index]

        for position, candidate in enumerate(remaining):
            if abs(current - candidate) <= tolerance:
                next_remaining = (
                    remaining[:position]
                    + remaining[position + 1:]
                )

                if match_remaining(
                    index + 1,
                    next_remaining,
                ):
                    return True

        return False

    return match_remaining(0, expected_values)


# --------------------------------------------------
# Matrix-property evaluation
# --------------------------------------------------

def evaluate_matrix_properties(
    result: Mapping[str, Any],
    expected: Mapping[str, Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> list[dict[str, Any]]:
    """Evaluate rank, determinant, and eigenvalues."""
    return [
        make_check(
            "MATRIX-RANK",
            "Matrix rank matches the expected value.",
            result.get("matrix_rank"),
            expected.get("rank"),
            exact_equal(
                result.get("matrix_rank"),
                expected.get("rank"),
            ),
        ),
        make_check(
            "MATRIX-DETERMINANT",
            "Determinant matches the expected value.",
            result.get("determinant"),
            expected.get("determinant"),
            exact_equal(
                result.get("determinant"),
                expected.get("determinant"),
            ),
        ),
        make_check(
            "MATRIX-EIGENVALUES",
            "Complex eigenvalues match, including multiplicity.",
            result.get("eigenvalues"),
            expected.get("eigenvalues"),
            eigenvalues_equal(
                result.get("eigenvalues"),
                expected.get("eigenvalues"),
                tolerance,
            ),
        ),
    ]


# --------------------------------------------------
# Cayley-Hamilton evaluation
# --------------------------------------------------

def evaluate_cayley_hamilton(
    result: Mapping[str, Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Evaluate the numerical Cayley-Hamilton residual."""
    residual = result.get("cayley_hamilton_residual")
    reported_valid = result.get("cayley_hamilton_valid")

    residual_passed = numeric_equal(
        residual,
        0.0,
        tolerance,
    )

    passed = (
        residual_passed
        and reported_valid is True
    )

    return make_check(
        "CAYLEY-HAMILTON",
        "Characteristic polynomial residual is within tolerance.",
        {
            "residual": residual,
            "reported_valid": reported_valid,
        },
        {
            "maximum_residual": tolerance,
            "reported_valid": True,
        },
        passed,
    )


# --------------------------------------------------
# Reachability evaluation
# --------------------------------------------------

def evaluate_reachability(
    result: Mapping[str, Any],
    expected: Mapping[str, Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> list[dict[str, Any]]:
    """Evaluate reachability and strong connectivity."""
    return [
        make_check(
            "REACHABLE-PAIRS",
            "Reachable ordered-pair count matches.",
            result.get("reachable_pairs"),
            expected.get("reachable_pairs"),
            exact_equal(
                result.get("reachable_pairs"),
                expected.get("reachable_pairs"),
            ),
        ),
        make_check(
            "REACHABILITY-RATIO",
            "Reachability ratio matches.",
            result.get("reachability_ratio"),
            expected.get("reachability_ratio"),
            numeric_equal(
                result.get("reachability_ratio"),
                expected.get("reachability_ratio"),
                tolerance,
            ),
        ),
        make_check(
            "STRONG-CONNECTIVITY",
            "Strong-connectivity status matches.",
            result.get("strongly_connected"),
            expected.get("strongly_connected"),
            exact_equal(
                result.get("strongly_connected"),
                expected.get("strongly_connected"),
            ),
        ),
    ]


# --------------------------------------------------
# Fault-injection evaluation
# --------------------------------------------------

FAULT_FIELDS = (
    "surviving_nodes",
    "reachable_pairs",
    "reachability_ratio",
    "strongly_connected",
)


def fault_result_equal(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """Compare one node-failure result."""
    if actual.get("failed_node") != expected.get("failed_node"):
        return False

    for field in FAULT_FIELDS:
        actual_value = actual.get(field)
        expected_value = expected.get(field)

        if field == "reachability_ratio":
            if not numeric_equal(
                actual_value,
                expected_value,
                tolerance,
            ):
                return False
        elif not exact_equal(actual_value, expected_value):
            return False

    return True


def evaluate_fault_results(
    actual_results: Sequence[Mapping[str, Any]],
    expected_results: Sequence[Mapping[str, Any]],
    tolerance: float = DEFAULT_TOLERANCE,
) -> list[dict[str, Any]]:
    """
    Evaluate independent single-node failure results.

    Detects:
    - Missing failure cases
    - Unexpected failure cases
    - Duplicate failed-node identifiers
    - Incorrect connectivity measurements
    """
    validate_tolerance(tolerance)

    if not isinstance(actual_results, (list, tuple)):
        raise ValueError(
            "Actual fault results must be a sequence."
        )

    if not isinstance(expected_results, (list, tuple)):
        raise ValueError(
            "Expected fault results must be a sequence."
        )

    def index_results(
        items: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, Mapping[str, Any]], set[str]]:
        indexed = {}
        duplicates = set()

        for item in items:
            if not isinstance(item, Mapping):
                raise ValueError(
                    "Fault result must be an object."
                )

            node = item.get("failed_node")

            if not isinstance(node, str) or not node:
                raise ValueError(
                    "Failed-node ID must be a nonempty string."
                )

            if node in indexed:
                duplicates.add(node)

            indexed[node] = item

        return indexed, duplicates

    actual_by_node, actual_duplicates = index_results(
        actual_results
    )

    expected_by_node, expected_duplicates = index_results(
        expected_results
    )

    if expected_duplicates:
        raise ValueError(
            "Expected fault results contain duplicate nodes."
        )

    checks = []

    checks.append(
        make_check(
            "FAULT-CASE-COVERAGE",
            "All expected failure cases appear exactly once.",
            {
                "count": len(actual_results),
                "nodes": sorted(actual_by_node),
                "duplicates": sorted(actual_duplicates),
            },
            {
                "count": len(expected_results),
                "nodes": sorted(expected_by_node),
                "duplicates": [],
            },
            (
                len(actual_results) == len(expected_results)
                and set(actual_by_node) == set(expected_by_node)
                and not actual_duplicates
            ),
        )
    )

    for node in sorted(expected_by_node):
        actual = actual_by_node.get(node)
        expected = expected_by_node[node]

        passed = (
            actual is not None
            and fault_result_equal(
                actual,
                expected,
                tolerance,
            )
            and node not in actual_duplicates
        )

        checks.append(
            make_check(
                f"FAULT-{node}",
                f"Failure result for {node} matches.",
                dict(actual) if actual is not None else None,
                dict(expected),
                passed,
            )
        )

    return checks


# --------------------------------------------------
# Topology evaluation
# --------------------------------------------------

def evaluate_topology(
    result: Mapping[str, Any],
    topology_config: Mapping[str, Any],
    expected_fault_results: Sequence[Mapping[str, Any]],
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Evaluate one canonical topology against configuration.

    Expected result schema:
        topology_config["expected"]

    Calculated result schema:
        src.network.analyze_topology(...)
    """
    validate_tolerance(tolerance)

    topology_id = topology_config["id"]
    expected = topology_config["expected"]

    if result.get("topology_id") != topology_id:
        raise ValueError(
            "Result topology ID does not match configuration."
        )

    checks = []

    checks.append(
        make_check(
            "TOPOLOGY-MATRIX",
            "Analyzed adjacency matrix matches configuration.",
            result.get("adjacency_matrix"),
            topology_config.get("adjacency_matrix"),
            exact_equal(
                result.get("adjacency_matrix"),
                topology_config.get("adjacency_matrix"),
            ),
        )
    )

    checks.append(
        make_check(
            "TOPOLOGY-ACTIVE-NODES",
            "Active-node set matches configuration.",
            result.get("active_nodes"),
            topology_config.get("active_nodes"),
            (
                isinstance(result.get("active_nodes"), list)
                and isinstance(
                    topology_config.get("active_nodes"),
                    list,
                )
                and len(result["active_nodes"])
                == len(topology_config["active_nodes"])
                and set(result["active_nodes"])
                == set(topology_config["active_nodes"])
            ),
        )
    )

    checks.extend(
        evaluate_matrix_properties(
            result,
            expected,
            tolerance,
        )
    )

    checks.append(
        evaluate_cayley_hamilton(
            result,
            tolerance,
        )
    )

    checks.extend(
        evaluate_reachability(
            result,
            expected,
            tolerance,
        )
    )

    checks.extend(
        evaluate_fault_results(
            result.get("fault_results", []),
            expected_fault_results,
            tolerance,
        )
    )

    passed_count = sum(
        check["status"] == "PASS"
        for check in checks
    )

    failed_count = len(checks) - passed_count

    return {
        "topology_id": topology_id,
        "status": "PASS" if failed_count == 0 else "FAIL",
        "total_checks": len(checks),
        "passed_checks": passed_count,
        "failed_checks": failed_count,
        "checks": checks,
    }


# --------------------------------------------------
# Complete experiment evaluation
# --------------------------------------------------

def evaluate_experiment(
    results: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Evaluate all canonical topologies.

    This function does not execute an experiment.
    It evaluates previously calculated results.

    Missing, duplicate, or unexpected topology
    results cause the experiment to fail.
    """
    tolerances = config["numerical_tolerance"]

    absolute_tolerance = tolerances["absolute"]
    eigenvalue_tolerance = tolerances["eigenvalue"]
    ch_tolerance = tolerances["cayley_hamilton_residual"]

    for tolerance in (
        absolute_tolerance,
        eigenvalue_tolerance,
        ch_tolerance,
    ):
        validate_tolerance(tolerance)

    if not isinstance(results, (list, tuple)):
        raise ValueError("Results must be a sequence.")

    result_by_id = {}
    duplicate_ids = set()

    for result in results:
        if not isinstance(result, Mapping):
            raise ValueError("Each result must be an object.")

        topology_id = result.get("topology_id")

        if not isinstance(topology_id, str):
            raise ValueError("Invalid topology ID.")

        if topology_id in result_by_id:
            duplicate_ids.add(topology_id)

        result_by_id[topology_id] = result

    expected_topologies = {
        topology["id"]: topology
        for topology in config["topologies"]
    }

    expected_ids = set(expected_topologies)
    actual_ids = set(result_by_id)

    coverage_passed = (
        expected_ids == actual_ids
        and not duplicate_ids
        and len(results) == len(expected_topologies)
    )

    topology_reports = []

    for topology in config["topologies"]:
        topology_id = topology["id"]

        if topology_id not in result_by_id:
            topology_reports.append({
                "topology_id": topology_id,
                "status": "FAIL",
                "error": "Missing topology result.",
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 1,
                "checks": [],
            })
            continue

        report = evaluate_topology(
            result_by_id[topology_id],
            topology,
            config["fault_injection"][
                "expected_results"
            ][topology_id],
            absolute_tolerance,
        )

        # Apply the configured eigenvalue tolerance.
        for check in report["checks"]:
            if check["check_id"] == "MATRIX-EIGENVALUES":
                passed = eigenvalues_equal(
                    check["actual"],
                    check["expected"],
                    eigenvalue_tolerance,
                )
                check["status"] = (
                    "PASS" if passed else "FAIL"
                )

            if check["check_id"] == "CAYLEY-HAMILTON":
                residual = check["actual"]["residual"]
                reported_valid = (
                    check["actual"]["reported_valid"]
                )

                passed = (
                    numeric_equal(
                        residual,
                        0.0,
                        ch_tolerance,
                    )
                    and reported_valid is True
                )

                check["status"] = (
                    "PASS" if passed else "FAIL"
                )
                check["expected"] = {
                    "maximum_residual": ch_tolerance,
                    "reported_valid": True,
                }

        report["passed_checks"] = sum(
            check["status"] == "PASS"
            for check in report["checks"]
        )
        report["failed_checks"] = (
            report["total_checks"]
            - report["passed_checks"]
        )
        report["status"] = (
            "PASS"
            if report["failed_checks"] == 0
            else "FAIL"
        )

        topology_reports.append(report)

    passed_topologies = sum(
        report["status"] == "PASS"
        for report in topology_reports
    )

    failed_topologies = (
        len(topology_reports) - passed_topologies
    )

    overall_passed = (
        coverage_passed
        and failed_topologies == 0
    )

    return {
        "experiment_id": config["experiment_id"],
        "spec_version": config["spec_version"],
        "stage": config["stage"],
        "status": "PASS" if overall_passed else "FAIL",
        "coverage": {
            "status": (
                "PASS" if coverage_passed else "FAIL"
            ),
            "expected_topologies": sorted(expected_ids),
            "actual_topologies": sorted(actual_ids),
            "duplicate_topologies": sorted(duplicate_ids),
        },
        "summary": {
            "total_topologies": len(expected_topologies),
            "passed_topologies": passed_topologies,
            "failed_topologies": failed_topologies,
        },
        "topologies": topology_reports,
        "interpretation": (
            "Stage 1 mathematical validation only. "
            "No LLM reasoning performance is established."
        ),
    }


# --------------------------------------------------
# Human-readable reporting
# --------------------------------------------------

def format_evaluation_report(
    evaluation: Mapping[str, Any],
) -> str:
    """Format an experiment evaluation for console output."""
    lines = [
        "=== RTL v0.1 Stage 1 Evaluation ===",
        f"Experiment: {evaluation['experiment_id']}",
        f"Status: {evaluation['status']}",
        "",
    ]

    coverage = evaluation["coverage"]

    lines.append(
        f"[{coverage['status']}] Topology coverage"
    )

    for topology in evaluation["topologies"]:
        lines.append(
            f"\n[{topology['status']}] "
            f"{topology['topology_id']}"
        )

        if "error" in topology:
            lines.append(
                f"  Error: {topology['error']}"
            )

        for check in topology.get("checks", []):
            lines.append(
                f"  [{check['status']}] "
                f"{check['check_id']}"
            )

            if check["status"] == "FAIL":
                lines.append(
                    f"    Actual: {check['actual']}"
                )
                lines.append(
                    f"    Expected: {check['expected']}"
                )

    summary = evaluation["summary"]

    lines.extend([
        "",
        "--- Summary ---",
        f"Passed topologies: {summary['passed_topologies']}",
        f"Failed topologies: {summary['failed_topologies']}",
        f"Overall status: {evaluation['status']}",
        "",
        evaluation["interpretation"],
    ])

    return "\n".join(lines)
