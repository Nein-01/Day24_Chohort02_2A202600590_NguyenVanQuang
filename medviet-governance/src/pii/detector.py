import re
from typing import Iterable, Iterator, List, Tuple

import spacy
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine


class BlankVietnameseNlpEngine(NlpEngine):
    """Minimal NLP engine so Presidio can run custom recognizers offline."""

    def __init__(self):
        self.nlp = spacy.blank("xx")
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def process_text(self, text: str, language: str) -> NlpArtifacts:
        doc = self.nlp(text)
        return NlpArtifacts(
            entities=[],
            tokens=doc,
            tokens_indices=[token.idx for token in doc],
            lemmas=[token.text.lower() for token in doc],
            nlp_engine=self,
            language=language,
        )

    def process_batch(
        self,
        texts: Iterable[str],
        language: str,
        batch_size: int = 1,
        n_process: int = 1,
        **kwargs,
    ) -> Iterator[Tuple[str, NlpArtifacts]]:
        for text in texts:
            yield text, self.process_text(text, language)

    def is_stopword(self, word: str, language: str) -> bool:
        return False

    def is_punct(self, word: str, language: str) -> bool:
        return bool(re.fullmatch(r"\W+", word or ""))

    def get_supported_entities(self) -> List[str]:
        return []

    def get_supported_languages(self) -> List[str]:
        return ["vi"]


def build_vietnamese_analyzer() -> AnalyzerEngine:
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[Pattern(name="cccd_pattern", regex=r"(?<!\d)\d{11,12}(?!\d)", score=0.9)],
        context=["cccd", "can cuoc", "chung minh", "cmnd"],
        supported_language="vi",
    )

    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[
            Pattern(
                name="vn_phone",
                regex=r"(?<!\d)(?:0(?:3|5|7|8|9)\d{8}|(?:3|5|7|8|9)\d{8})(?!\d)",
                score=0.85,
            )
        ],
        context=["dien thoai", "sdt", "phone", "lien he"],
        supported_language="vi",
    )

    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[
            Pattern(
                name="email",
                regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                score=0.9,
            )
        ],
        context=["email", "mail"],
        supported_language="vi",
    )

    # Covers Faker vi_VN names well enough for the lab's detection-rate target.
    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        patterns=[
            Pattern(
                name="vn_person_name",
                regex=r"\b(?:[A-Z][A-Za-zÀ-ỹà-ỹ']+\s+){1,5}[A-Z][A-Za-zÀ-ỹà-ỹ']+\b",
                score=0.75,
            )
        ],
        context=["benh nhan", "bac si", "ho ten"],
        supported_language="vi",
    )

    nlp_engine = BlankVietnameseNlpEngine()
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["vi"],
    )
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)
    analyzer.registry.add_recognizer(person_recognizer)
    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    return analyzer.analyze(
        text=str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
