"""Shared context-integrity instructions prepended to every LLM system prompt."""

CONTEXT_INTEGRITY_BLOCK = """
## Response envelope (mandatory)

Every response MUST be a single JSON object with exactly this top-level shape:

{
  "missing_context": <true|false>,
  "missing": [<string>, ...],
  "detail": "<string>",
  "payload": <object|null>
}

Rules:
1. Before answering, decide whether the system and user messages together contain everything required to complete the task without using outside facts, unstated assumptions, or general knowledge not present in the messages.
2. If ANY required information is missing, unclear, or absent from the provided context: set "missing_context" to true, list short labels in "missing", explain in "detail" (one paragraph) what is missing and why the task cannot be completed, set "payload" to null. Do not add any other top-level keys. Do not provide a partial or guessed answer inside "payload".
3. If context is sufficient: set "missing_context" to false, "missing" to [], "detail" to "", and put the task output ONLY inside "payload" (a JSON object matching the task schema described elsewhere).
4. If you are uncertain whether context is sufficient, treat it as insufficient (missing_context: true).
5. Do not mix a full task answer with missing_context: true in the same response.
"""


def apply_context_integrity(system_prompt: str) -> str:
    """Prepend the integrity + envelope rules to a system prompt."""
    return CONTEXT_INTEGRITY_BLOCK.strip() + "\n\n" + system_prompt.strip()
