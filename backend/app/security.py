import re
from typing import List

DOMAIN_TERMS = [
    r"\b(vehicle|engine|motor|battery|coolant|rpm|speed|torque|sensor|telemetry|ecu|obd|abs|tpms|fuel|oil|voltage|temperature|thermostat|misfire|knock|dtc|can bus|canbus|brake|throttle|ignition)\b",
    r"\b(iot|device|firmware|uptime|latency|packet|telemetry|heartbeat|diagnostic|alert|fault|error code|status)\b",
]

BLOCK_TERMS = [
    r"\b(password|api_key|secret|private key|credit card|ssn)\b",
]

SAFE_REPLACEMENTS = [
    (re.compile(r"\b(sk-)[a-zA-Z0-9-_]{20,}\b"), "[REDACTED_TOKEN]"),
]


def sanitize_text(text: str, max_len: int = 20000) -> str:
    """Basic content sanitization/guardrail.
    - strip control chars
    - redact obvious secrets
    - clamp length
    """
    text = text.replace("\x00", "")
    for patt, repl in SAFE_REPLACEMENTS:
        text = patt.sub(repl, text)
    # remove very long lines to limit prompt injections
    lines = []
    for line in text.splitlines():
        if len(line) > 5000:
            lines.append(line[:5000] + " …")
        else:
            lines.append(line)
    text = "\n".join(lines)
    return text[:max_len]


def is_in_domain(text: str) -> bool:
    lower = text.lower()
    has = any(re.search(p, lower) for p in DOMAIN_TERMS)
    bad = any(re.search(p, lower) for p in BLOCK_TERMS)
    return has and not bad


def guardrail_refusal(message: str) -> str:
    return (
        "Request appears out of scope for vehicle IoT diagnostics. "
        "Please provide motor vehicle IoT logs or ask about device status."
    )
