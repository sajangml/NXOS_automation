# semantic_diff/normalize.py

import re
from typing import List

# ---------------------------------------------------------
# Regex: Remove ANSI escape sequences
# ---------------------------------------------------------
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

# ---------------------------------------------------------
# Sensitive tokens that should be normalized (not removed)
# ---------------------------------------------------------
# Example:
#   radius-server host 10.1.1.1 key 6 "abc..." authentication accounting
# -> radius-server host 10.1.1.1 key 6 <redacted> authentication accounting
SECRET_TOKEN_RE = re.compile(r"(\bkey(?:\s+\d+)?\s+)(\"[^\"]*\"|\S+)")
SNMP_AUTH_SECRET_RE = re.compile(r"(\bauth\s+\S+\s+)(\"[^\"]*\"|\S+)")
SNMP_PRIV_SECRET_RE = re.compile(r"(\bpriv\s+\S+\s+)(\"[^\"]*\"|\S+)")

# ---------------------------------------------------------
# Lines that are noise / metadata and must be removed
# ---------------------------------------------------------
NOISE_PREFIXES = (
    "!Command: ",
    "!Time: ",
    "!Running configuration last done at",
    "!Last configuration change at",
    "!No configuration change since",
    "Building configuration...",
    "Current configuration :",
)

# ---------------------------------------------------------
# Lines that should always be ignored for security reasons
# ---------------------------------------------------------
IGNORE_PATTERNS = [
    r"^crypto key generate",
    r"^key-string ",
    r"^snmp-server user .* localizedkey",
    r"^username .* password",
    r"^username .* secret",
    r"^feature ssh",   # optional — tune depending on your requirements
]
IGNORE_REGEXES = tuple(re.compile(pattern) for pattern in IGNORE_PATTERNS)


# ---------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------
def _strip_ansi(line: str) -> str:
    """Remove ANSI terminal color codes."""
    return ANSI_ESCAPE_RE.sub("", line)


def _is_noise_line(line: str) -> bool:
    """Return True for timestamps, banners, or metadata NX-OS emits."""
    if not line.strip():
        return True

    for p in NOISE_PREFIXES:
        if line.startswith(p):
            return True

    return False


def _matches_ignore_patterns(line: str) -> bool:
    """Return True if line contains secrets/keys/etc."""
    for pattern in IGNORE_REGEXES:
        if pattern.search(line):
            return True
    return False


def _redact_sensitive_tokens(line: str) -> str:
    """
    Redact inline key/password token values so semantic diffs ignore only the secret value.
    """
    if line.startswith("radius-server ") or line.startswith("tacacs-server "):
        return SECRET_TOKEN_RE.sub(r"\1<redacted>", line)
    if line.startswith("snmp-server user "):
        line = SNMP_AUTH_SECRET_RE.sub(r"\1<redacted>", line)
        line = SNMP_PRIV_SECRET_RE.sub(r"\1<redacted>", line)
        return line
    return line


# ---------------------------------------------------------
# MAIN NORMALIZER — this cleans NX-OS raw config
# ---------------------------------------------------------
def normalize_config_text(raw: str) -> List[str]:
    """
    Primary normaliser used internally.

    - Remove ANSI escape sequences
    - Remove NX-OS metadata banners
    - Remove secret/crypto lines
    - Remove empty/comment-only lines
    - Strip trailing whitespace
    """
    lines = raw.splitlines()
    cleaned: List[str] = []
    append = cleaned.append

    for line in lines:
        # Remove ANSI codes
        line = _strip_ansi(line)
        line = line.rstrip()
        line = _redact_sensitive_tokens(line)
        stripped = line.strip()

        # Remove '!' metadata lines except ones we want to keep
        if line.startswith("!"):
            if _is_noise_line(line):
                continue
            if stripped == "!":
                continue
            # Other '!' lines fall through (rare)

        # Remove obvious noise
        if _is_noise_line(line):
            continue

        # Remove lines containing secrets/keys
        if _matches_ignore_patterns(stripped):
            continue

        # Remove empty lines
        if not stripped:
            continue

        append(line)

    return cleaned


# ---------------------------------------------------------
# REQUIRED BY ENGINE — wrapper ensuring API compatibility
# ---------------------------------------------------------
def normalize_config(raw: str) -> List[str]:
    """
    Wrapper used by engine.py.
    Ensures backward compatibility and correct import target.
    """
    return normalize_config_text(raw)
