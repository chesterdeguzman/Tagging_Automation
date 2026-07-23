# Tagging workflow

1. Load and normalize column names.
2. Prefer translated content when already present.
3. Extract the first hit sentence from headline and opening text.
4. Normalize the monitored brand name by removing market/version suffixes.
5. Build relevancy search terms from the normalized brand and `Keywords`.
6. Apply exact matching, then fuzzy matching.
7. Apply sentiment rules in a deterministic priority order.
8. Write audit reasons and relevancy scores.
9. Export the tagged result.
