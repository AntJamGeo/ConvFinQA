from typing import List
from dataclasses import dataclass

from utils import is_operation, equivalent_operation

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

    def is_operation(self, question_number):
        return is_operation(self.answers[question_number])

    def equivalent_operations(self, question_number, program, rel_tol, abs_tol):
        expected = self.answers[question_number]
        return equivalent_operation(expected, program, self.exe_answers, rel_tol, abs_tol)