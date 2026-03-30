"""Abstract LLM provider interface for batch processing."""
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    custom_id: str
    system_prompt: str
    user_prompt: str
    max_tokens: int = 4096
    temperature: float = 0.2
    response_format: Optional[dict] = None  # e.g. {"type": "json_object"}


@dataclass
class BatchResult:
    custom_id: str
    content: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    error: Optional[str] = None


class LLMProvider(ABC):
    @abstractmethod
    def submit_batch(self, requests: list[BatchRequest]) -> str:
        """Submit a batch of requests. Returns a batch_id."""

    @abstractmethod
    def check_batch_status(self, batch_id: str) -> str:
        """
        Check batch status.
        Returns one of: 'pending', 'running', 'completed', 'failed', 'cancelled'.
        """

    @abstractmethod
    def get_batch_results(self, batch_id: str) -> list[BatchResult]:
        """Retrieve results after batch is completed."""

    def wait_for_batch(
        self,
        batch_id: str,
        poll_interval_seconds: int = 60,
        max_wait_hours: int = 25,
    ) -> list[BatchResult]:
        """Poll until the batch completes or times out. Returns results."""
        max_polls = (max_wait_hours * 3600) // poll_interval_seconds
        for i in range(max_polls):
            status = self.check_batch_status(batch_id)
            logger.info(f"Batch {batch_id} status: {status} (poll {i + 1}/{max_polls})")
            if status == "completed":
                return self.get_batch_results(batch_id)
            if status in ("failed", "cancelled"):
                raise RuntimeError(f"Batch {batch_id} ended with status: {status}")
            time.sleep(poll_interval_seconds)
        raise TimeoutError(
            f"Batch {batch_id} did not complete within {max_wait_hours} hours"
        )
