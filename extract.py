"""Offline prototype. See README.md for scope and limitations."""
import re
from dataclasses import dataclass, field
from validators import PAN_RE, AADHAAR_RE, IFSC_RE, DOB_RE


@dataclass
class KycDocument:
    doc_type: str               # pan | aadhaar | bank_statement
    raw_text: str
    name: str = ""
    dob: str = ""
    pan: str = ""
    aadhaar: str = ""
    address: str = ""
    ifsc: str = ""
    account: str = ""
    extra: dict = field(default_factory=dict)


def _grab(pattern, text, group=1):
    m = pattern.search(text)
    return m.group(group) if m else ""


def _grab_line(label, text):
    m = re.search(label + r"\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_document(doc_type: str, raw_text: str) -> KycDocument:
    d = KycDocument(doc_type=doc_type, raw_text=raw_text)
    d.name = _grab_line(r"(?:name|naam)", raw_text)
    d.dob = _grab(DOB_RE, raw_text)
    d.address = _grab_line(r"address", raw_text)
    # label-first extraction so malformed numbers are flagged by the
    # validators instead of silently never being extracted
    if doc_type == "pan":
        d.pan = _grab_line(r"pan", raw_text).upper() or _grab(PAN_RE, raw_text)
    elif doc_type == "aadhaar":
        d.aadhaar = (_grab_line(r"aadhaar\s*no", raw_text)
                     or _grab(AADHAAR_RE, raw_text))
    elif doc_type == "bank_statement":
        d.ifsc = _grab_line(r"ifsc", raw_text).upper() or _grab(IFSC_RE, raw_text)
        d.account = _grab_line(r"account\s*(?:no|number)", raw_text)
    return d
