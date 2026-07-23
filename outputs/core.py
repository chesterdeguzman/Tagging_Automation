from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml
from rapidfuzz import fuzz


@dataclass(frozen=True)
class TaggingConfig:
    fuzzy_threshold: int
    use_keywords_column: bool
    brand_suffix_patterns: tuple[str, ...]
    preserve_original_positive: bool
    positive_keywords: tuple[str, ...]
    stock_neutral_keywords: tuple[str, ...]
    negative_keywords: tuple[str, ...]


def load_config(path: str | Path) -> TaggingConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    rel = raw["relevancy"]
    sent = raw["sentiment"]
    return TaggingConfig(
        fuzzy_threshold=int(rel.get("fuzzy_threshold", 88)),
        use_keywords_column=bool(rel.get("use_keywords_column", True)),
        brand_suffix_patterns=tuple(rel.get("brand_suffix_patterns", [])),
        preserve_original_positive=bool(sent.get("preserve_original_positive", True)),
        positive_keywords=tuple(map(str.lower, sent.get("positive_keywords", []))),
        stock_neutral_keywords=tuple(map(str.lower, sent.get("stock_neutral_keywords", []))),
        negative_keywords=tuple(map(str.lower, sent.get("negative_keywords", []))),
    )


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", html.unescape(str(value))).strip()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [re.sub(r"\s+", " ", str(c).strip()).title() for c in out.columns]
    return out


def extract_hit_sentence(headline: Any, opening: Any) -> str:
    text = clean_text(f"{clean_text(headline)} {clean_text(opening)}")
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?。！？])\s+", text, maxsplit=1)
    return parts[0]


def normalize_brand(input_name: Any, patterns: Iterable[str]) -> str:
    brand = clean_text(input_name)
    for pattern in patterns:
        brand = re.sub(pattern, "", brand, flags=re.IGNORECASE)
    return clean_text(brand).lower()


def split_keywords(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    return [x.strip().lower() for x in re.split(r"[,;|]", text) if x.strip()]


def build_search_terms(row: pd.Series, config: TaggingConfig) -> list[str]:
    terms: list[str] = []
    brand = normalize_brand(row.get("Input Name", ""), config.brand_suffix_patterns)
    if brand:
        terms.append(brand)
    if config.use_keywords_column:
        terms.extend(split_keywords(row.get("Keywords", "")))
    # preserve order while removing duplicates and very short noise
    return list(dict.fromkeys(t for t in terms if len(t) >= 2))


def choose_analysis_text(row: pd.Series) -> str:
    # Prefer pretranslated columns when the dataset already has them.
    headline = clean_text(row.get("Translated Headline", "")) or clean_text(row.get("Headline", ""))
    opening = clean_text(row.get("Translated Opening", "")) or clean_text(row.get("Opening Text", ""))
    hit = clean_text(row.get("Hit Sentence", ""))
    return clean_text(f"{headline} {opening} {hit}")


def relevancy_details(row: pd.Series, config: TaggingConfig) -> tuple[str, str, float]:
    text = choose_analysis_text(row).lower()
    if not text:
        return "Not Relevant", "No analyzable text", 0.0

    best_term = ""
    best_score = 0.0
    for term in build_search_terms(row, config):
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, flags=re.IGNORECASE):
            return "Relevant", f"Exact match: {term}", 100.0
        score = float(fuzz.partial_ratio(term, text))
        if score > best_score:
            best_term, best_score = term, score

    if best_score >= config.fuzzy_threshold:
        return "Relevant", f"Fuzzy match: {best_term}", best_score
    return "Not Relevant", "No brand or keyword match", best_score


def has_keyword(text: str, keywords: Iterable[str]) -> str | None:
    low = text.lower()
    for kw in keywords:
        # Use token boundaries so, for example, "profit" does not match "competitor".
        pattern = r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)"
        if re.search(pattern, low):
            return kw
    return None


def sentiment_details(row: pd.Series, config: TaggingConfig) -> tuple[str, str]:
    original = clean_text(row.get("Original Sentiment", "")) or clean_text(row.get("Sentiment", ""))
    text = choose_analysis_text(row)

    if config.preserve_original_positive and original.lower() == "positive":
        return "Positive", "Preserved original Positive"

    positive = has_keyword(text, config.positive_keywords)
    stock = has_keyword(text, config.stock_neutral_keywords)
    negative = has_keyword(text, config.negative_keywords)

    # Mixed evidence is reviewed conservatively.
    if positive and negative:
        return "Neutral", f"Mixed signals: +{positive}; -{negative}"
    if stock:
        return "Neutral", f"Stock movement rule: {stock}"
    if positive:
        return "Positive", f"Positive keyword: {positive}"
    if negative:
        return "Negative", f"Negative keyword: {negative}"
    return "Neutral", "No configured sentiment trigger"


def tag_dataframe(df: pd.DataFrame, config: TaggingConfig) -> pd.DataFrame:
    out = normalize_columns(df)
    required = {"Input Name", "Headline", "Opening Text", "Sentiment"}
    missing = sorted(required - set(out.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    if "Original Sentiment" not in out.columns:
        out.insert(0, "Original Sentiment", out["Sentiment"])

    out["Hit Sentence"] = [extract_hit_sentence(h, o) for h, o in zip(out["Headline"], out["Opening Text"])]
    rel = out.apply(lambda row: relevancy_details(row, config), axis=1)
    sent = out.apply(lambda row: sentiment_details(row, config), axis=1)

    for col in ["Relevancy", "New_Sentiment", "Tagging Reason", "Relevancy Score"]:
        if col in out.columns:
            out.drop(columns=col, inplace=True)

    out.insert(0, "Relevancy", [x[0] for x in rel])
    out.insert(2, "New_Sentiment", [x[0] for x in sent])
    out.insert(3, "Tagging Reason", [f"{r[1]} | {s[1]}" for r, s in zip(rel, sent)])
    out.insert(4, "Relevancy Score", [round(x[2], 1) for x in rel])
    return out
