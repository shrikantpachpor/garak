"""Helpers to normalize attempt dictionaries for persisted reports.

This module centralizes write-time normalization rules so all report writers
produce identical JSON shapes without changing in-memory Attempt objects.

Rule implemented:
- Keep top-level `notes` as {} when empty.
- Convert `prompt.notes` from {} -> null.
- Convert each conversation dict's `notes` from {} -> null.
- Leave message-level and output-level `notes` as {}.
"""

from typing import Any, Dict, List


def normalize_attempt_for_persistence(d: Dict[str, Any]) -> Dict[str, Any]:
    """Mutate and return `d` so its nested `notes` follow the original tool's
    persisted representation.

    Only the following are converted from empty dict -> None:
    - d['prompt']['notes']
    - each conv in d['conversations']: conv['notes']

    Everything else is left untouched to preserve tests that expect empty
    dicts in other locations (e.g. outputs[].notes, message content notes).
    """
    try:
        if not isinstance(d, dict):
            return d

        # Prompt-level notes -> null
        prompt = d.get("prompt")
        if isinstance(prompt, dict):
            if "notes" in prompt and prompt.get("notes") == {}:
                prompt["notes"] = None

        # Conversations: each conversation dict's notes -> null
        convs = d.get("conversations")
        if isinstance(convs, list):
            for conv in convs:
                if isinstance(conv, dict) and conv.get("notes") == {}:
                    conv["notes"] = None

    except Exception:
        # Make normalization best-effort; never raise during report write
        return d
    return d
