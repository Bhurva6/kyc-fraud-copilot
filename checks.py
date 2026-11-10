"""Offline prototype. See README.md for scope and limitations."""
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import datetime
from extract import KycDocument
from validators import check_pan, check_aadhaar, check_ifsc, HOLDER_TYPES

STOPWORDS = {"kumar", "singh", "sharma", "devi", "kumari", "lal", "chand"}


@dataclass
class Flag:
    code: str
    severity: str          # high | medium | low
    reason: str
    evidence: str


def _norm_name(n: str) -> list[str]:
    parts = re.sub(r"[^a-z ]", "", n.lower()).split()
    return [p for p in parts if p not in STOPWORDS] or parts


def _name_sim(a: str, b: str) -> float:
    """Same surname must not clear a different given name (family fraud
    rings share surnames), so the given name carries most of the weight."""
    ta, tb = _norm_name(a), _norm_name(b)
    if not ta or not tb:
        return 0.0
    given = SequenceMatcher(None, ta[0], tb[0]).ratio()
    sa, sb = set(ta), set(tb)
    rest_a, rest_b = " ".join(sorted(sa - {ta[0]})), " ".join(sorted(sb - {tb[0]}))
    rest = 1.0 if rest_a == rest_b else SequenceMatcher(None, rest_a, rest_b).ratio()
    exact = len(sa & sb) / max(len(sa), len(sb))
    score = max(exact, 0.65 * given + 0.35 * rest)
    if given < 0.7:  # different given name: a shared surname cannot clear it
        score = min(score, 0.55)
    return score


def run_checks(docs: list[KycDocument]) -> list[Flag]:
    flags: list[Flag] = []
    by_type = {d.doc_type: d for d in docs}

    for kind in ("pan", "aadhaar", "bank_statement"):
        if kind not in by_type:
            flags.append(Flag("MISSING_DOCUMENT", "medium", "required sample document missing", kind))
    for d in docs:
        for key in {"pan": ("name", "dob", "pan"), "aadhaar": ("name", "dob", "aadhaar"), "bank_statement": ("name", "ifsc", "account")}.get(d.doc_type, ()):
            if not getattr(d, key):
                flags.append(Flag("MISSING_FIELD", "medium", "required field not extracted", f"{d.doc_type}: {key}"))
        if d.pan:
            for p in check_pan(d.pan):
                flags.append(Flag("PAN_FORMAT", "high", p, f"{d.doc_type}: {d.pan}"))
        if d.aadhaar:
            for p in check_aadhaar(d.aadhaar):
                flags.append(Flag("AADHAAR_CHECKSUM", "high", p, f"{d.doc_type}: {d.aadhaar}"))
        if d.ifsc:
            for p in check_ifsc(d.ifsc):
                flags.append(Flag("IFSC_FORMAT", "medium", p, f"{d.doc_type}: {d.ifsc}"))
        if d.dob:
            try:
                datetime.strptime(d.dob.replace("-", "/"), "%d/%m/%Y")
            except ValueError:
                flags.append(Flag("DOB_INVALID", "medium", "date cannot be parsed", d.doc_type))

    pan_doc, aad_doc, bank = by_type.get("pan"), by_type.get("aadhaar"), by_type.get("bank_statement")

    if pan_doc and aad_doc:
        sim = _name_sim(pan_doc.name, aad_doc.name)
        if sim < 0.6:
            flags.append(Flag("NAME_MISMATCH", "high",
                              "applicant name differs across PAN and Aadhaar",
                              f"PAN '{pan_doc.name}' vs Aadhaar '{aad_doc.name}' (similarity {sim:.2f})"))
        if pan_doc.dob and aad_doc.dob and pan_doc.dob != aad_doc.dob:
            flags.append(Flag("DOB_MISMATCH", "high",
                              "date of birth differs across PAN and Aadhaar",
                              f"PAN {pan_doc.dob} vs Aadhaar {aad_doc.dob}"))

    if bank and (pan_doc or aad_doc):
        ref = pan_doc or aad_doc
        sim = _name_sim(bank.name, ref.name)
        if sim < 0.6:
            flags.append(Flag("BANK_NAME_MISMATCH", "high",
                              "bank account holder does not match the applicant",
                              f"statement '{bank.name}' vs {ref.doc_type} '{ref.name}' ({sim:.2f})"))
        if ref.pan and ref.pan[3] in HOLDER_TYPES and HOLDER_TYPES[ref.pan[3]] != "individual":
            flags.append(Flag("HOLDER_TYPE", "medium",
                              "PAN holder type is not an individual",
                              f"4th character '{ref.pan[3]}' = {HOLDER_TYPES[ref.pan[3]]}"))

    if pan_doc and aad_doc and pan_doc.address and aad_doc.address:
        a = set(re.sub(r"[^a-z0-9 ]", "", pan_doc.address.lower()).split())
        b = set(re.sub(r"[^a-z0-9 ]", "", aad_doc.address.lower()).split())
        overlap = len(a & b) / max(len(a), 1)
        if overlap < 0.25:
            flags.append(Flag("ADDRESS_LOW_OVERLAP", "low",
                              "addresses share few tokens; confirm current residence",
                              f"token overlap {overlap:.2f}"))

    return flags


def verdict(flags: list[Flag]) -> str:
    # No approval, rejection or identity authentication is possible from these checks.
    return "REVIEW_FLAGS" if flags else "NO_FLAGS_NOT_VERIFIED"
