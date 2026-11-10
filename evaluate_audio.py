"""Record the reproducible single-file audio demo result."""

import json
from pathlib import Path

from kb import load_kb, map_text, rank, transcribe


ROOT = Path(__file__).parent
AUDIO = ROOT / "samples" / "influenza_demo.mp3"
EXPECTED = "I have a runny nose, chills, and a sore throat."


def main():
    evidences, conditions = load_kb()
    transcript = transcribe(AUDIO)
    matched, ignored = map_text(transcript, evidences)
    codes = sorted({code for _, code, _ in matched})
    results = rank(conditions, codes) if len(codes) >= 2 else []
    ties = sum(abs(score - results[0][0]) < 1e-9 for score, _, _ in results) if results else 0
    report = {
        "file": str(AUDIO.relative_to(ROOT)),
        "audio_type": "synthetic English speech; one demo clip",
        "expected_transcript": EXPECTED,
        "transcript": transcript,
        "transcript_exact_match": transcript == EXPECTED,
        "mapped_codes": codes,
        "ignored_clauses": ignored,
        "disease_candidates": len(results),
        "top_score_ties": ties,
        "top_disease": results[0][1] if results else None,
        "top_score": results[0][0] if results else None,
        "top_evidence_codes": sorted(results[0][2]) if results else [],
    }
    output = ROOT / "artifacts" / "audio_demo.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
