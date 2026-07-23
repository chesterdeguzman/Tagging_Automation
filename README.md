# Media Tagging Automation

A GitHub-ready Python project for automated **relevancy** and **sentiment** tagging of multilingual media-monitoring data.

This repository was organized from the provided tagging notebooks and the dummy dataset `HK - MSM.xlsx`. The production workflow is now reusable from the command line instead of being tied to one notebook or filename.

## What it does

- Reads Excel or CSV media-monitoring datasets.
- Uses existing `Translated Headline` and `Translated Opening` columns when available.
- Generates or refreshes `Hit Sentence`.
- Tags each row as `Relevant` or `Not Relevant`.
- Uses normalized `Input Name` plus the `Keywords` field for brand matching.
- Supports exact and configurable fuzzy matching.
- Re-tags sentiment into `Positive`, `Neutral`, or `Negative` using editable YAML rules.
- Adds `Tagging Reason` and `Relevancy Score` for auditability.
- Exports a tagged Excel or CSV file.

## Repository structure

```text
media-tagging-automation/
├── config/tagging_rules.yml
├── data/sample/HK_MSM_dummy.xlsx
├── notebooks/
│   ├── Tagging_Automation_Translation.ipynb
│   ├── Tagging_Automation_Translation_v2.ipynb
│   └── tagging_notebook.ipynb
├── outputs/
├── src/tagging_automation/
│   ├── __init__.py
│   ├── cli.py
│   └── core.py
├── tests/test_core.py
├── pyproject.toml
├── requirements.txt
└── run.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -e .
```

## Run on the included dummy dataset

```bash
media-tagger \
  --input "data/sample/HK_MSM_dummy.xlsx" \
  --sheet "HK - MSM" \
  --output "outputs/HK_MSM_tagged.xlsx"
```

You can also run it without installing the CLI entry point:

```bash
PYTHONPATH=src python run.py \
  --input "data/sample/HK_MSM_dummy.xlsx" \
  --sheet "HK - MSM" \
  --output "outputs/HK_MSM_tagged.xlsx"
```

## Expected input columns

Required:

- `Input Name`
- `Headline`
- `Opening Text`
- `Sentiment`

Optional but recommended:

- `Keywords`
- `Translated Headline`
- `Translated Opening`
- `Original Sentiment`

## Output fields

The original fields are retained. The automation adds or refreshes:

- `Relevancy`
- `Original Sentiment`
- `New_Sentiment`
- `Tagging Reason`
- `Relevancy Score`
- `Hit Sentence`

## Edit the rules

All keyword lists and the fuzzy threshold are stored in `config/tagging_rules.yml`. This keeps business logic outside the Python code and makes review easier.

Important rule order:

1. Preserve original Positive sentiment when configured.
2. Mixed positive and negative signals become Neutral.
3. Stock-price movement phrases become Neutral.
4. Positive keyword match becomes Positive.
5. Negative keyword match becomes Negative.
6. Otherwise, default to Neutral.

## Translation behavior

The dummy HK dataset already includes translated headline and opening fields, so the core workflow does not require an online translation service. The original translation notebooks are retained in `notebooks/` for reference. Google Cloud credentials must never be committed to GitHub.

## Tests

```bash
PYTHONPATH=src pytest -q
```

## Data note

The included spreadsheet is identified as a dummy dataset by the repository owner. Remove it before publishing if it contains any confidential, licensed, or personal data.
