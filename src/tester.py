import math
import numbers
import collections
from dataclasses import dataclass

from conversation_handler import ConversationHandler
from client import Client
from _consts import OP_MAP
from _extra_typing import Entries, EntryKeyCollection

class Tester:
    """A class for testing the conversation handler.

    Args:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        entries (Entries): A collection of entries
            to be tested, with a unique key for each that can be used
            access a specific entry.

    Attributes:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        entries (Entries): A collection of entries
            to be tested, with a unique key for each that can be used
            access a specific entry.
        conversations (Dict[EntryKey, ConversationHandler]): The
            conversation handler for each entry, indexed by the entry's
            unique key.
    """
    def __init__(self, client: Client, entries: Entries):
        self.client = client
        self.entries = entries
        self.conversations = {}

    def run(self, indices: EntryKeyCollection):
        """Generate responses for each entry specified.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation, in order to
        start a conversation with an LLM using the client provided on
        initialisation, and attempt to answer each question.
        The results will be stored in the `conversations` attribute.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to generate responses
                for.
        """
        for i, entry_index in enumerate(indices):
            entry = self.entries[entry_index]
            ch = ConversationHandler(self.client, entry["context"])
            self.conversations[entry_index] = ch
            for j, question in enumerate(entry["questions"]):
                print(f"Processing Entry {i+1}/{len(indices)} (id: {entry_index}) - Question {j+1}/{len(entry["questions"])}                 ", end="\r")
                _, err = ch.ask(question)
                if err is not None:
                    print(
                        f"Found an error processing entry {entry_index}, question {j+1}. "
                        "Skipping to the next one..."
                    )
        print(f"Done                                                    ")

    def compare(self, indices: EntryKeyCollection):
        """View the difference between expected and generated results.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation. For each key,
        you can see the expected vs generated programs, followed by
        the expected vs generated final answers.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to compare results
                for.
        """
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation found with index {i}")
                continue
            entry, conv = self.entries[i], self.conversations[i]
            print(f"Entry {i}")
            print(entry["answers"])
            print(conv.extracted_answers)
            print("----------------------------------------")
            print(entry["exe_answers"])
            print(conv.exe_answers)
            print("\n----------------------------------------\n")

    def view_err_log(self, indices: EntryKeyCollection):
        """View the error logs.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation. For each key,
        you can see the errors raised while attempting to answer each
        question, if there were any.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to view the errors
                for.
        """
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation found with index {i}")
                continue
            if not self.conversations[i].err_log:
                continue
            print(f"Entry {i}")
            for err in self.conversations[i].err_log:
                print("----------------------------------------")
                print(err)
            print("\n----------------------------------------\n")

    def answer_accuracy(
        self,
        indices: EntryKeyCollection,
        rel_tol: float = 0.01,
        abs_tol: float = 0.0,
    ):
        accuracy = Accuracy()
        for i in indices:
            expecteds = self.entries[i]["exe_answers"]
            gots = self.conversations[i].exe_answers
            for expected, got in zip(expecteds, gots):
                if self._equivalent_answers(expected, got, rel_tol, abs_tol):
                    accuracy.score += 1
                accuracy.total += 1
        accuracy.calculate_acc()
        return accuracy

    def answer_accuracy_by_question_number(
        self,
        indices: EntryKeyCollection,
        rel_tol: float = 0.01,
        abs_tol: float = 0.0,
    ):
        accuracies = []
        for i in indices:
            expecteds = self.entries[i]["exe_answers"]
            gots = self.conversations[i].exe_answers
            for j, (expected, got) in enumerate(zip(expecteds, gots)):
                if j == len(accuracies):
                    accuracies.append(Accuracy())
                if self._equivalent_answers(expected, got, rel_tol, abs_tol):
                    accuracies[j].score += 1
                accuracies[j].total += 1
        for acc_item in accuracies:
            acc_item.calculate_acc()
        return accuracies

    def answer_accuracy_by_question_type(
        self,
        indices: EntryKeyCollection,
        rel_tol: float = 0.01,
        abs_tol: float = 0.0,
    ):
        accuracies = {"retrieval": Accuracy(), "program": Accuracy()}
        for i in indices:
            is_ops = self.entries[i]["is_op"]
            expecteds = self.entries[i]["exe_answers"]
            gots = self.conversations[i].exe_answers
            for expected, got, is_op  in zip(expecteds, gots, is_ops):
                key = "program" if is_op else "retrieval"
                if self._equivalent_answers(expected, got, rel_tol, abs_tol):
                    accuracies[key].score += 1
                accuracies[key].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def answer_accuracy_by_operation(
        self,
        indices: EntryKeyCollection,
        rel_tol: float = 0.01,
        abs_tol: float = 0.0,
    ):
        accuracies = {op: Accuracy() for op in OP_MAP}
        for i in indices:
            expecteds = self.entries[i]["exe_answers"]
            gots = self.conversations[i].exe_answers
            is_ops = self.entries[i]["is_op"]
            programs = self.entries[i]["answers"]
            for expected, got, is_op, program  in zip(expecteds, gots, is_ops, programs):
                if not is_op:
                    continue
                op = program.split("(")[0]
                if self._equivalent_answers(expected, got, rel_tol, abs_tol):
                    accuracies[op].score += 1
                accuracies[op].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def _equivalent_answers(self, expected, got, rel_tol, abs_tol):
        if isinstance(expected, numbers.Number) and isinstance(got, numbers.Number):
            return math.isclose(expected, got, rel_tol=rel_tol, abs_tol=abs_tol)
        return expected == got

    def program_accuracy(self, indices: EntryKeyCollection):
        pass

@dataclass
class Accuracy:
    score: int = 0
    total: int = 0
    accuracy: float = 0

    def calculate_acc(self):
        if self.total > 0:
            self.accuracy = self.score / self.total