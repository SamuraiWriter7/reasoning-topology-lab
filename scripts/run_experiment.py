"""
Reasoning Topology Lab (RTL) v0.1
Stage 1 deterministic experiment runner.

Python: 3.11+
External dependencies: None

Run from repository root:

    python scripts/run_experiment.py

Responsibilities:
- Load the experiment configuration
- Validate essential configuration constraints
- Execute canonical topology analysis
- Repeat execution to check reproducibility
- Compare results with expected values
- Save a deterministic JSON report
- Return a nonzero exit code on failure

This runner validates mathematical and graph
properties only. It does not execute LLM tasks
or establish reasoning performance improvements.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# --------------------------------------------------
# Repository paths and imports
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.network import (  # noqa: E402
    CANONICAL_MATRICES,
    analyze_topology,
    validate_matrix,
    validate_nodes,
)

from src.metrics import (  # noqa: E402
    evaluate_experiment,
    format_evaluation_report,
    validate_tolerance,
)


DEFAULT_CONFIG = (
    ROOT / "configs" / "experiment-v0.1.json"
)

DEFAULT_OUTPUT = (
    ROOT / "results" / "stage1-results.json"
)

EXPECTED_TOPOLOGIES = {
    "single": ["N1"],
    "sequential": ["N1", "N2", "N3"],
    "cyclic": ["N1", "N2", "N3"],
}


# --------------------------------------------------
# Configuration loading
# --------------------------------------------------

def load_configuration(path: Path) -> dict[str, Any]:
    """
    Load JSON configuration.

    Reject duplicate JSON object keys and
    nonstandard NaN/Infinity constants.
    """

    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        result = {}

        for key, value in pairs:
            if key in result:
                raise ValueError(
                    f"Duplicate JSON key: {key}"
                )
            result[key] = value

        return result

    def reject_constant(value: str) -> None:
        raise ValueError(
            f"Nonstandard JSON constant: {value}"
        )

    if not path.is_file():
        raise FileNotFoundError(
            f"Configuration not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = json.load(
            file,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )

    if not isinstance(config, dict):
        raise ValueError(
            "Configuration root must be an object."
        )

    return config


# --------------------------------------------------
# Configuration validation
# --------------------------------------------------

def validate_configuration(
    config: dict[str, Any],
) -> None:
    """
    Validate the RTL v0.1 canonical configuration.

    This is a targeted validation of essential
    experiment constraints, not a general JSON
    Schema validator.
    """
    if config.get("experiment_id") != "RTL-EXP-0.1":
        raise ValueError(
            "Invalid experiment identifier."
        )

    if config.get("spec_version") != "0.1.0":
        raise ValueError(
            "Unsupported specification version."
        )

    if type(config.get("stage")) is not int:
        raise ValueError("Stage must be an integer.")

    if config["stage"] != 1:
        raise ValueError(
            "RTL v0.1 runner supports Stage 1 only."
        )

    if config.get("experiment_type") != (
        "deterministic_structural_validation"
    ):
        raise ValueError(
            "Unsupported experiment type."
        )

    if type(config.get("node_count")) is not int:
        raise ValueError("Node count must be an integer.")

    if config["node_count"] != 3:
        raise ValueError(
            "RTL v0.1 requires exactly three nodes."
        )

    nodes = config.get("nodes")

    if not isinstance(nodes, list) or len(nodes) != 3:
        raise ValueError(
            "Configuration must contain three nodes."
        )

    if any(
        not isinstance(node, dict)
        or not isinstance(node.get("id"), str)
        or not isinstance(node.get("role"), str)
        or not node["role"]
        for node in nodes
    ):
        raise ValueError("Invalid node definition.")

    node_ids = [node["id"] for node in nodes]

    if node_ids != ["N1", "N2", "N3"]:
        raise ValueError(
            "Canonical node order must be N1, N2, N3."
        )

    validate_nodes(node_ids, node_ids)

    expected_roles = [
        "strategy",
        "research",
        "audit",
    ]

    if [node["role"] for node in nodes] != expected_roles:
        raise ValueError(
            "Canonical node roles do not match."
        )

    convention = config.get("matrix_convention")

    if not isinstance(convention, dict):
        raise ValueError(
            "Missing matrix convention."
        )

    required_conventions = {
        "type": "directed_binary_adjacency",
        "edge_direction": "row_to_column",
        "self_loops_allowed": False,
        "inactive_node_policy": (
            "exclude_from_effective_graph"
        ),
        "reachability": "reflexive",
        "single_node_reachability_ratio": 1.0,
        "zero_node_reachability_ratio": 1.0,
    }

    for key, expected in required_conventions.items():
        actual = convention.get(key)

        if (
            type(actual) is not type(expected)
            or actual != expected
        ):
            raise ValueError(
                f"Invalid matrix convention: {key}"
            )

    tolerances = config.get("numerical_tolerance")

    if not isinstance(tolerances, dict):
        raise ValueError(
            "Missing numerical tolerance configuration."
        )

    for key in (
        "absolute",
        "eigenvalue",
        "cayley_hamilton_residual",
    ):
        if key not in tolerances:
            raise ValueError(
                f"Missing numerical tolerance: {key}"
            )

        validate_tolerance(tolerances[key])

    topologies = config.get("topologies")

    if not isinstance(topologies, list):
        raise ValueError(
            "Topologies must be a list."
        )

    if len(topologies) != 3:
        raise ValueError(
            "Exactly three topologies are required."
        )

    topology_ids = []

    for topology in topologies:
        if not isinstance(topology, dict):
            raise ValueError(
                "Topology must be an object."
            )

        topology_id = topology.get("id")
        topology_ids.append(topology_id)

        if topology_id not in EXPECTED_TOPOLOGIES:
            raise ValueError(
                f"Unknown topology: {topology_id}"
            )

        matrix = topology.get("adjacency_matrix")
        active_nodes = topology.get("active_nodes")

        validate_matrix(matrix)

        if not isinstance(active_nodes, list):
            raise ValueError(
                "Active nodes must be a list."
            )

        validate_nodes(node_ids, active_nodes)

        if matrix != CANONICAL_MATRICES[topology_id]:
            raise ValueError(
                f"Noncanonical matrix: {topology_id}"
            )

        if active_nodes != EXPECTED_TOPOLOGIES[topology_id]:
            raise ValueError(
                f"Invalid active nodes: {topology_id}"
            )

        if not isinstance(topology.get("expected"), dict):
            raise ValueError(
                f"Missing expected values: {topology_id}"
            )

    if set(topology_ids) != set(EXPECTED_TOPOLOGIES):
        raise ValueError(
            "Canonical topology coverage is incomplete."
        )

    if len(set(topology_ids)) != len(topology_ids):
        raise ValueError(
            "Duplicate topology identifiers."
        )

    fault = config.get("fault_injection")

    if not isinstance(fault, dict):
        raise ValueError(
            "Missing fault injection configuration."
        )

    expected_fault_settings = {
        "enabled": True,
        "mode": "single_active_node_removal",
        "reset_before_each_trial": True,
        "remove_incident_edges": True,
        "test_all_active_nodes": True,
    }

    for key, expected in expected_fault_settings.items():
        actual = fault.get(key)

        if (
            type(actual) is not type(expected)
            or actual != expected
        ):
            raise ValueError(
                f"Invalid fault setting: {key}"
            )

    fault_expected = fault.get("expected_results")

    if not isinstance(fault_expected, dict):
        raise ValueError(
            "Missing expected fault results."
        )

    if set(fault_expected) != set(EXPECTED_TOPOLOGIES):
        raise ValueError(
            "Expected fault topology coverage mismatch."
        )

    for topology_id, active_nodes in (
        EXPECTED_TOPOLOGIES.items()
    ):
        cases = fault_expected[topology_id]

        if not isinstance(cases, list):
            raise ValueError(
                f"Invalid fault cases: {topology_id}"
            )

        failed_nodes = []

        for case in cases:
            if not isinstance(case, dict):
                raise ValueError(
                    "Fault case must be an object."
                )

            failed_nodes.append(case.get("failed_node"))

        if (
            len(failed_nodes) != len(active_nodes)
            or set(failed_nodes) != set(active_nodes)
            or len(set(failed_nodes)) != len(failed_nodes)
        ):
            raise ValueError(
                f"Fault case coverage mismatch: {topology_id}"
            )

    validation = config.get("validation")

    if not isinstance(validation, dict):
        raise ValueError(
            "Missing validation configuration."
        )

    if validation.get("deterministic") is not True:
        raise ValueError(
            "Stage 1 must be deterministic."
        )

    repeat_runs = validation.get("repeat_runs")

    if (
        type(repeat_runs) is not int
        or repeat_runs < 2
    ):
        raise ValueError(
            "At least two repeated runs are required."
        )

    required_ids = [
        f"RTL-{index:03d}"
        for index in range(1, 14)
    ]

    if validation.get("required_test_ids") != required_ids:
        raise ValueError(
            "Required test IDs do not match RTL v0.1."
        )

    reporting = config.get("reporting")

    if not isinstance(reporting, dict):
        raise ValueError(
            "Missing reporting configuration."
        )

    if reporting.get("format") != "json":
        raise ValueError(
            "RTL v0.1 supports JSON reporting only."
        )

    if reporting.get("include_llm_performance_claims") is not False:
        raise ValueError(
            "LLM performance claims are not permitted."
        )

    if reporting.get("output_path") != (
        "results/stage1-results.json"
    ):
        raise ValueError(
            "Unexpected canonical output path."
        )

    for field in (
        "include_matrix_properties",
        "include_reachability",
        "include_fault_results",
        "include_validation_status",
    ):
        if reporting.get(field) is not True:
            raise ValueError(
                f"Required reporting field disabled: {field}"
            )


# --------------------------------------------------
# Execution
# --------------------------------------------------

def execute_once(
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Execute the three canonical topology analyses.

    Each topology begins from its original
    adjacency matrix and active-node set.
    """
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


