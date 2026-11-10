"""Offline prototype. See README.md for scope and limitations."""
import re

# Verhoeff tables
_D = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],
      [3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
      [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],
      [9,8,7,6,5,4,3,2,1,0]]
_P = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],
      [8,9,1,6,0,4,3,5,2,7],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
      [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]

def verhoeff_valid(number: str) -> bool:
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0

PAN_RE = re.compile(r"\b([A-Z]{3}[ABCEFGHJLPT][A-Z]\d{4}[A-Z])\b")
AADHAAR_RE = re.compile(r"\b([2-9]\d{3}\s?\d{4}\s?\d{4})\b")
IFSC_RE = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
DOB_RE = re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b")

HOLDER_TYPES = {"P": "individual", "C": "company", "F": "firm", "T": "trust"}

def check_pan(pan: str) -> list[str]:
    problems = []
    if not PAN_RE.fullmatch(pan):
        problems.append("PAN fails format AAAAA9999A with valid holder-type letter")
    return problems

def check_aadhaar(aadhaar: str) -> list[str]:
    digits = aadhaar.replace(" ", "")
    problems = []
    if not digits.isdigit() or len(digits) != 12 or digits[0] in "01":
        problems.append("Aadhaar must be 12 digits starting 2-9")
    elif not verhoeff_valid(digits):
        problems.append("Aadhaar fails Verhoeff checksum (possible transcription error; not evidence of fraud)")
    return problems

def check_ifsc(ifsc: str) -> list[str]:
    return [] if IFSC_RE.fullmatch(ifsc) else ["IFSC fails format (4 letters, 0, 6 alphanumeric)"]
