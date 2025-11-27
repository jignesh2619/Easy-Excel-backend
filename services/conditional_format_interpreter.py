"""
Conditional Formatting Interpreter

Detects highlight/format prompts and returns strict schema-compliant JSON.
"""

import json
import logging
from typing import Dict, List, Tuple


class ConditionalFormattingInterpreter:
    """Dedicated helper to handle conditional-formatting prompts."""

    KEYWORDS = [
        "highlight",
        "mark",
        "color",
        "colour",
        "shade",
        "flag",
        "format cells",
        "format the cells",
        "highlight cells",
        "highlight rows",
        "conditional format",
        "make it bold",
        "make it red",
        "change the cell color",
    ]

    def __init__(self, client, model: str, schema: Dict):
        """
        Args:
            client: Shared OpenAI client instance.
            model: Model name to use.
            schema: Response schema enforcing conditional_formatting array.
        """
        self.client = client
        self.model = model
        self.schema = schema
        self.logger = logging.getLogger(__name__)

    def should_handle_prompt(self, prompt: str) -> bool:
        """Return True when the user is clearly asking for conditional formatting."""
        if not prompt:
            return False
        lowered = prompt.lower()
        return any(keyword in lowered for keyword in self.KEYWORDS)

    def interpret(self, prompt: str, available_columns: List[str]) -> Tuple[Dict, int]:
        """
        Call GPT with a strict schema to obtain conditional-formatting JSON.

        Returns:
            Tuple of parsed JSON dict and token usage.
        """
        column_context = (
            ", ".join(available_columns[:40]) if available_columns else "No columns provided"
        )
        instructions = f"""You are a conditional-formatting planner.
The dataset columns are: {column_context}

TASK:
- Examine the user request below.
- Return JSON that strictly matches the provided schema.
- Never include prose, markdown, or explanations.

RULES:
1. If the user does not specify a column, set "apply_to" to "all_columns".
2. Otherwise, "apply_to" must match one of the provided column names exactly.
3. Always set "condition_value" from the user request (trim quotes if present).
4. Pick sensible formatting defaults (background_color, font_color, bold) if the user omits them.
5. Keep the array concise—only add multiple entries if the user clearly asked for more than one rule.

USER PROMPT:
{prompt}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You must respond with JSON only. Follow the response schema exactly.",
                },
                {"role": "user", "content": instructions},
            ],
            temperature=0,
            response_format=self.schema,
        )

        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("Conditional formatting helper returned empty content.")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            self.logger.error("Failed to parse conditional-format helper response: %s", content)
            raise ValueError(f"Helper produced invalid JSON: {exc}") from exc

        usage = getattr(response, "usage", None)
        tokens_used = 0
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            tokens_used = prompt_tokens + completion_tokens

        return payload, tokens_used


