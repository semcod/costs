"""Tokenizers for accurate LLM token counting."""

from typing import Optional, Dict
import re
from functools import lru_cache


@lru_cache(maxsize=32)
def _encoding_for_model(model: Optional[str]):
    """Cache only model metadata, never source text or credentials."""
    import tiktoken

    name = (model or "").lower()
    if name.startswith("openrouter/"):
        name = name[len("openrouter/") :]
    if name.startswith("openai/"):
        name = name[len("openai/") :]
    try:
        return tiktoken.encoding_name_for_model(name), True
    except KeyError:
        return "cl100k_base", False


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class Tokenizer:
    """Local counting; unsupported models use an explicitly approximate encoding."""

    def _get_tiktoken(self, model: Optional[str] = None):
        import tiktoken

        return tiktoken.get_encoding(_encoding_for_model(model)[0])

    def describe(self, model: Optional[str] = None) -> dict:
        encoding, exact = _encoding_for_model(model)
        return {
            "tokenizer": encoding,
            "input_tokens": "tokenized" if exact else "approximate",
            "output_tokens": "heuristic",
        }

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count literal text without treating special-token strings as controls.

        This counts text, not provider-specific chat framing. Claude and other
        unsupported model families use cl100k_base as a local approximation.
        No provider clients are created and no inference requests are made.
        """
        if not text:
            return 0
        return len(self._get_tiktoken(model).encode_ordinary(text))

    def _count_claude_tokens(self, text: str) -> int:
        """Compatibility wrapper for the local Claude approximation."""
        return self.count_tokens(text, "claude")

    def estimate_tokens_simple(self, text: str) -> int:
        """
        Simple heuristic without external dependencies.
        Used as last resort fallback.
        This is an uncalibrated approximation, not a provider token count.
        """
        if not text:
            return 0

        # Split on whitespace and punctuation
        tokens = re.findall(r"\w+|[^\w\s]", text)

        # Code typically has shorter tokens due to symbols
        code_chars = sum(1 for c in text if c in "{}();=<>[]!&|^~")
        code_ratio = code_chars / max(len(text), 1)

        # Adjust: more code chars = more aggressive splitting
        adjustment = 0.7 + (code_ratio * 0.3)

        return int(len(tokens) * adjustment)


class GitDiffParser:
    """Parse git diff for accurate change statistics."""

    @staticmethod
    def parse_diff_stats(diff: str) -> Dict[str, int]:
        """
        Parse diff text to get accurate line statistics.

        Returns:
            Dict with added_lines, deleted_lines, total_changed
        """
        if not diff:
            return {"added_lines": 0, "deleted_lines": 0, "total_changed": 0}

        added_lines = 0
        deleted_lines = 0

        old_remaining = new_remaining = 0
        # Git separates lines with LF, not Unicode line/paragraph separators.
        for line in diff.split("\n"):
            if not line:
                continue
            prefix = line[0]
            if prefix == "+":
                if (
                    not line.startswith("+++ ")
                    or old_remaining > 0
                    or new_remaining > 0
                ):
                    added_lines += 1
                    new_remaining -= 1
            elif prefix == "-":
                if (
                    not line.startswith("--- ")
                    or old_remaining > 0
                    or new_remaining > 0
                ):
                    deleted_lines += 1
                    old_remaining -= 1
            elif prefix == " ":
                old_remaining -= 1
                new_remaining -= 1
            elif prefix == "@":
                match = _HUNK.match(line)
                if match:
                    old_remaining = int(match[2] or 1)
                    new_remaining = int(match[4] or 1)
            elif line.startswith("diff --git "):
                old_remaining = new_remaining = 0

        return {
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "total_changed": added_lines + deleted_lines,
        }

    @staticmethod
    def get_file_extensions(diff: str) -> list:
        """Extract file extensions from diff headers."""
        extensions = []
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                filename = line[6:]
                if "." in filename:
                    ext = filename.rsplit(".", 1)[1]
                    extensions.append(f".{ext}")
        return list(set(extensions))


# Singleton instance for convenience
_default_tokenizer = None


def get_tokenizer() -> Tokenizer:
    """Get default tokenizer instance."""
    global _default_tokenizer
    if _default_tokenizer is None:
        _default_tokenizer = Tokenizer()
    return _default_tokenizer


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """Convenience function to count tokens."""
    return get_tokenizer().count_tokens(text, model)
