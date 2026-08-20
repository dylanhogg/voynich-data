"""
Centralized text processing for VCAT.

This module is the SINGLE SOURCE OF TRUTH for text cleaning and stripping.
Both the builder (builders/build_eva_lines.py) and the verifier
(validators/verify_invariants.py) MUST import from here.

CRITICAL: Do not duplicate this logic elsewhere. If you need to strip
markup or clean text, import these functions. This ensures the builder
and verifier always apply identical rules, preventing subtle bugs where
they diverge over time.
"""

import re


def strip_ivtff_markup(text: str, alternative: int = 0) -> str:
    """
    Strip IVTFF markup from text, preserving uncertainty markers.

    This produces the "flag basis" - the text used to compute
    has_uncertain and has_illegible flags.

    Removes:
    - Curly brace comments: {like this}
    - Alternative brackets: [a:b] -> a (keeps the chosen option)
    - All angle-bracket tags: <...>

    Preserves:
    - Uncertainty markers: ?, !, *
    - High-ASCII tokens: @NNN;
    - EVA characters

    Args:
        text: Raw IVTFF transcription text
        alternative: Which option of ``[a:b]`` to keep. 0 (default) keeps the
            first, as every built dataset does; 1 keeps the second. Used by the
            Phase 1 uncertainty-sensitivity analysis to measure how much the
            first-option convention decides. Values beyond the available
            options fall back to the last one.

    Returns:
        Text with markup stripped but uncertainty markers intact
    """
    result = text

    # Remove curly brace comments
    result = re.sub(r"\{[^}]*\}", "", result)

    # Handle alternatives [a:b] - keep the requested option
    # Uses * not + to handle empty alternatives like [:ch] or [a:]
    result = re.sub(
        r"\[([^:\]]*):([^\]]*)\]",
        lambda m: m.group(min(alternative + 1, m.re.groups)),
        result,
    )

    # Remove all angle-bracket tags (catches <->, <$>, <%>, <~>, <!...>, etc.)
    result = re.sub(r"<[^>]*>", "", result)

    # Normalize whitespace
    result = re.sub(r"\s+", " ", result).strip()

    return result


def clean_text_for_analysis(text: str, alternative: int = 0) -> str:
    """
    Produce analysis-ready text (text_clean).

    This is the final cleaned text for computational analysis.
    It has all markup AND uncertainty markers removed.

    Args:
        text: Raw IVTFF transcription text
        alternative: Which option of ``[a:b]`` to keep (see
            :func:`strip_ivtff_markup`). The datasets are built with 0.

    Returns:
        Clean text suitable for analysis (no markup, no uncertainty markers)
    """
    # First strip markup
    result = strip_ivtff_markup(text, alternative)

    # Then remove uncertainty markers (they're preserved in flags)
    result = re.sub(r"[?!*]", "", result)

    # Handle known transcription errors:
    # - Uppercase 'I' appears once (f48r.13) - lowercase it
    result = result.replace("I", "i")

    # Final whitespace normalization
    result = re.sub(r"\s+", " ", result).strip()

    return result


def inline_tags(text: str) -> list[str]:
    """
    Return the angle-bracket tags of a raw IVTFF line, in order.

    The cleaners above delete these; some carry layout information that the
    cleaned text cannot express (``<%>`` paragraph start, ``<$>`` paragraph
    end, ``<->`` plain line end). Reading them goes through here so no caller
    grows its own copy of the tag regex.

    Args:
        text: Raw IVTFF transcription text

    Returns:
        The tags found, including their angle brackets
    """
    return re.findall(r"<[^>]*>", text)


def compute_flags(text: str) -> tuple[bool, bool, bool]:
    """
    Compute quality flags from raw text.

    Flags are computed from the "flag basis" (markup stripped, markers present)
    BEFORE uncertainty markers are removed.

    Args:
        text: Raw IVTFF transcription text

    Returns:
        Tuple of (has_uncertain, has_illegible, has_alternatives)
    """
    # Get flag basis (markup stripped, uncertainty markers present)
    flag_basis = strip_ivtff_markup(text)

    has_uncertain = "?" in flag_basis
    has_illegible = "!" in flag_basis or "*" in flag_basis
    has_alternatives = "[" in text and ":" in text

    return (has_uncertain, has_illegible, has_alternatives)


def validate_stripped_text(text: str) -> bool:
    """
    Sanity check that stripped text contains no markup.

    Use this as a defensive check after stripping.

    Args:
        text: Text that should have been stripped

    Returns:
        True if text contains no markup characters
    """
    forbidden = set("<>{}")
    return not bool(set(text) & forbidden)
