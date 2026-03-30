"""OpenAI Batch API implementation of LLMProvider."""
import io
import json
import logging
import uuid
from typing import Optional

import openai

from src.llm.provider import BatchRequest, BatchResult, LLMProvider

logger = logging.getLogger(__name__)

# gpt-4o batch pricing (50% off standard as of 2025)
# Standard: input $2.50/1M, output $10.00/1M
# Batch:    input $1.25/1M, output $5.00/1M
INPUT_PRICE_PER_1M_TOKENS = 1.25
OUTPUT_PRICE_PER_1M_TOKENS = 5.00

# Status mapping from OpenAI batch statuses to our canonical statuses
STATUS_MAP = {
    "validating": "pending",
    "in_progress": "running",
    "finalizing": "running",
    "completed": "completed",
    "failed": "failed",
    "expired": "failed",
    "cancelling": "failed",
    "cancelled": "cancelled",
}


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def _build_jsonl(self, requests: list[BatchRequest]) -> bytes:
        """Build JSONL file content for the batch API."""
        lines = []
        for req in requests:
            body: dict = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": req.system_prompt},
                    {"role": "user", "content": req.user_prompt},
                ],
                "max_tokens": req.max_tokens,
                "temperature": req.temperature,
            }
            if req.response_format:
                body["response_format"] = req.response_format

            line = {
                "custom_id": req.custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": body,
            }
            lines.append(json.dumps(line))

        return "\n".join(lines).encode("utf-8")

    def submit_batch(self, requests: list[BatchRequest]) -> str:
        """Upload JSONL, create batch, return batch_id."""
        if not requests:
            raise ValueError("Cannot submit empty batch")

        jsonl_bytes = self._build_jsonl(requests)
        logger.info(f"Uploading batch file ({len(jsonl_bytes):,} bytes, {len(requests)} requests)...")

        # Upload the file
        batch_file = self.client.files.create(
            file=("batch_requests.jsonl", io.BytesIO(jsonl_bytes), "application/json"),
            purpose="batch",
        )
        logger.info(f"File uploaded: {batch_file.id}")

        # Create the batch
        batch = self.client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"source": "agi-tracker"},
        )
        logger.info(f"Batch created: {batch.id}")
        return batch.id

    def check_batch_status(self, batch_id: str) -> str:
        """Check and return canonical status string."""
        batch = self.client.batches.retrieve(batch_id)
        raw_status = batch.status
        canonical = STATUS_MAP.get(raw_status, "running")
        logger.debug(f"Batch {batch_id}: raw={raw_status}, canonical={canonical}")
        return canonical

    def get_batch_results(self, batch_id: str) -> list[BatchResult]:
        """Download and parse batch output file."""
        batch = self.client.batches.retrieve(batch_id)

        if not batch.output_file_id:
            if batch.error_file_id:
                logger.warning(f"Batch {batch_id} has errors — downloading error file")
                error_content = self.client.files.content(batch.error_file_id)
                error_lines = error_content.text.strip().split("\n")
                results = []
                for line in error_lines:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        results.append(BatchResult(
                            custom_id=obj.get("custom_id", "unknown"),
                            content="",
                            tokens_input=0,
                            tokens_output=0,
                            cost_usd=0.0,
                            error=obj.get("error", {}).get("message", "Unknown error"),
                        ))
                    except json.JSONDecodeError:
                        pass
                return results
            raise RuntimeError(f"Batch {batch_id} has no output file and no error file")

        output_content = self.client.files.content(batch.output_file_id)
        lines = output_content.text.strip().split("\n")

        results: list[BatchResult] = []
        for line in lines:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse output line: {e}")
                continue

            custom_id = obj.get("custom_id", "unknown")
            response = obj.get("response", {})
            error = obj.get("error")

            if error:
                results.append(BatchResult(
                    custom_id=custom_id,
                    content="",
                    tokens_input=0,
                    tokens_output=0,
                    cost_usd=0.0,
                    error=str(error),
                ))
                continue

            body = response.get("body", {})
            choices = body.get("choices", [])
            usage = body.get("usage", {})

            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "") or ""

            tokens_input = usage.get("prompt_tokens", 0)
            tokens_output = usage.get("completion_tokens", 0)
            cost_usd = (
                tokens_input * INPUT_PRICE_PER_1M_TOKENS / 1_000_000
                + tokens_output * OUTPUT_PRICE_PER_1M_TOKENS / 1_000_000
            )

            results.append(BatchResult(
                custom_id=custom_id,
                content=content,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost_usd,
            ))

        logger.info(f"Batch {batch_id}: {len(results)} results parsed")
        return results
