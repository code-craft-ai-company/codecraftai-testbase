"""
    .. module:: ccai.testbase.properties.propertyrunner
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
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Callable, Dict, Optional

import hashlib
import json
import os
import random
import uuid

from ccai.errors.xtraceback import create_traceback_detail, format_traceback_detail

from ccai.xmodules.xformatting import indent_lines_list

from ccai.testbase.properties.assumptions import UnsatisfiedAssumption
from ccai.testbase.properties.strategies import Strategy

from ccai.testbase.results.model.checkresult import CheckResult
from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.testresult import TestResult


DEFAULT_MAX_EXAMPLES = 100
DEFAULT_MAX_SHRINK_ATTEMPTS = 100

# Environment variable name for the per-property max-examples cap.  When set
# to a positive integer, ``PropertyRunner`` caps every property test's
# ``max_examples`` at this value, regardless of what the test specifies.
# This is intended for fast-CI runs where the full case sweep is too slow;
# nightly / release runs leave the variable unset and get full coverage.
ENV_MAX_EXAMPLES_CAP = "TESTBASE_MAX_EXAMPLES_CAP"


def _resolve_max_examples_cap() -> Optional[int]:
    """
        Read the ``TESTBASE_MAX_EXAMPLES_CAP`` environment variable and
        return it as a positive integer, or ``None`` when the variable
        is unset, empty, or not a positive integer.

        :returns: The cap value, or ``None`` to indicate "no cap".
    """
    raw = os.environ.get(ENV_MAX_EXAMPLES_CAP)
    if raw is None:
        return None

    raw_stripped = raw.strip()
    if len(raw_stripped) == 0:
        return None

    try:
        cap = int(raw_stripped)
    except ValueError:
        return None

    if cap <= 0:
        return None

    return cap


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

        The per-test seed is always derived deterministically from the job seed
        and fully qualified test name. This ensures that a given ``--job-seed``
        value always reproduces the same property test results. Each generated
        random value is derived from the previous PRNG state, guaranteeing a
        fully deterministic sequence.

        :param constraints: Dictionary of execution constraints. Supported keys:
            ``max_examples`` (int, default 100), ``max_shrink_attempts`` (int, default 100).
        :param job_seed: The job-level seed for reproducibility (UUID string).
        :param test_name: The fully qualified test name.
        :param recorder: The result recorder for writing check results.
        :param parent_inst: The instance ID of the parent test result.
        :param test_result: The parent :class:`TestResult` that receives the property metadata.
    """

    def __init__(self, constraints: dict, job_seed: str,
                 test_name: str, recorder: Any, parent_inst: str,
                 test_result: Optional[TestResult] = None):
        """
            Initializes the PropertyRunner.

            :param constraints: Dictionary of execution constraints. Supported keys:
                ``max_examples`` (int, default 100), ``max_shrink_attempts`` (int, default 100).
            :param job_seed: The job-level seed for reproducibility (UUID string).
            :param test_name: The fully qualified test name.
            :param recorder: The result recorder for writing check results.
            :param parent_inst: The instance ID of the parent test result.
            :param test_result: Optional parent :class:`TestResult` of the property test.  When
                given, :meth:`run` attaches the property metadata to it (see
                :meth:`TestResult.set_property_metadata`) on every outcome: passed, falsified,
                errored, and aborted for too many rejected assumptions.  Defaults to ``None``,
                in which case the metadata is only returned by :meth:`run` when it passes.
        """
        configured_max_examples = constraints.get("max_examples", DEFAULT_MAX_EXAMPLES)
        env_cap = _resolve_max_examples_cap()
        if env_cap is not None and env_cap < configured_max_examples:
            self._max_examples = env_cap
        else:
            self._max_examples = configured_max_examples

        self._max_shrink_attempts = constraints.get("max_shrink_attempts", DEFAULT_MAX_SHRINK_ATTEMPTS)
        self._job_seed = job_seed
        self._test_name = test_name
        self._recorder = recorder
        self._parent_inst = parent_inst
        self._test_result = test_result

        # The per-test seed is always derived from the job seed and test name.
        # This ensures full reproducibility: same job seed produces the same
        # random sequence for every property test in the job.
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

            When the runner was constructed with a ``test_result``, the property
            metadata is attached to it before this method returns or raises, so the
            parent :class:`TestResult` serializes it as ``property_metadata``.

            :param test_func: The property test function to invoke.
            :param strategies: Dictionary mapping parameter names to Strategy instances.
            :param injected_args: Dictionary of injection-resolved parameter values.
            :returns: A dictionary containing property test metadata with keys:
                ``examples_run``, ``max_examples``, ``seed``, ``job_seed``,
                ``counterexample`` (if failed), ``strategy_descriptions``,
                and ``is_property_test``.
            :raises AssertionError: Re-raised after recording when a property
                test fails (after shrinking).  It is chained to the ``AssertionError``
                of the first failing example and its message includes that failure's
                traceback.
            :raises RuntimeError: When an example raises an unexpected (non-assertion)
                exception, or when too many generated examples are rejected by ``assume()``.
        """
        max_examples = self._max_examples
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
                self._attach_metadata(
                    examples_run=examples_run,
                    max_examples=max_examples,
                    assumptions_rejected=assumptions_rejected,
                    strategy_descriptions=strategy_descriptions
                )
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

                # Attach the metadata to the test result, then re-raise as an error (no shrinking)
                self._attach_metadata(
                    examples_run=examples_run,
                    max_examples=max_examples,
                    assumptions_rejected=assumptions_rejected,
                    strategy_descriptions=strategy_descriptions
                )

                raise RuntimeError(
                    f"Property test errored on example {example_index}: {ex!r}"
                ) from ex

        safe_counterexample = None
        if counterexample is not None:
            # Safely serialize counterexample for metadata
            safe_counterexample = {}
            for k, v in counterexample.items():
                try:
                    json.dumps(v)
                    safe_counterexample[k] = v
                except (TypeError, ValueError):
                    safe_counterexample[k] = repr(v)

        # Build the property metadata and attach it to the test result
        metadata = self._attach_metadata(
            examples_run=examples_run,
            max_examples=max_examples,
            assumptions_rejected=assumptions_rejected,
            strategy_descriptions=strategy_descriptions,
            counterexample=safe_counterexample
        )

        if safe_counterexample is not None:
            err_msg_lines = [
                f"Property falsified after {examples_run} examples. "
                f"Counterexample: {safe_counterexample}",
                "",
                "FIRST FAILURE:"
            ]
            first_failure_lines = format_traceback_detail(first_failure_traceback)
            first_failure_lines = indent_lines_list(first_failure_lines, 1)
            err_msg_lines.extend(first_failure_lines)

            errmsg = os.linesep.join(err_msg_lines)
            raise AssertionError(errmsg) from first_failure_error

        return metadata

    def _attach_metadata(self, *, examples_run: int, max_examples: int,
                         assumptions_rejected: int, strategy_descriptions: Dict[str, str],
                         counterexample: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
            Builds the property-test metadata and, when the runner was given a parent
            :class:`TestResult`, attaches it to that result.

            :param examples_run: The number of examples that ran (assumption rejections excluded).
            :param max_examples: The maximum number of examples for the test.
            :param assumptions_rejected: The number of examples rejected by ``assume()``.
            :param strategy_descriptions: The ``describe()`` output of each strategy, by parameter name.
            :param counterexample: The JSON-safe (shrunk) counterexample when the property was
                falsified, otherwise ``None``.  Omitted from the metadata when ``None``.

            :returns: The metadata dictionary with the keys ``is_property_test``, ``examples_run``,
                ``max_examples``, ``seed``, ``job_seed``, ``assumptions_rejected``,
                ``strategy_descriptions`` and, when falsified, ``counterexample``.
        """
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
            metadata["counterexample"] = counterexample

        if self._test_result is not None:
            self._test_result.set_property_metadata(metadata)

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
        max_attempts = self._max_shrink_attempts
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