def canonical_json(value: Any) -> str:
    """
    Serialize a value deterministically.

    NaN and Infinity are rejected.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def execute_repeated(
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Execute repeated deterministic trials.

    Each execution must produce exactly the same
    serialized mathematical results.
    """
    repeat_runs = config["validation"]["repeat_runs"]

    baseline = execute_once(config)
    baseline_serialized = canonical_json(baseline)

    matches = []

    for run_index in range(1, repeat_runs + 1):
        if run_index == 1:
            current_serialized = baseline_serialized
        else:
            current_serialized = canonical_json(
                execute_once(config)
            )

        matches.append(
            {
                "run": run_index,
                "matches_baseline": (
                    current_serialized == baseline_serialized
                ),
            }
        )

    reproducible = all(
        item["matches_baseline"]
        for item in matches
    )

    return baseline, {
        "status": "PASS" if reproducible else "FAIL",
        "repeat_runs": repeat_runs,
        "runs": matches,
    }


# --------------------------------------------------
# Reporting
# --------------------------------------------------

def build_report(
    config: dict[str, Any],
    results: list[dict[str, Any]],
    evaluation: dict[str, Any],
    reproducibility: dict[str, Any],
) -> dict[str, Any]:
    """Build a complete Stage 1 report."""

    overall_passed = (
        evaluation["status"] == "PASS"
        and reproducibility["status"] == "PASS"
    )

    return {
        "experiment_id": config["experiment_id"],
        "spec_version": config["spec_version"],
        "stage": 1,
        "experiment_type": config["experiment_type"],
        "status": "PASS" if overall_passed else "FAIL",
        "configuration": {
            "node_count": config["node_count"],
            "topologies": [
                topology["id"]
                for topology in config["topologies"]
            ],
            "numerical_tolerance": config[
                "numerical_tolerance"
            ],
        },
        "results": results,
        "evaluation": evaluation,
        "reproducibility": reproducibility,
        "limitations": [
            "Stage 1 validates mathematical and graph properties.",
            "No LLM inference was executed.",
            "Network connectivity does not establish task completion.",
            "Matrix properties do not directly measure reasoning quality.",
        ],
    }


