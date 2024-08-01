from typing import List
from dataclasses import dataclass

from utils import is_program, equivalent_programs

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

    def is_program(self, question_number):
        return is_program(self.answers[question_number])

    def equivalent_programs(self, question_number, program, rel_tol, abs_tol):
        expected = self.answers[question_number]
        return equivalent_programs(expected, program, self.exe_answers, rel_tol, abs_tol)