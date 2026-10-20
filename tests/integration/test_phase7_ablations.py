"""Component-removal experiments must actually alter search, retaining honest final checks."""

from pathlib import Path

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.constraints.bounds import check_bound_violations
from prescriptxai.evaluation.ablations import (
    SearchPolicy,
    ablation_policies,
    ladder_policies,
    run_ablation_search,
)
from prescriptxai.recourse.optimizer import RecourseOptimizer
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


def test_bound_and_distribution_removal_change_actual_candidate() -> None:
    """A bounded unsafe toy case becomes model-safe only when its bound is removed."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/experiments/phase6-pipeline-v1.yaml"))
    config.recourse.max_iterations = 2
    config.recourse.alpha_steps = config.recourse.l1_escalation_steps = 1
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    taxonomy.actuator_constraints["actuator"].maximum = -1
    specs = list(taxonomy.features)
    specs[0].bounds.maximum = -1
    taxonomy.features = tuple(specs)
    state = {"actuator": -2.0, "sensor": 2.0}
    full = run_ablation_search(
        state, bundle, taxonomy, config, None, validator, SearchPolicy(), free_rate_fraction=1
    )
    unbounded = run_ablation_search(
        state,
        bundle,
        taxonomy,
        config,
        None,
        validator,
        ablation_policies()["no_bounds"],
        free_rate_fraction=1,
    )
    assert not full.model_valid and unbounded.model_valid
    assert check_bound_violations(unbounded.state, taxonomy, features=("actuator",))
    assert taxonomy.actuator_constraints["actuator"].maximum == -1


def test_default_policy_reproduces_production_and_ladder_additions() -> None:
    """Experimental defaults preserve production candidates and ladder has eight actual stages."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/experiments/phase6-pipeline-v1.yaml"))
    config.recourse.max_iterations = 2
    config.recourse.alpha_steps = config.recourse.l1_escalation_steps = 1
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    state = {"actuator": -2.0, "sensor": 2.0}
    production = RecourseOptimizer(bundle, taxonomy, mahalanobis=validator).solve(state, config)
    experimental = run_ablation_search(
        state, bundle, taxonomy, config, None, validator, SearchPolicy(), free_rate_fraction=1
    )
    assert experimental.state == production.state
    policies = ladder_policies()
    assert len(policies) == 8 and policies["L7_coupling"] == SearchPolicy()
    assert not policies["L0_all_free"].freeze_immutable
