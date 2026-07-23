import pandas as pd
from tagging_automation.core import load_config, tag_dataframe


def test_tagging_rules():
    config = load_config("config/tagging_rules.yml")
    source = pd.DataFrame([
        {"Input Name": "Acme Bank [HK] (MSM) - V3", "Keywords": "Acme Bank", "Headline": "Acme Bank appoints a new CEO", "Opening Text": "The appointment supports growth.", "Sentiment": "Neutral"},
        {"Input Name": "Acme Bank [HK] (MSM) - V3", "Keywords": "Acme Bank", "Headline": "Market update", "Opening Text": "A competitor faces a fraud investigation.", "Sentiment": "Neutral"},
    ])
    result = tag_dataframe(source, config)
    assert result.loc[0, "Relevancy"] == "Relevant"
    assert result.loc[0, "New_Sentiment"] == "Positive"
    assert result.loc[1, "Relevancy"] == "Not Relevant"
    assert result.loc[1, "New_Sentiment"] == "Negative"