def save_report(
    report: dict[str, Any],
    output_path: Path,
) -> None:
    """Save a deterministic, human-readable JSON report."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    )

    output_path.write_text(
        serialized + "\n",
        encoding="utf-8",
    )


# --------------------------------------------------
# Main experiment workflow
# --------------------------------------------------

def run_experiment(
    config_path: Path = DEFAULT_CONFIG,
    output_path: Path = DEFAULT_OUTPUT,
) -> int:
    """
    Run the complete RTL v0.1 Stage 1 workflow.

    Returns:
        0: All structural checks passed.
        1: Validation failure or execution error.
    """
    try:
        print("=== RTL v0.1 Stage 1 Experiment ===")
        print(f"Configuration: {config_path}")
        print()

        config = load_configuration(config_path)
        validate_configuration(config)

        print("[PASS] Configuration validation")

        results, reproducibility = execute_repeated(
            config
        )

        print(
            f"[{reproducibility['status']}] "
            "Deterministic reproducibility"
        )

        evaluation = evaluate_experiment(
            results,
            config,
        )

        print()
        print(format_evaluation_report(evaluation))

        report = build_report(
            config,
            results,
            evaluation,
            reproducibility,
        )

        save_report(report, output_path)

        print()
        print(f"Report saved: {output_path}")
        print(f"Final status: {report['status']}")

        if report["status"] != "PASS":
            return 1

        return 0

    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        ArithmeticError,
    ) as error:
        print(
            f"[FAIL] Experiment execution: {error}",
            file=sys.stderr,
        )
        return 1


# --------------------------------------------------
# Command-line interface
# --------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run RTL v0.1 deterministic "
            "structural validation."
        )
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to the experiment configuration.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the JSON result report.",
    )

    args = parser.parse_args()

    return run_experiment(
        config_path=args.config,
        output_path=args.output,
    )


if __name__ == "__main__":
    sys.exit(main())
