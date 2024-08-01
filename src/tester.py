from typing import Dict, List, Optional

from accuracy import Accuracy
from conversation_handler import ConversationHandler
from client import Client
from utils import equivalent_val
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

    def run(self, indices: Optional[EntryKeyCollection] = None):
        """Generate responses for each entry specified.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation, in order to
        start a conversation with an LLM using the client provided on
        initialisation, and attempt to answer each question.
        The results will be stored in the `conversations` attribute.

        Args:
            indices (Optional[EntryKeyCollection]): An iterable
                containing keys of the entries that you would like to
                generate responses for.
        """
        if indices is None:
            indices = list(self.entries.keys())

        for entry_number, entry_id in enumerate(indices):
            entry = self.entries[entry_id]
            ch = ConversationHandler(self.client, entry.context)
            self.conversations[entry_id] = ch
            for question_number, question in enumerate(entry.questions):
                print(
                    (
                        f"Processing Entry {entry_number+1}/{len(indices)} "
                        f"(id: {entry_id}) - "
                        f"Question {question_number+1}/{len(entry.questions)}"
                        "                 "
                    ),
                    end="\r",
                )
                _, err = ch.ask(question)
                if err is not None:
                    print(
                        f"Found an error processing entry {entry_id}, "
                        f"question {question_number+1}. "
                        "Skipping to the next one..."
                    )
        print(f"Done                                                    ")

    def compare(self, indices: Optional[EntryKeyCollection] = None):
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
        if indices is None:
            indices = list(self.entries.keys())

        for i in indices:
            if i not in self.conversations:
                print(f"No conversation found with index {i}")
                continue
            entry, conv = self.entries[i], self.conversations[i]
            print(f"Entry {i}")
            print(entry.answers)
            print(conv.answers)
            print("----------------------------------------")
            print(entry.exe_answers)
            print(conv.exe_answers)
            print("\n----------------------------------------\n")

    def view_err_log(self, indices: Optional[EntryKeyCollection] = None):
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
        if indices is None:
            indices = list(self.entries.keys())

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
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Accuracy:
        if indices is None:
            indices = list(self.entries.keys())

        accuracy = Accuracy()
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            expecteds = self.entries[i].exe_answers
            gots = self.conversations[i].exe_answers
            for expected, got in zip(expecteds, gots):
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracy.score += 1
                accuracy.total += 1
        accuracy.calculate_acc()
        return accuracy

    def answer_accuracy_by_question_number(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> List[Accuracy]:
        if indices is None:
            indices = list(self.entries.keys())

        accuracies = []
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            expecteds = self.entries[i].exe_answers
            gots = self.conversations[i].exe_answers
            for question_number, (expected, got) in enumerate(zip(expecteds, gots)):
                if question_number == len(accuracies):
                    accuracies.append(Accuracy())
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracies[question_number].score += 1
                accuracies[question_number].total += 1
        for acc_item in accuracies:
            acc_item.calculate_acc()
        return accuracies

    def answer_accuracy_by_question_type(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        if indices is None:
            indices = list(self.entries.keys())

        accuracies = {"retrieval": Accuracy(), "program": Accuracy()}
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            entry = self.entries[i]
            expecteds = entry.exe_answers
            gots = self.conversations[i].exe_answers
            for question_number, (expected, got) in enumerate(zip(expecteds, gots)):
                key = "program" if entry.is_program(question_number) else "retrieval"
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracies[key].score += 1
                accuracies[key].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def answer_accuracy_by_operation(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        if indices is None:
            indices = list(self.entries.keys())

        accuracies = {op: Accuracy() for op in OP_MAP}
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            entry = self.entries[i]
            programs = entry.answers
            expecteds = entry.exe_answers
            gots = self.conversations[i].exe_answers
            for question_number, (expected, got, program)  in enumerate(zip(expecteds, gots, programs)):
                if not entry.is_program(question_number):
                    continue
                op = program.split("(")[0]
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracies[op].score += 1
                accuracies[op].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def program_accuracy(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ):
        if indices is None:
            indices = list(self.entries.keys())

        accuracy = Accuracy()
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            entry = self.entries[i]
            answers = self.conversations[i].answers
            for question_number, answer in enumerate(answers):
                if not entry.is_program(question_number):
                    continue
                if entry.equivalent_programs(question_number, answer, rel_tol, abs_tol):
                    accuracy.score += 1
                accuracy.total += 1
        accuracy.calculate_acc()
        return accuracy

    def program_accuracy_by_question_number(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> List[Accuracy]:
        if indices is None:
            indices = list(self.entries.keys())

        accuracies = []
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            entry = self.entries[i]
            answers = self.conversations[i].answers
            for question_number, answer in enumerate(answers):
                if question_number == len(accuracies):
                    accuracies.append(Accuracy())
                if not entry.is_program(question_number):
                    continue
                if entry.equivalent_programs(question_number, answer, rel_tol, abs_tol):
                    accuracies[question_number].score += 1
                accuracies[question_number].total += 1
        for acc_item in accuracies:
            acc_item.calculate_acc()
        return accuracies

    def program_accuracy_by_operation(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        if indices is None:
            indices = list(self.entries.keys())

        accuracies = {op: Accuracy() for op in OP_MAP}
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation for entry {i}")
                continue
            entry = self.entries[i]
            programs = entry.answers
            answers = self.conversations[i].answers
            for question_number, (answer, program)  in enumerate(zip(answers, programs)):
                if not entry.is_program(question_number):
                    continue
                op = program.split("(")[0]
                if entry.equivalent_programs(question_number, answer, rel_tol, abs_tol):
                    accuracies[op].score += 1
                accuracies[op].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies