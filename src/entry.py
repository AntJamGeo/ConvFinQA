from typing import List
from dataclasses import dataclass

@dataclass
class Entry:
    """An entry contains some context, a set of questions to answer, and
    their model answers
    """
    id: int
    type: int
    context: str
    questions: List[str]
    answers: List[str]
    exe_answers: List[float]