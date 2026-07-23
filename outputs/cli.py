from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from .core import load_config, tag_dataframe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automate media relevancy and sentiment tagging.")
    parser.add_argument("--input", required=True, help="Input .xlsx, .xls, or .csv file")
    parser.add_argument("--output", default="outputs/tagged_output.xlsx", help="Output .xlsx or .csv file")
    parser.add_argument("--sheet", default=None, help="Excel sheet name; defaults to the first sheet")
    parser.add_argument("--config", default="config/tagging_rules.yml", help="YAML tagging rules")
    return parser.parse_args()


def read_input(path: Path, sheet: str | None) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError("Input must be an Excel or CSV file.")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    config = load_config(args.config)
    tagged = tag_dataframe(read_input(input_path, args.sheet), config)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        tagged.to_csv(output_path, index=False)
    else:
        tagged.to_excel(output_path, index=False)

    print(f"Tagged {len(tagged):,} rows -> {output_path}")
    print("\nRelevancy:\n", tagged["Relevancy"].value_counts(dropna=False).to_string())
    print("\nSentiment:\n", tagged["New_Sentiment"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
