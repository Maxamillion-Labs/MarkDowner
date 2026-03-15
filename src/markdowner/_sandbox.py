# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Subprocess isolation helpers for third-party parsers."""

from __future__ import annotations

import multiprocessing
import queue
from dataclasses import dataclass
from typing import Any, Callable

from ._exceptions import MarkDownerException


DEFAULT_PARSER_TIMEOUT_SECONDS = 30
DEFAULT_PARSER_MEMORY_LIMIT_BYTES = 512 * 1024 * 1024


class ParserSandboxException(MarkDownerException):
    """Base exception for parser sandbox failures."""


class ParserSandboxTimeout(ParserSandboxException):
    """Raised when a parser worker exceeds its timeout."""

    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Parser worker exceeded timeout of {timeout_seconds} seconds")


class ParserSandboxWorkerError(ParserSandboxException):
    """Raised when a parser worker returns an error."""

    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(f"Parser worker failed with {error_type}: {message}")


class ParserSandboxExited(ParserSandboxException):
    """Raised when a parser worker exits without a response."""

    def __init__(self, exit_code: int | None):
        self.exit_code = exit_code
        super().__init__(f"Parser worker exited unexpectedly with code {exit_code}")


@dataclass(frozen=True)
class ParserSandboxLimits:
    timeout_seconds: int = DEFAULT_PARSER_TIMEOUT_SECONDS
    memory_limit_bytes: int | None = DEFAULT_PARSER_MEMORY_LIMIT_BYTES


def _apply_memory_limit(memory_limit_bytes: int | None) -> None:
    if memory_limit_bytes is None:
        return

    try:
        import resource
    except ImportError:
        return

    try:
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
    except (AttributeError, OSError, ValueError):
        return


def _sandbox_worker(
    result_queue: multiprocessing.Queue,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    memory_limit_bytes: int | None,
) -> None:
    _apply_memory_limit(memory_limit_bytes)

    try:
        result_queue.put(("ok", func(*args, **kwargs)))
    except BaseException as exc:  # pragma: no cover
        result_queue.put(("error", (exc.__class__.__name__, str(exc))))


def run_in_subprocess(
    func: Callable[..., Any],
    *args: Any,
    limits: ParserSandboxLimits | None = None,
    **kwargs: Any,
) -> Any:
    """Run a top-level callable inside a subprocess and return its result."""
    sandbox_limits = limits or ParserSandboxLimits()
    ctx = multiprocessing.get_context("spawn")
    result_queue = ctx.Queue()
    process = ctx.Process(
        target=_sandbox_worker,
        args=(result_queue, func, args, kwargs, sandbox_limits.memory_limit_bytes),
    )
    process.start()
    process.join(timeout=sandbox_limits.timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        raise ParserSandboxTimeout(sandbox_limits.timeout_seconds)

    try:
        status, payload = result_queue.get_nowait()
    except queue.Empty as exc:
        raise ParserSandboxExited(process.exitcode) from exc

    if status == "error":
        error_type, message = payload
        raise ParserSandboxWorkerError(error_type, message)

    return payload
