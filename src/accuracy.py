from dataclasses import dataclass

@dataclass
class Accuracy:
    score: int = 0
    total: int = 0
    accuracy: float = 0

    def calculate_acc(self):
        if self.total > 0:
            self.accuracy = self.score / self.total