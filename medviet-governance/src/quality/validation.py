import re

import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite


VALID_CONDITIONS = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def build_patient_expectation_suite() -> ExpectationSuite:
    context = gx.get_context()
    suite_name = "patient_data_suite"

    try:
        suite = context.add_expectation_suite(suite_name)
    except Exception:
        suite = context.get_expectation_suite(suite_name)

    df = pd.read_csv("data/raw/patients_raw.csv")

    try:
        validator = context.sources.pandas_default.read_dataframe(df)
        validator.expect_column_values_to_not_be_null("patient_id")
        validator.expect_column_value_lengths_to_equal(column="cccd", value=12)
        validator.expect_column_values_to_be_between(
            column="ket_qua_xet_nghiem",
            min_value=0,
            max_value=50,
        )
        validator.expect_column_values_to_be_in_set(column="benh", value_set=VALID_CONDITIONS)
        validator.expect_column_values_to_match_regex(column="email", regex=EMAIL_REGEX)
        validator.expect_column_values_to_be_unique(column="patient_id")
        validator.save_expectation_suite()
    except Exception as exc:
        # GX APIs vary across versions; keep validation helpers usable.
        suite.meta["build_warning"] = str(exc)

    return suite


def validate_anonymized_data(filepath: str) -> dict:
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns),
        },
    }

    def fail(message: str) -> None:
        results["success"] = False
        results["failed_checks"].append(message)

    if "cccd" in df.columns and df["cccd"].astype(str).str.fullmatch(r"\d{12}").any():
        fail("cccd still contains raw 12-digit values")

    required_columns = ["patient_id", "cccd", "so_dien_thoai", "email", "benh", "ket_qua_xet_nghiem"]
    present_required = [col for col in required_columns if col in df.columns]
    null_counts = df[present_required].isnull().sum()
    for col, count in null_counts.items():
        if count:
            fail(f"{col} contains {int(count)} null values")

    try:
        original_rows = len(pd.read_csv("data/raw/patients_raw.csv"))
        if len(df) != original_rows:
            fail(f"row count mismatch: anonymized={len(df)} original={original_rows}")
    except FileNotFoundError:
        results["stats"]["original_rows_check"] = "skipped: raw file missing"

    if "email" in df.columns:
        invalid_emails = ~df["email"].astype(str).apply(lambda value: bool(re.fullmatch(EMAIL_REGEX, value)))
        if invalid_emails.any():
            fail(f"email contains {int(invalid_emails.sum())} invalid values")

    return results
