import hashlib

import pandas as pd
from faker import Faker
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def fake_cccd() -> str:
    return "".join(fake.random_choices(elements="0123456789", length=12))


def fake_phone() -> str:
    return f"0{fake.random_element(elements=('3', '5', '7', '8', '9'))}{fake.msisdn()[:8]}"


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        text = str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "DEFAULT": OperatorConfig(
                    "mask",
                    {
                        "masking_char": "*",
                        "chars_to_mask": 8,
                        "from_end": False,
                    },
                )
            }
        elif strategy == "hash":
            operators = {"DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})}
        else:
            raise ValueError(f"Unsupported anonymization strategy: {strategy}")

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_anon = df.copy()

        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = [fake.name() for _ in range(len(df_anon))]
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = [fake.address().replace("\n", ", ") for _ in range(len(df_anon))]
        if "email" in df_anon.columns:
            df_anon["email"] = [fake.email() for _ in range(len(df_anon))]
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [f"CCCD_MASKED_{hashlib.sha256(str(v).encode()).hexdigest()[:12]}" for v in df["cccd"]]
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [fake_phone() for _ in range(len(df_anon))]
        if "ngay_sinh" in df_anon.columns:
            df_anon["nam_sinh"] = pd.to_datetime(
                df_anon["ngay_sinh"],
                format="%d/%m/%Y",
                errors="coerce",
            ).dt.year
            df_anon = df_anon.drop(columns=["ngay_sinh"])

        return df_anon

    def calculate_detection_rate(self, original_df: pd.DataFrame, pii_columns: list) -> float:
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if results:
                    detected += 1

        return detected / total if total > 0 else 0.0
