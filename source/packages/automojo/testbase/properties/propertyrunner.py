"""
    .. module:: automojo.testbase.properties.propertyrunner
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for property test execution — generation, shrinking, and result creation.

    The :class:`PropertyRunner` orchestrates the execution of a single
    property test function. It generates random inputs using declared
    strategies, invokes the test function for each set of inputs, handles
    failure detection with automatic counterexample shrinking, and creates
    :class:`CheckResult` instances for each generated example.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Callable, Dict, Optional

import hashlib
import random
import traceback
import uuid

from datetime import datetime

from automojo.errors.xtraceback import (
    TracebackDetail,
    create_traceback_detail
)

from automojo.testbase.properties.assumptions import UnsatisfiedAssumption
from automojo.testbase.properties.propertysettings import PropertySettings
from automojo.testbase.properties.strategies import Strategy

from automojo.testbase.results.model.checkresult import CheckResult
from automojo.testbase.results.model.resultcode import ResultCode


def derive_test_seed(job_seed: str, test_name: str) -> int:
    """
        Derives a unique, deterministic seed for a specific test from the job seed.

        Uses SHA-256 hashing of the combined job seed and fully qualified test
        name to produce a reproducible per-test seed. The same inputs always
        produce the same output seed, ensuring that property tests are
        reproducible when the same job seed is used.

        :param job_seed: The job-level seed value (typically a UUID string).
        :param test_name: The fully qualified test name (e.g., "pkg.module#test_func").
        :returns: An integer seed derived from the combination of job_seed and test_name.
    """
    combined = f"{job_seed}:{test_name}"
    hash_bytes = hashlib.sha256(combined.encode()).digest()
    return int.from_bytes(hash_bytes[:8], byteorder='big')


class PropertyRunner:
    """
        Orchestrates the execution of a property test function.

        The runner generates random inputs using declared strategies, invokes
        the test function for each set of inputs, detects failures, performs
        automatic counterexample shrinking, and creates :class:`CheckResult`
        instances for each generated example.

        :param settings: The :class:`PropertySettings` controlling execution.
        :param job_seed: The job-level seed for reproducibility (UUID string).
        :param test_name: The fully qualified test name.
        :param recorder: The result recorder for writing check results.
        :param parent_inst: The instance ID of the parent test result.
    """

    def __init__(self, settings: PropertySettings, job_seed: str,
                 test_name: str, recorder: Any, parent_inst: str):
        """
            Initializes the PropertyRunner.

            :param settings: The :class:`PropertySettings` controlling execution.
            :param job_seed: The job-level seed for reproducibility (UUID string).
            :param test_name: The fully qualified test name.
            :param recorder: The result recorder for writing check results.
            :param parent_inst: The instance ID of the parent test result.
        """
        self._settings = settings
        self._job_seed = job_seed
        self._test_name = test_name
        self._recorder = recorder
        self._parent_inst = parent_inst

        # Determine the per-test seed
        if settings.seed is not None:
            self._test_seed = settings.seed
        else:
            self._test_seed = derive_test_seed(job_seed, test_name)

        self._rng = random.Random(self._test_seed)
        return

    @property
    def test_seed(self) -> int:
        """
            The resolved per-test seed used for random generation.
        """
        return self._test_seed

    @property
    def job_seed(self) -> str:
        """
            The job-level seed.
        """
        return self._job_seed

    def run(self, test_func: Callable, strategies: Dict[str, Strategy],
            injected_args: Dict[str, Any]) -> Dict[str, Any]:
        """
            Executes the property test by generating examples and calling the test function.

            For each of ``max_examples`` iterations:
            
            1. Generates random values using the declared strategies
            2. Merges generated values with injected parameters
            3. Calls the test function with the combined arguments
            4. Records a :class:`CheckResult` for the example

            If any example fails with an ``AssertionError``, the runner triggers
            the shrinking engine to find a minimal counterexample, then records
            the test as FAILED. If an unexpected exception occurs, the test is
            recorded as ERRORED without shrinking.

            :param test_func: The property test function to invoke.
            :param strategies: Dictionary mapping parameter names to Strategy instances.
            :param injected_args: Dictionary of injection-resolved parameter values.
            :returns: A dictionary containing property test metadata with keys:
                ``examples_run``, ``max_examples``, ``seed``, ``job_seed``,
                ``counterexample`` (if failed), ``strategy_descriptions``,
                and ``is_property_test``.
            :raises AssertionError: Re-raised after recording when a property
                test fails (after shrinking).
        """
        max_examples = self._settings.max_examples
        examples_run = 0
        assumptions_rejected = 0
        max_rejections = 50 * max_examples
        counterexample = None
        first_failure_error = None
        first_failure_traceback = None

        strategy_descriptions = {
            name: strategy.describe() for name, strategy in strategies.items()
        }

        example_index = 0

        while examples_run < max_examples:
            # Check for too many assumption rejections
            if assumptions_rejected >= max_rejections:
                raise RuntimeError(
                    f"Too many assumption rejections ({assumptions_rejected}) "
                    f"after {examples_run} successful examples. This usually "
                    f"means the preconditions in assume() are too restrictive "
                    f"for the strategies being used."
                )

            # Generate values for this example
            generated_values = {
                name: strategy.generate(self._rng)
                for name, strategy in strategies.items()
            }

            # Merge injected and generated args
            all_args = {}
            all_args.update(injected_args)
            all_args.update(generated_values)

            # Create a check result for this example
            check_inst_id = str(uuid.uuid4())
            check_name = f"check_{example_index:04d}"

            check_result = CheckResult(
                inst_id=check_inst_id,
                name=check_name,
                parent_inst=self._parent_inst,
                generated_values=generated_values,
                example_index=example_index,
                seed=self._test_seed,
                result_code=ResultCode.UNSET
            )

            # Preview the check result
            self._recorder.preview(check_result)

            try:
                test_func(**all_args)

                # Example passed — mark and record
                check_result.finalize()
                self._recorder.record(check_result)
                examples_run += 1
                example_index += 1

            except UnsatisfiedAssumption:
                # Precondition not met — skip this example entirely
                assumptions_rejected += 1
                example_index += 1
                continue

            except AssertionError as ae:
                # Property assertion failure
                # Property assertion failure — add failure detail, then finalize
                tb_detail = create_traceback_detail(ae)
                check_result.add_failure(tb_detail)
                check_result.finalize()
                self._recorder.record(check_result)
                examples_run += 1

                # Store first failure for shrinking
                counterexample = generated_values
                first_failure_error = ae
                first_failure_traceback = tb_detail

                # Attempt to shrink the counterexample
                shrunk = self._shrink(test_func, strategies, generated_values, injected_args)
                if shrunk is not None:
                    counterexample = shrunk

                break

            except Exception as ex:
                # Unexpected error
                # Unexpected error — add error detail, then finalize
                tb_detail = create_traceback_detail(ex)
                check_result.add_error(tb_detail)
                check_result.finalize()
                self._recorder.record(check_result)

                # Build metadata and re-raise as an error (no shrinking)
                metadata = {
                    "is_property_test": True,
                    "examples_run": examples_run,
                    "max_examples": max_examples,
                    "seed": self._test_seed,
                    "job_seed": self._job_seed,
                    "assumptions_rejected": assumptions_rejected,
                    "strategy_descriptions": strategy_descriptions,
                }

                raise RuntimeError(
                    f"Property test errored on example {example_index}: {ex!r}"
                ) from ex

        # Build property metadata
        metadata = {
            "is_property_test": True,
            "examples_run": examples_run,
            "max_examples": max_examples,
            "seed": self._test_seed,
            "job_seed": self._job_seed,
            "assumptions_rejected": assumptions_rejected,
            "strategy_descriptions": strategy_descriptions,
        }

        if counterexample is not None:
            # Safely serialize counterexample for metadata
            safe_counterexample = {}
            for k, v in counterexample.items():
                try:
                    import json
                    json.dumps(v)
                    safe_counterexample[k] = v
                except (TypeError, ValueError):
                    safe_counterexample[k] = repr(v)

            metadata["counterexample"] = safe_counterexample

            raise AssertionError(
                f"Property falsified after {examples_run} examples. "
                f"Counterexample: {safe_counterexample}"
            )

        return metadata

    def _shrink(self, test_func: Callable, strategies: Dict[str, Strategy],
                failing_values: Dict[str, Any],
                injected_args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
            Attempts to shrink the failing counterexample to a simpler input.

            Iterates through each strategy parameter and tries shrunk candidates
            from the strategy's ``shrink()`` method. Only candidates that still
            reproduce the original failure are kept. The process is bounded by
            ``max_shrink_attempts``.

            :param test_func: The property test function.
            :param strategies: Dictionary mapping parameter names to strategies.
            :param failing_values: The original failing generated values.
            :param injected_args: The injected parameter values.
            :returns: The simplest failing set of generated values found,
                or ``None`` if no simpler counterexample was found.
        """
        max_attempts = self._settings.max_shrink_attempts
        attempts = 0
        current_best = dict(failing_values)
        improved = False

        for param_name, strategy in strategies.items():
            if attempts >= max_attempts:
                break

            for shrunk_value in strategy.shrink(current_best[param_name]):
                if attempts >= max_attempts:
                    break

                attempts += 1

                # Try the shrunk value
                candidate = dict(current_best)
                candidate[param_name] = shrunk_value

                all_args = {}
                all_args.update(injected_args)
                all_args.update(candidate)

                try:
                    test_func(**all_args)
                    # This candidate no longer fails — skip it
                except AssertionError:
                    # Still fails — this is a better (simpler) counterexample
                    current_best = candidate
                    improved = True
                except Exception:
                    # Different error — skip this candidate
                    pass

        return current_best if improved else None
