# KYC document-consistency prototype

An offline rules-based reviewer of **text exports**, not document images.
It extracts labelled sample fields, runs identifier-format and Verhoeff
checksum checks, compares names and dates, and prints evidence-linked flags.
The analyst note is a deterministic template. **No OCR, vision model, LLM,
registry lookup or identity verification is connected.**

## Run

Python 3.10+, standard library only:

```sh
python3 sample_fixtures.py  # create synthetic local text fixtures
python3 copilot_cli.py samples/clean
python3 copilot_cli.py samples/fraud_ring
python3 -m unittest discover -s . -v
```

11 unit tests cover the examples, malformed/missing fields, invalid dates,
checksum failures and cross-document differences. All fixtures are invented.
Identifiers may resemble valid formats by design; they are not known-valid
or assigned identities. Do not use these fixtures as identity documents.

## Interpretation

- `NO_FLAGS_NOT_VERIFIED`: implemented checks found no inconsistency.
  This does **not** establish authenticity or identity.
- `REVIEW_FLAGS`: missing evidence or inconsistencies need human review.
  A flag may be an OCR/transcription error, an outdated address or a name
  variation. It is not a fraud finding and must not reject an applicant.

Names are compared with a simple heuristic that can mishandle initials,
reordered names, transliteration and legitimate variations. No precision or
recall claim is made. A checksum proves mathematical consistency, not that
an Aadhaar exists or belongs to anyone. Raw fields appear in local evidence;
use only synthetic examples until redaction, consent, retention and access
controls are implemented. No real KYC files should be uploaded here.

Next: evaluated OCR extraction, source spans, redacted evidence, tests on
legitimate variations, calibrated review thresholds and an approved human
workflow. No models trained or fine-tuned.
