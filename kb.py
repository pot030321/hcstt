"""Inspect and query DDXPlus disease-symptom relationships."""

import argparse
import re
from collections import Counter
from math import log
from pathlib import Path


def load_kb():
    from kb_store import load

    return load()


def rank(conditions, codes):
    codes = set(codes)
    document_frequency = Counter(
        code for condition in conditions.values() for code in condition["symptoms"]
    )
    unknown = codes - document_frequency.keys()
    if unknown:
        raise SystemExit(f"Codes without disease-symptom links: {sorted(unknown)}")
    weights = {
        code: 1 + log((len(conditions) + 1) / (document_frequency[code] + 1))
        for code in codes
    }
    total = sum(weights.values())
    assert total > 0
    results = []
    for name, condition in conditions.items():
        matched = sorted(codes & condition["symptoms"].keys())
        if matched:
            score = min(1.0, sum(weights[code] for code in matched) / total)
            assert 0 < score <= 1
            results.append((score, name, matched))
    return sorted(results, key=lambda item: (-item[0], -len(item[2]), item[1]))


def transcribe(path):
    import soundfile as sf
    import whisper
    from scipy.signal import resample_poly
    from math import gcd

    info = sf.info(path)
    if not 0 < info.duration <= 60:
        raise ValueError("Audio must be between 0 and 60 seconds long")
    audio, sample_rate = sf.read(path, dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    divisor = gcd(sample_rate, 16000)
    if sample_rate != 16000:
        audio = resample_poly(audio, 16000 // divisor, sample_rate // divisor).astype("float32")
    return whisper.load_model("tiny.en").transcribe(
        audio, language="en", fp16=False, condition_on_previous_text=False
    )["text"].strip()


def map_text(text, evidences):
    from symptom_model import phrases, predict

    # shortcut: 15 English symptom classes and simple negation; expand after collecting real utterances.
    stopwords = set("i my me you your am is are a an the have has had do does did to of in on for with and but it its i'm i've can't been feel feeling felt think might there this that very more less much all over recently experiencing".split())
    anchors = {}
    for row in phrases():
        if row["split"] == "train":
            anchors.setdefault(row["evidence_id"], set()).update(re.findall(r"[a-z']+", row["text"].lower()))
    for code, words in anchors.items():
        words.update(re.findall(r"[a-z']+", evidences[code]["question_en"].lower()))
        words.difference_update(stopwords)

    matched, ignored = [], []
    for clause in re.split(r"\b(?:and|but)\b|[,;.]", text, flags=re.IGNORECASE):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:no|not|without|deny|denies)\b|don't", clause, re.IGNORECASE):
            ignored.append(clause)
            continue
        words = set(re.findall(r"[a-z']+", clause.lower())) - stopwords
        candidate = next(
            ((code, score) for code, score in predict(clause) if score >= 0.4 and words & anchors[code]),
            None,
        )
        if candidate:
            matched.append((clause, *candidate))
        else:
            ignored.append(clause)
    return matched, ignored


def print_ranked(evidences, conditions, codes):
    results = rank(conditions, codes)
    print(f"Showing {min(5, len(results))} of {len(results)} candidates; match score is not a diagnosis probability:")
    if results:
        ties = sum(abs(score - results[0][0]) < 1e-9 for score, _, _ in results)
        if ties > 1:
            print(f"{ties} candidates share the highest score; more symptoms are needed to distinguish them.")
    for score, name, matched in results[:5]:
        print(f"{score:.3f} | {name}")
        for code in matched:
            print(f"  {code}: {evidences[code]['question_en']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("search", help="Find evidence codes by one English keyword").add_argument("keyword")
    commands.add_parser("rank", help="Rank diseases from positive symptom codes").add_argument("codes", nargs="+")
    commands.add_parser("text", help="Map an English symptom sentence and query the knowledge base").add_argument("words", nargs="+")
    commands.add_parser("audio", help="Transcribe an English audio file and query the knowledge base").add_argument("file", type=Path)
    args = parser.parse_args()
    evidences, conditions = load_kb()

    if args.command == "search":
        symptom_codes = {code for condition in conditions.values() for code in condition["symptoms"]}
        matches = [
            (code, evidences[code]["question_en"])
            for code in sorted(symptom_codes)
            if args.keyword.casefold() in evidences[code]["question_en"].casefold()
        ]
        for code, question in matches:
            print(f"{code}: {question}")
        if not matches:
            print("No matching symptom terms.")
    elif args.command == "rank":
        unknown = set(args.codes) - evidences.keys()
        if unknown:
            parser.error(f"Unknown evidence codes: {sorted(unknown)}")
        print_ranked(evidences, conditions, args.codes)
    else:
        try:
            text = transcribe(args.file) if args.command == "audio" else " ".join(args.words)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.error(f"Cannot read audio: {exc}")
        print(f"{'Transcription' if args.command == 'audio' else 'Input'}: {text}")
        try:
            matched, ignored = map_text(text, evidences)
        except FileNotFoundError as exc:
            parser.error(f"Missing model. Run: py -3.11 symptom_model.py ({exc})")
        for clause in ignored:
            print(f"Unmapped or negated: {clause}")
        if not matched:
            print("No supported positive symptoms found; no disease lookup performed.")
            return
        print("Mapped symptoms:")
        for clause, code, score in matched:
            print(f"  {clause} -> {code} ({score:.3f}): {evidences[code]['question_en']}")
        codes = {code for _, code, _ in matched}
        if len(codes) < 2:
            print("Need at least two distinct positive symptoms for disease lookup.")
            return
        print_ranked(evidences, conditions, codes)


if __name__ == "__main__":
    main()
