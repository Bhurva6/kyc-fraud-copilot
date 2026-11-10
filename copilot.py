"""Offline prototype. See README.md for scope and limitations."""
from checks import verdict

def analyst_note(flags, applicant=""):
    lines = [f"Sample consistency review: {verdict(flags)}", "SYNTHETIC FIXTURES ONLY. Not an identity or fraud verdict."]
    for f in flags:
        lines.append(f"- [{f.severity.upper()}] {f.code}: {f.reason} (evidence: {f.evidence})")
    if not flags:
        lines.append("No implemented checks fired. This does not establish document authenticity.")
    lines.append("Human review required. No approval, rejection, registry lookup or identity verification performed.")
    return "\n".join(lines)
