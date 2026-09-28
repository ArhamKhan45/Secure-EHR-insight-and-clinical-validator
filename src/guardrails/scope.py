import re


_UNRELATED_TERMS = re.compile(
    r"\b(?:python|programming|code|weather|joke|capital|president|homework|quantum|story)\b",
    re.IGNORECASE,
)
_PATIENT_RECORD_TERMS = re.compile(
    r"\b(?:patient|record|chart|history|diagnos\w*|medicat\w*|medicine|drug|"
    r"dos\w*|prescrib\w*|treat\w*|lab\w*|test\w*|result\w*|admi\w*|"
    r"discharg\w*|procedure\w*|condition\w*|symptom\w*|encounter\w*|"
    r"clinical|medical)\b",
    re.IGNORECASE,
)


def is_patient_record_question(question: str) -> bool:
    """Return whether a question is scoped to patient-record retrieval."""
    return not _UNRELATED_TERMS.search(question) and bool(_PATIENT_RECORD_TERMS.search(question))