"""
Tests for Session.run_in_background() and the associated
session._wait_for_background_tasks() lifecycle mechanism.
"""

import threading
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

from dify_plugin.core.runtime import Session
from dify_plugin.core.server.stdio.request_reader import StdioRequestReader
from dify_plugin.core.server.stdio.response_writer import StdioResponseWriter
from dify_plugin.entities.tool import ToolInvokeMessage, ToolRuntime
from dify_plugin.interfaces.tool import Tool


def _make_session() -> Session:
    return Session(
        session_id="test",
        executor=ThreadPoolExecutor(max_workers=4),
        reader=StdioRequestReader(),
        writer=StdioResponseWriter(),
    )


# ---------------------------------------------------------------------------
# Unit tests for Session.run_in_background / _wait_for_background_tasks
# ---------------------------------------------------------------------------


_MAX_NO_TASK_WAIT_SECONDS = 0.5
"""Maximum expected wall-clock time (seconds) for _wait_for_background_tasks
when no background tasks have been registered."""


def test_run_in_background_executes_task():
    """run_in_background should execute the provided callable."""
    session = _make_session()
    results: list[int] = []

    session.run_in_background(lambda: results.append(42))
    session._wait_for_background_tasks()

    assert results == [42]


def test_run_in_background_passes_args_and_kwargs():
    """run_in_background should forward positional and keyword arguments."""
    session = _make_session()
    captured: list = []

    def task(a, b, *, key):
        captured.append((a, b, key))

    session.run_in_background(task, 1, 2, key="value")
    session._wait_for_background_tasks()

    assert captured == [(1, 2, "value")]


def test_run_in_background_returns_thread():
    """run_in_background should return the started Thread."""
    session = _make_session()
    thread = session.run_in_background(lambda: time.sleep(0))
    assert isinstance(thread, threading.Thread)
    session._wait_for_background_tasks()


def test_wait_for_background_tasks_blocks_until_done():
    """_wait_for_background_tasks must not return before the task finishes."""
    session = _make_session()
    finished = threading.Event()

    def slow_task():
        time.sleep(0.1)
        finished.set()

    session.run_in_background(slow_task)
    session._wait_for_background_tasks()

    assert finished.is_set(), "_wait_for_background_tasks returned before the background task completed"


def test_multiple_background_tasks_all_waited():
    """All background tasks should be awaited, not just the first one."""
    session = _make_session()
    results: list[int] = []
    lock = threading.Lock()

    def task(value: int):
        time.sleep(0.05)
        with lock:
            results.append(value)

    for i in range(5):
        session.run_in_background(task, i)

    session._wait_for_background_tasks()

    assert sorted(results) == list(range(5))


def test_background_task_exception_does_not_propagate():
    """
    An exception inside a background task should be swallowed (logged) and
    must not prevent _wait_for_background_tasks from completing normally.
    """
    session = _make_session()

    def failing_task():
        raise RuntimeError("intentional error")

    session.run_in_background(failing_task)
    # Should not raise
    session._wait_for_background_tasks()


def test_no_background_tasks_wait_returns_immediately():
    """_wait_for_background_tasks on a fresh session should be a no-op."""
    session = _make_session()
    start = time.monotonic()
    session._wait_for_background_tasks()
    elapsed = time.monotonic() - start
    assert elapsed < _MAX_NO_TASK_WAIT_SECONDS, "wait took too long when there are no background tasks"


def test_task_removed_from_list_after_completion():
    """Background task list should be empty once all tasks complete."""
    session = _make_session()

    session.run_in_background(lambda: None)
    session._wait_for_background_tasks()

    with session._background_tasks_lock:
        remaining = list(session._background_tasks)
    assert remaining == [], f"Expected empty task list, got {remaining}"


# ---------------------------------------------------------------------------
# Integration: background tasks survive past _invoke generator exhaustion
# ---------------------------------------------------------------------------


def test_session_kept_alive_for_background_task():
    """
    Simulate the scenario described in the issue:
    A tool's _invoke starts a background thread via session.run_in_background,
    immediately returns (generator exhausted), and the background thread
    completes its work afterwards.

    _wait_for_background_tasks is called by the executor *after* the generator
    is exhausted, so the background thread should still be able to finish.
    """
    background_ran = threading.Event()

    class MyTool(Tool):
        def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
            def background_work():
                # Simulate calling session.storage or session.app.chat.invoke
                time.sleep(0.05)
                background_ran.set()

            # Register with session so the executor waits for it
            self.session.run_in_background(background_work)

            yield self.create_text_message("done")

    session = _make_session()
    tool = MyTool(
        runtime=ToolRuntime(credentials={}, user_id="test", session_id="test"),
        session=session,
    )

    # Exhaust the generator (mimics what Plugin._execute_request does)
    list(tool.invoke({}))

    # Now wait for background tasks (mimics what Plugin._execute_request does)
    session._wait_for_background_tasks()

    assert background_ran.is_set(), "Background task did not complete"


def test_cascading_background_tasks():
    """
    Background tasks that themselves spawn more background tasks via
    session.run_in_background should all be awaited.
    """
    session = _make_session()
    depth_reached = threading.Event()

    def inner_task():
        time.sleep(0.02)
        depth_reached.set()

    def outer_task():
        time.sleep(0.02)
        # Spawn a nested background task
        session.run_in_background(inner_task)

    session.run_in_background(outer_task)
    session._wait_for_background_tasks()

    assert depth_reached.is_set(), "Nested background task did not complete"
