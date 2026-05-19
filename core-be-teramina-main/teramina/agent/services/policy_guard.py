"""
Safety/Policy Guard for agent responses.

Provides risk grading and veto logic for high-risk advice without needing
a separate LLM call — deterministic pattern matching enforced post-generation.
"""

import re

# Keywords that indicate high-risk chemical/biological intervention
_HIGH_RISK_PATTERNS = [
    r"\bchlorin\w*\b",
    r"\bformalin\b",
    r"\bcopper sulfate\b",
    r"\bkupri\b",
    r"\bantibiotik\b",
    r"\bantibiotic\b",
    r"\bvaccin\w*\b",
    r"\bpestisid\w*\b",
    r"\bpesticide\b",
    r"\bmalachite green\b",
    r"\bhydrogen peroxide\b",
    r"\bkapur\b",  # lime application
    r"\bdolomite\b",
    r"\bsaponin\b",
    r"\bprobiotik dosis\b",
]

_MEDIUM_RISK_PATTERNS = [
    r"\btambah aerasi\b",
    r"\bincrease aeration\b",
    r"\bkurangi pakan\b",
    r"\breduce feed\b",
    r"\bganti air\b",
    r"\bwater change\b",
    r"\bpartial harvest\b",
    r"\bpanen sebagian\b",
]

_HIGH_RISK_DISCLAIMER_EN = (
    "\n\n⚠️ **High-risk recommendation.** Consult your aquaculture extension officer "
    "before applying any chemical or biological treatment. Incorrect dosing can cause "
    "mass mortality. Confidence rating applies to the diagnosis, not the treatment dose."
)
_HIGH_RISK_DISCLAIMER_ID = (
    "\n\n⚠️ **Rekomendasi berisiko tinggi.** Konsultasikan dengan penyuluh perikanan "
    "sebelum menerapkan perlakuan kimia atau biologis. Dosis yang salah dapat menyebabkan "
    "kematian massal. Tingkat kepercayaan berlaku untuk diagnosis, bukan dosis perlakuan."
)

_DISCLAIMER_ALREADY_PRESENT = ["extension officer", "penyuluh", "⚠️ **High-risk"]


def grade_risk(response_text: str) -> str:
    """Return 'high', 'medium', or 'low' based on response content."""
    lower = response_text.lower()
    if any(re.search(p, lower) for p in _HIGH_RISK_PATTERNS):
        return "high"
    if any(re.search(p, lower) for p in _MEDIUM_RISK_PATTERNS):
        return "medium"
    return "low"


def apply_policy(response_text: str) -> str:
    """
    Enforce safety policy on a generated response.
    - Appends high-risk disclaimer if needed.
    - Does not truncate or block — adds guardrails inline.
    """
    risk = grade_risk(response_text)
    if risk != "high":
        return response_text

    already_warned = any(marker in response_text for marker in _DISCLAIMER_ALREADY_PRESENT)
    if already_warned:
        return response_text

    id_indicators = ["tambak", "udang", "pakan", "kolam", "siklus", "petani", "panen"]
    lower = response_text.lower()
    if any(w in lower for w in id_indicators):
        return response_text + _HIGH_RISK_DISCLAIMER_ID
    return response_text + _HIGH_RISK_DISCLAIMER_EN


def veto_hallucinated_certainty(response_text: str) -> str:
    """
    Detect and soften absolute certainty claims about chemical doses or disease diagnoses
    that the system cannot actually verify. Replaces "will cure", "guaranteed", "pasti"
    with hedged language.
    """
    replacements = [
        (r"\bwill definitely cure\b", "may help address"),
        (r"\bguaranteed to\b", "likely to"),
        (r"\bpasti sembuh\b", "kemungkinan membantu"),
        (r"\bpasti berhasil\b", "kemungkinan berhasil"),
        (r"\b100% effective\b", "potentially effective"),
    ]
    for pattern, replacement in replacements:
        response_text = re.sub(pattern, replacement, response_text, flags=re.IGNORECASE)
    return response_text


def enforce_all(response_text: str) -> str:
    """Apply the full policy guard pipeline."""
    text = veto_hallucinated_certainty(response_text)
    text = apply_policy(text)
    return text
