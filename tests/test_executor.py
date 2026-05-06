"""Tests for AsyncExecutor with mock target client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aegis.config.target_config import TargetConfig
from aegis.core.context_manager import ContextManager
from aegis.core.models import AttackCase, AttackResult
from aegis.execution.executor import AsyncExecutor
from tests.mocks.mock_target_client import MockTargetClient


@pytest.fixture
def target_config() -> TargetConfig:
    return TargetConfig(
        endpoint="http://localhost:9000/chat",
        provider="openai",
        model="gpt-4o-mini",
        api_key="test-key",
        concurrency=3,
    )


@pytest.fixture
def context() -> ContextManager:
    return ContextManager()


@pytest.fixture
def sample_cases() -> list[AttackCase]:
    return [
        AttackCase(
            attack_id=f"test-{i:03d}",
            agent_name="jailbreak",
            category="jailbreak",
            prompt=f"Test prompt {i}",
        )
        for i in range(5)
    ]


async def test_execute_batch_returns_results(
    target_config: TargetConfig,
    context: ContextManager,
    sample_cases: list[AttackCase],
) -> None:
    """execute_batch should return one result per attack case."""
    mock_client = MockTargetClient()

    executor = AsyncExecutor(
        target_config=target_config,
        context=context,
        concurrency=3,
    )

    # Patch TargetClient to use our mock
    with patch("aegis.execution.executor.TargetClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        results = await executor.execute_batch(sample_cases)

    assert len(results) == len(sample_cases)
    for result in results:
        assert isinstance(result, AttackResult)


async def test_execute_empty_batch(
    target_config: TargetConfig, context: ContextManager
) -> None:
    """execute_batch with empty list should return empty list."""
    executor = AsyncExecutor(
        target_config=target_config,
        context=context,
    )
    results = await executor.execute_batch([])
    assert results == []


async def test_execute_batch_handles_errors(
    target_config: TargetConfig,
    context: ContextManager,
    sample_cases: list[AttackCase],
) -> None:
    """execute_batch should handle individual failures gracefully."""
    from tests.mocks.mock_target_client import DownMockTargetClient

    failing_client = DownMockTargetClient()

    executor = AsyncExecutor(
        target_config=target_config,
        context=context,
        concurrency=2,
    )

    with patch("aegis.execution.executor.TargetClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=failing_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        results = await executor.execute_batch(sample_cases)

    # Should still return results even if all are error results
    assert len(results) == len(sample_cases)
    for result in results:
        assert "[ERROR]" in result.response or result.status_code == 0


async def test_executor_concurrency_limit(
    target_config: TargetConfig, context: ContextManager
) -> None:
    """Executor should respect concurrency limit."""
    import asyncio

    concurrent_count = 0
    max_concurrent = 0

    class CountingMockClient:
        async def send(self, case: AttackCase) -> AttackResult:
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return AttackResult(
                attack_id=case.attack_id,
                agent_name=case.agent_name,
                category=case.category,
                prompt=case.prompt,
                response="ok",
            )

        async def __aenter__(self) -> "CountingMockClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    target_config_2 = TargetConfig(concurrency=2)
    executor = AsyncExecutor(
        target_config=target_config_2, context=context, concurrency=2
    )

    cases = [
        AttackCase(attack_id=f"c-{i}", agent_name="t", category="t", prompt="p")
        for i in range(6)
    ]

    counting_client = CountingMockClient()
    with patch("aegis.execution.executor.TargetClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=counting_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        await executor.execute_batch(cases)

    assert max_concurrent <= 2
