Reasoning Topology Lab (RTL) v0.1
Stage 1 deterministic validation tests.

Python: 3.11+
External dependencies: None

Run from repository root:

    python -m unittest discover -s tests -v

This suite covers RTL-001 through RTL-013.

Passing these tests validates the implemented
mathematical and graph operations, not the
quality of LLM reasoning.
"""

from __future__ import annotations

import copy
import json
import math
import sys
import unittest
from pathlib import Path


# --------------------------------------------------
# Repository imports
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.network import (  # noqa: E402
    CANONICAL_MATRICES,
    analyze_topology,
    canonical_eigenvalues,
    cayley_hamilton_residual,
    identity_matrix,
    matrix_determinant,
    matrix_multiply,
    matrix_power,
    matrix_rank,
    reachability_matrix,
    reachability_metrics,
    remove_node,
    simulate_all_single_node_failures,
    simulate_node_failure,
    validate_matrix,
    validate_nodes,
    verify_cayley_hamilton,
)

from src.metrics import (  # noqa: E402
    eigenvalues_equal,
    evaluate_experiment,
    evaluate_fault_results,
    evaluate_topology,
    format_evaluation_report,
    numeric_equal,
)


CONFIG_PATH = (
    ROOT / "configs" / "experiment-v0.1.json"
)

NODE_IDS = ["N1", "N2", "N3"]


# --------------------------------------------------
# Shared fixtures
# --------------------------------------------------

def load_config() -> dict:
    """Load the canonical experiment configuration."""
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def calculate_results(config: dict) -> list[dict]:
    """Calculate all configured topology results."""
    node_ids = [
        node["id"]
        for node in config["nodes"]
    ]

    tolerance = config[
        "numerical_tolerance"
    ]["cayley_hamilton_residual"]

    results = []

    for topology in config["topologies"]:
        result = analyze_topology(
            topology_id=topology["id"],
            matrix=topology["adjacency_matrix"],
            node_ids=node_ids,
            active_nodes=topology["active_nodes"],
            tolerance=tolerance,
        )

        results.append(result)

    return results


class RTLTestCase(unittest.TestCase):
    """Base class with shared configuration."""

    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def get_topology(self, topology_id: str) -> dict:
        return next(
            topology
            for topology in self.config["topologies"]
            if topology["id"] == topology_id
        )


# --------------------------------------------------
# RTL-001: Node configuration
# --------------------------------------------------

class TestNodeConfiguration(RTLTestCase):

    def test_rtl_001_exactly_three_nodes(self):
        self.assertEqual(
            self.config["node_count"],
            3,
        )

        self.assertEqual(
            len(self.config["nodes"]),
            3,
        )

        self.assertEqual(
            [
                node["id"]
                for node in self.config["nodes"]
            ],
            NODE_IDS,
        )

    def test_rtl_001_unique_node_ids(self):
        ids = [
            node["id"]
            for node in self.config["nodes"]
        ]

        self.assertEqual(
            len(ids),
            len(set(ids)),
        )

    def test_rtl_001_invalid_node_sets(self):
        with self.assertRaises(ValueError):
            validate_nodes(
                ["N1", "N2"],
                ["N1"],
            )

        with self.assertRaises(ValueError):
            validate_nodes(
                ["N1", "N1", "N3"],
                ["N1"],
            )

        with self.assertRaises(ValueError):
            validate_nodes(
                NODE_IDS,
                ["N4"],
            )

        with self.assertRaises(ValueError):
            validate_nodes(
                NODE_IDS,
                ["N1", "N1"],
            )


# --------------------------------------------------
# RTL-002 to RTL-004: Matrix validation
# --------------------------------------------------

class TestMatrixValidation(RTLTestCase):

    def test_rtl_002_matrix_dimensions(self):
        for topology in self.config["topologies"]:
            with self.subTest(topology=topology["id"]):
                matrix = topology["adjacency_matrix"]

                self.assertEqual(len(matrix), 3)
                self.assertTrue(
                    all(len(row) == 3 for row in matrix)
                )

                validate_matrix(matrix)

    def test_rtl_002_invalid_dimensions(self):
        invalid_matrices = [
            [[0, 1], [1, 0]],
            [[0, 0, 0]],
            [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0],
            ],
        ]

        for matrix in invalid_matrices:
            with self.subTest(matrix=matrix):
                with self.assertRaises(ValueError):
                    validate_matrix(matrix)

    def test_rtl_003_binary_entries(self):
        invalid_values = [
            2,
            -1,
            0.5,
            True,
            False,
            "1",
            None,
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                matrix = copy.deepcopy(
                    CANONICAL_MATRICES["single"]
                )

                matrix[0][1] = value

                with self.assertRaises(ValueError):
                    validate_matrix(matrix)

    def test_rtl_004_no_self_loops(self):
        for topology in self.config["topologies"]:
            matrix = topology["adjacency_matrix"]

            self.assertTrue(
                all(
                    matrix[i][i] == 0
                    for i in range(3)
                )
            )

        matrix = copy.deepcopy(
            CANONICAL_MATRICES["cyclic"]
        )

        matrix[1][1] = 1

        with self.assertRaises(ValueError):
            validate_matrix(matrix)


# --------------------------------------------------
# RTL-005: Canonical topology definitions
# --------------------------------------------------

class TestCanonicalTopologies(RTLTestCase):

    def test_rtl_005_topology_identifiers(self):
        actual_ids = {
            topology["id"]
            for topology in self.config["topologies"]
        }

        self.assertEqual(
            actual_ids,
            {"single", "sequential", "cyclic"},
        )

    def test_rtl_005_canonical_matrices(self):
        for topology in self.config["topologies"]:
            topology_id = topology["id"]

            with self.subTest(topology=topology_id):
                self.assertEqual(
                    topology["adjacency_matrix"],
                    CANONICAL_MATRICES[topology_id],
                )

    def test_rtl_005_active_nodes(self):
        expected_active = {
            "single": ["N1"],
            "sequential": NODE_IDS,
            "cyclic": NODE_IDS,
        }

        for topology_id, expected in expected_active.items():
            topology = self.get_topology(topology_id)

            self.assertEqual(
                topology["active_nodes"],
                expected,
            )


# --------------------------------------------------
# Matrix arithmetic
# --------------------------------------------------

class TestMatrixArithmetic(unittest.TestCase):

    def test_identity_matrix(self):
        self.assertEqual(
            identity_matrix(),
            [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ],
        )

    def test_matrix_multiplication(self):
        matrix = CANONICAL_MATRICES["sequential"]

        expected_square = [
            [0, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
        ]

        self.assertEqual(
            matrix_multiply(matrix, matrix),
            expected_square,
        )

    def test_matrix_power_zero(self):
        matrix = CANONICAL_MATRICES["cyclic"]

        self.assertEqual(
            matrix_power(matrix, 0),
            identity_matrix(),
        )

    def test_cyclic_matrix_cubed(self):
        matrix = CANONICAL_MATRICES["cyclic"]

        self.assertEqual(
            matrix_power(matrix, 3),
            identity_matrix(),
        )

    def test_negative_matrix_power_rejected(self):
        with self.assertRaises(ValueError):
            matrix_power(
                CANONICAL_MATRICES["cyclic"],
                -1,
            )


# --------------------------------------------------
# RTL-006: Rank and determinant
# --------------------------------------------------

class TestMatrixProperties(RTLTestCase):

    def test_rtl_006_expected_rank(self):
        expected_ranks = {
            "single": 0,
            "sequential": 2,
            "cyclic": 3,
        }

        for topology_id, expected in expected_ranks.items():
            with self.subTest(topology=topology_id):
                self.assertEqual(
                    matrix_rank(
                        CANONICAL_MATRICES[topology_id]
                    ),
                    expected,
                )

    def test_rtl_006_expected_determinant(self):
        expected_determinants = {
            "single": 0,
            "sequential": 0,
            "cyclic": 1,
        }

        for topology_id, expected in (
            expected_determinants.items()
        ):
            with self.subTest(topology=topology_id):
                self.assertEqual(
                    matrix_determinant(
                        CANONICAL_MATRICES[topology_id]
                    ),
                    expected,
                )

    def test_rank_one_matrix(self):
        matrix = [
            [0, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        self.assertEqual(
            matrix_rank(matrix),
            1,
        )


# --------------------------------------------------
# RTL-007: Eigenvalues
# --------------------------------------------------

class TestEigenvalues(RTLTestCase):

    def test_rtl_007_canonical_eigenvalues(self):
        for topology in self.config["topologies"]:
            topology_id = topology["id"]

            with self.subTest(topology=topology_id):
                actual = canonical_eigenvalues(
                    topology_id,
                    topology["adjacency_matrix"],
                )

                serialized = [
                    [value.real, value.imag]
                    for value in actual
                ]

                expected = topology[
                    "expected"
                ]["eigenvalues"]

                self.assertTrue(
                    eigenvalues_equal(
                        serialized,
                        expected,
                        tolerance=1e-9,
                    )
                )

    def test_eigenvalue_order_independence(self):
        actual = [
            [1.0, 0.0],
            [-0.5, math.sqrt(3) / 2],
            [-0.5, -math.sqrt(3) / 2],
        ]

        expected = list(reversed(actual))

        self.assertTrue(
            eigenvalues_equal(actual, expected)
        )

    def test_eigenvalue_multiplicity(self):
        actual = [
            [0.0, 0.0],
            [0.0, 0.0],
            [1.0, 0.0],
        ]

        expected = [
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
        ]

        self.assertFalse(
            eigenvalues_equal(actual, expected)
        )

    def test_noncanonical_matrix_rejected(self):
        with self.assertRaises(ValueError):
            canonical_eigenvalues(
                "cyclic",
                CANONICAL_MATRICES["sequential"],
            )

    def test_unknown_topology_rejected(self):
        with self.assertRaises(ValueError):
            canonical_eigenvalues(
                "unknown",
                CANONICAL_MATRICES["single"],
            )


# --------------------------------------------------
# RTL-008: Cayley-Hamilton
# --------------------------------------------------

class TestCayleyHamilton(RTLTestCase):

    def test_rtl_008_identity(self):
        tolerance = self.config[
            "numerical_tolerance"
        ]["cayley_hamilton_residual"]

        for topology in self.config["topologies"]:
            topology_id = topology["id"]
            matrix = topology["adjacency_matrix"]

            with self.subTest(topology=topology_id):
                residual = cayley_hamilton_residual(
                    matrix
                )

                self.assertLessEqual(
                    residual,
                    tolerance,
                )

                self.assertTrue(
                    verify_cayley_hamilton(
                        matrix,
                        tolerance,
                    )
                )

    def test_invalid_tolerance_rejected(self):
        matrix = CANONICAL_MATRICES["cyclic"]

        for tolerance in [-1.0, math.nan, math.inf]:
            with self.subTest(tolerance=tolerance):
                with self.assertRaises(ValueError):
                    verify_cayley_hamilton(
                        matrix,
                        tolerance,
                    )

    def test_cayley_hamilton_is_not_quality_metric(self):
        """
        A valid matrix identity must not be interpreted
        as an empirical LLM quality measurement.
        """
        for matrix in CANONICAL_MATRICES.values():
            self.assertTrue(
                verify_cayley_hamilton(matrix)
            )


# --------------------------------------------------
# RTL-009: Reachability
# --------------------------------------------------

class TestReachability(RTLTestCase):

    def test_rtl_009_expected_reachability(self):
        expected_values = {
            "single": (0, 1.0, True),
            "sequential": (3, 0.5, False),
            "cyclic": (6, 1.0, True),
        }

        for topology in self.config["topologies"]:
            topology_id = topology["id"]

            metrics = reachability_metrics(
                topology["adjacency_matrix"],
                NODE_IDS,
                topology["active_nodes"],
            )

            pairs, ratio, connected = (
                expected_values[topology_id]
            )

            with self.subTest(topology=topology_id):
                self.assertEqual(
                    metrics["reachable_pairs"],
                    pairs,
                )

                self.assertAlmostEqual(
                    metrics["reachability_ratio"],
                    ratio,
                )

                self.assertEqual(
                    metrics["strongly_connected"],
                    connected,
                )

    def test_sequential_reachability_matrix(self):
        actual = reachability_matrix(
            CANONICAL_MATRICES["sequential"],
            NODE_IDS,
            NODE_IDS,
        )

        expected = [
            [1, 1, 1],
            [0, 1, 1],
            [0, 0, 1],
        ]

        self.assertEqual(actual, expected)

    def test_cyclic_reachability_matrix(self):
        actual = reachability_matrix(
            CANONICAL_MATRICES["cyclic"],
            NODE_IDS,
            NODE_IDS,
        )

        self.assertEqual(
            actual,
            [
                [1, 1, 1],
                [1, 1, 1],
                [1, 1, 1],
            ],
        )

    def test_single_reachability_matrix(self):
        actual = reachability_matrix(
            CANONICAL_MATRICES["single"],
            NODE_IDS,
            ["N1"],
        )

        self.assertEqual(
            actual,
            [
                [1, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ],
        )


# --------------------------------------------------
# RTL-010 to RTL-012: Fault injection
# --------------------------------------------------

class TestFaultInjection(RTLTestCase):

    def test_rtl_010_each_active_node_removed(self):
        for topology in self.config["topologies"]:
            results = simulate_all_single_node_failures(
                topology["adjacency_matrix"],
                NODE_IDS,
                topology["active_nodes"],
            )

            failed_nodes = [
                result["failed_node"]
                for result in results
            ]

            with self.subTest(topology=topology["id"]):
                self.assertEqual(
                    failed_nodes,
                    topology["active_nodes"],
                )

    def test_rtl_010_independent_fault_trials(self):
        active_nodes = NODE_IDS.copy()

        first = remove_node(active_nodes, "N1")
        second = remove_node(active_nodes, "N2")

        self.assertEqual(first, ["N2", "N3"])
        self.assertEqual(second, ["N1", "N3"])

        self.assertEqual(active_nodes, NODE_IDS)

    def test_rtl_011_inactive_nodes_excluded(self):
        matrix = CANONICAL_MATRICES["cyclic"]

        actual = reachability_matrix(
            matrix,
            NODE_IDS,
            ["N1", "N2"],
        )

        self.assertEqual(
            actual,
            [
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
            ],
        )

    def test_rtl_011_zero_node_convention(self):
        metrics = reachability_metrics(
            CANONICAL_MATRICES["single"],
            NODE_IDS,
            [],
        )

        self.assertEqual(
            metrics["active_node_count"],
            0,
        )

        self.assertEqual(
            metrics["reachable_pairs"],
            0,
        )

        self.assertEqual(
            metrics["reachability_ratio"],
            1.0,
        )

        self.assertTrue(
            metrics["strongly_connected"]
        )

    def test_rtl_012_expected_fault_results(self):
        expected_by_topology = self.config[
            "fault_injection"
        ]["expected_results"]

        for topology in self.config["topologies"]:
            topology_id = topology["id"]

            actual = simulate_all_single_node_failures(
                topology["adjacency_matrix"],
                NODE_IDS,
                topology["active_nodes"],
            )

            checks = evaluate_fault_results(
                actual,
                expected_by_topology[topology_id],
            )

            with self.subTest(topology=topology_id):
                self.assertTrue(
                    all(
                        check["status"] == "PASS"
                        for check in checks
                    )
                )

    def test_fault_results_detect_wrong_ratio(self):
        topology = self.get_topology("sequential")

        actual = simulate_all_single_node_failures(
            topology["adjacency_matrix"],
            NODE_IDS,
            topology["active_nodes"],
        )

        actual[0]["reachability_ratio"] = 1.0

        checks = evaluate_fault_results(
            actual,
            self.config[
                "fault_injection"
            ]["expected_results"]["sequential"],
        )

        self.assertTrue(
            any(
                check["status"] == "FAIL"
                for check in checks
            )
        )

    def test_fault_results_detect_missing_case(self):
        topology = self.get_topology("cyclic")

        actual = simulate_all_single_node_failures(
            topology["adjacency_matrix"],
            NODE_IDS,
            topology["active_nodes"],
        )

        actual.pop()

        checks = evaluate_fault_results(
            actual,
            self.config[
                "fault_injection"
            ]["expected_results"]["cyclic"],
        )

        self.assertEqual(
            checks[0]["status"],
            "FAIL",
        )

    def test_fault_results_detect_duplicate_case(self):
        topology = self.get_topology("cyclic")

        actual = simulate_all_single_node_failures(
            topology["adjacency_matrix"],
            NODE_IDS,
            topology["active_nodes"],
        )

        actual[2] = copy.deepcopy(actual[0])

        checks = evaluate_fault_results(
            actual,
            self.config[
                "fault_injection"
            ]["expected_results"]["cyclic"],
        )

        self.assertEqual(
            checks[0]["status"],
            "FAIL",
        )

    def test_removing_inactive_node_rejected(self):
        with self.assertRaises(ValueError):
            simulate_node_failure(
                CANONICAL_MATRICES["single"],
                NODE_IDS,
                ["N1"],
                "N2",
            )


# --------------------------------------------------
# RTL-013: Deterministic reproducibility
# --------------------------------------------------

class TestDeterminism(RTLTestCase):

    def test_rtl_013_repeated_results_identical(self):
        repeat_runs = self.config[
            "validation"
        ]["repeat_runs"]

        self.assertGreaterEqual(repeat_runs, 2)

        baseline = calculate_results(self.config)

        for _ in range(repeat_runs - 1):
            current = calculate_results(self.config)

            self.assertEqual(
                current,
                baseline,
            )

    def test_rtl_013_serialized_results_identical(self):
        first = json.dumps(
            calculate_results(self.config),
            sort_keys=True,
            allow_nan=False,
        )

        second = json.dumps(
            calculate_results(self.config),
            sort_keys=True,
            allow_nan=False,
        )

        self.assertEqual(first, second)

    def test_input_matrices_not_mutated(self):
        topology = self.get_topology("cyclic")

        matrix = copy.deepcopy(
            topology["adjacency_matrix"]
        )

        original = copy.deepcopy(matrix)

        analyze_topology(
            "cyclic",
            matrix,
            NODE_IDS,
            NODE_IDS,
        )

        self.assertEqual(matrix, original)


# --------------------------------------------------
# Evaluation engine
# --------------------------------------------------

class TestEvaluationEngine(RTLTestCase):

    def test_complete_experiment_passes(self):
        results = calculate_results(self.config)

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "PASS",
        )

        self.assertEqual(
            evaluation["summary"]["passed_topologies"],
            3,
        )

        self.assertEqual(
            evaluation["summary"]["failed_topologies"],
            0,
        )

    def test_each_topology_passes(self):
        results = calculate_results(self.config)

        fault_expected = self.config[
            "fault_injection"
        ]["expected_results"]

        for result in results:
            topology_id = result["topology_id"]
            topology = self.get_topology(topology_id)

            evaluation = evaluate_topology(
                result,
                topology,
                fault_expected[topology_id],
            )

            with self.subTest(topology=topology_id):
                self.assertEqual(
                    evaluation["status"],
                    "PASS",
                )

    def test_missing_topology_detected(self):
        results = calculate_results(self.config)

        results.pop()

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "FAIL",
        )

        self.assertEqual(
            evaluation["coverage"]["status"],
            "FAIL",
        )

    def test_duplicate_topology_detected(self):
        results = calculate_results(self.config)

        results.append(copy.deepcopy(results[0]))

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "FAIL",
        )

        self.assertEqual(
            evaluation["coverage"]["status"],
            "FAIL",
        )

    def test_incorrect_rank_detected(self):
        results = calculate_results(self.config)

        results[1]["matrix_rank"] = 3

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "FAIL",
        )

    def test_incorrect_eigenvalue_detected(self):
        results = calculate_results(self.config)

        results[2]["eigenvalues"][0] = [2.0, 0.0]

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "FAIL",
        )

    def test_incorrect_reachability_detected(self):
        results = calculate_results(self.config)

        results[1]["reachability_ratio"] = 1.0

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "FAIL",
        )

    def test_cayley_hamilton_failure_detected(self):
        results = calculate_results(self.config)

        results[0]["cayley_hamilton_residual"] = 0.1
        results[0]["cayley_hamilton_valid"] = False

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        self.assertEqual(
            evaluation["status"],
            "FAIL",
        )

    def test_report_format(self):
        results = calculate_results(self.config)

        evaluation = evaluate_experiment(
            results,
            self.config,
        )

        report = format_evaluation_report(evaluation)

        self.assertIn(
            "RTL v0.1 Stage 1 Evaluation",
            report,
        )

        self.assertIn(
            "Overall status: PASS",
            report,
        )

    def test_numeric_comparison_rejects_nan(self):
        self.assertFalse(
            numeric_equal(math.nan, 0.0)
        )

        self.assertFalse(
            numeric_equal(math.inf, 0.0)
        )

        self.assertFalse(
            numeric_equal(True, 1.0)
        )


# --------------------------------------------------
# Specification consistency
# --------------------------------------------------

class TestSpecificationConsistency(RTLTestCase):

    def test_required_validation_ids(self):
        expected_ids = [
            f"RTL-{number:03d}"
            for number in range(1, 14)
        ]

        self.assertEqual(
            self.config[
                "validation"
            ]["required_test_ids"],
            expected_ids,
        )

    def test_stage_one_only(self):
        self.assertEqual(
            self.config["stage"],
            1,
        )

        self.assertEqual(
            self.config["experiment_type"],
            "deterministic_structural_validation",
        )

    def test_no_llm_performance_claims(self):
        self.assertFalse(
            self.config[
                "reporting"
            ]["include_llm_performance_claims"]
        )

    def test_fault_injection_enabled(self):
        fault = self.config["fault_injection"]

        self.assertTrue(fault["enabled"])
        self.assertTrue(
            fault["reset_before_each_trial"]
        )
        self.assertTrue(
            fault["test_all_active_nodes"]
        )

    def test_node_failure_preserves_matrix(self):
        matrix = copy.deepcopy(
            CANONICAL_MATRICES["cyclic"]
        )

        original = copy.deepcopy(matrix)

        simulate_all_single_node_failures(
            matrix,
            NODE_IDS,
            NODE_IDS,
        )

        self.assertEqual(matrix, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
