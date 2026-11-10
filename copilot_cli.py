"""Offline prototype. See README.md for scope and limitations."""
import json, os, sys
from extract import parse_document
from checks import run_checks, verdict
from copilot import analyst_note

TYPES = {"pan": "pan", "aadhaar": "aadhaar", "bank_statement": "bank_statement"}


def main(folder: str):
    docs = []
    for fn in sorted(os.listdir(folder)):
        stem = os.path.splitext(fn)[0]
        if stem in TYPES:
            with open(os.path.join(folder, fn), encoding="utf-8") as f:
                docs.append(parse_document(TYPES[stem], f.read()))
    if not docs:
        sys.exit("no recognised documents (pan.txt, aadhaar.txt, bank_statement.txt)")
    flags = run_checks(docs)
    applicant = docs[0].name
    print(analyst_note(flags, applicant))
    print("\n--- machine report ---")
    print(json.dumps({
        "verdict": verdict(flags),
        "flags": [f.__dict__ for f in flags],
        "documents": [{"type": d.doc_type, "name": d.name,
                       "pan": d.pan, "aadhaar": d.aadhaar, "ifsc": d.ifsc} for d in docs],
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "samples/clean")
