import pickle
from typing import Dict, List, Optional

from accuracy import Accuracy
from utils import equivalent_val
from _consts import OP_MAP
from _extra_typing import EntryKeyCollection

class Analyser:
    """A class for analysing conversation results.

    Args:
        entries (Entries): A collection of entries containing the expected
            answers, with a unique key for each that can be used access
            a specific entry.
        pickle_file_path (str): A path to a pickle file containing a
            dictionary of conversations.

    Attributes:
        entries (Entries): A collection of entries containing the expected
            answers, with a unique key for each that can be used access
            a specific entry.
        conversations (Dict[EntryKey, ConversationHandler]): The
            conversation handler for each entry, indexed by the entry's
            unique key. This will contain generated answers to be
            compared with the expected answers in entries.
    """
    
    def __init__(self, entries, pickle_file_path):
        self.entries = entries
        with open(pickle_file_path, "rb") as conversation_file:
            self.conversations = pickle.load(conversation_file)

    def compare(self, indices: Optional[EntryKeyCollection] = None):
        """View the difference between expected and generated results.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation. For each key,
        you can see the expected vs generated computed answers, followed
        by the expected vs generated retrievals and operations.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to compare results
                for.
        """
        indices = self._get_indices(indices)

        for i in indices:
            if self._index_absent(i):
                continue
            entry, conv = self.entries[i], self.conversations[i]
            c_acc = self.computational_accuracy([i])
            r_acc = self.computational_accuracy_by_question_type([i])["retrieval"]
            o_acc = self.operation_accuracy([i])
            print(f"\033[1mEntry {i}\033[0m")
            print("----------------------------------------")
            print("\033[1;31mQuestions\033[0m")
            for q in entry.questions:
                print(q)
            print("----------------------------------------")
            print("\033[1;34mComputations\033[0m")
            print(f"Expected : {entry.exe_answers}")
            print(f"Generated: {conv.exe_answers}")
            print(f"\033[34mComputational Accuracy:\033[0m {c_acc}")
            print("----------------------------------------")
            print("\033[1;32mRetrievals and Operations\033[0m")
            print(f"Expected : {entry.answers}")
            print(f"Generated: {conv.answers}")
            print(f"\033[32mRetrieval Accuracy:\033[0m {r_acc}")
            print(f"\033[32mOperation Accuracy:\033[0m {o_acc}")
            print("----------------------------------------\n")

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
        indices = self._get_indices(indices)

        for i in indices:
            if self._index_absent(i):
                continue
            if not self.conversations[i].err_log:
                continue
            print(f"Entry {i}")
            for err in self.conversations[i].err_log:
                print("----------------------------------------")
                print(err)
            print("\n----------------------------------------\n")

    def computational_accuracy(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Accuracy:
        """Compute the computational accuracy.

        For each question, the executed answer from the response from
        the LLM is compared to the expected answer.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated answer and the expected answer (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated answer and the expected answer (if they are
                floats)

        Returns:
            accuracy (Accuracy): An accuracy object, containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
        """
        indices = self._get_indices(indices)

        accuracy = Accuracy()
        for i in indices:
            if self._index_absent(i):
                continue
            expecteds = self.entries[i].exe_answers
            gots = self.conversations[i].exe_answers
            for expected, got in zip(expecteds, gots):
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracy.score += 1
                accuracy.total += 1
        accuracy.calculate_acc()
        return accuracy

    def computational_accuracy_by_question_number(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> List[Accuracy]:
        """Compute the accuracy of the executed answers by question number.

        For each question, the executed answer from the response from
        the LLM is compared to the expected answer. The accuracy scores are
        then grouped by question number within an entry. This allows for
        comparison in the accuracy between questions earlier and later on
        within an entry.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated answer and the expected answer (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated answer and the expected answer (if they are
                floats)

        Returns:
            accuracies (List[Accuracy]): A list of accuracy objects, 
                containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
                The list is indexed by question number.
            """
        indices = self._get_indices(indices)

        accuracies = []
        for i in indices:
            if self._index_absent(i):
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

    def computational_accuracy_by_question_type(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        """Compute the accuracy of the executed answers by question type.

        For each question, the executed answer from the response from
        the LLM is compared to the expected answer. The accuracy scores are
        separated by whether they are "retrieval" questions (looking up
        numbers within the text) or "operation" questions (performing a
        calculation).

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated answer and the expected answer (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated answer and the expected answer (if they are
                floats)

        Returns:
            accuracies (Dict[Accuracy]): An dict of accuracy objects,
                containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
                It will contain two items, one for "retrieval", and
                the other for "operation".
        """
        indices = self._get_indices(indices)

        accuracies = {"retrieval": Accuracy(), "operation": Accuracy()}
        for i in indices:
            if self._index_absent(i):
                continue
            entry = self.entries[i]
            expecteds = entry.exe_answers
            gots = self.conversations[i].exe_answers
            for question_number, (expected, got) in enumerate(zip(expecteds, gots)):
                key = "operation" if entry.is_operation(question_number) else "retrieval"
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracies[key].score += 1
                accuracies[key].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def computational_accuracy_by_operation(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        """Compute the accuracy of the executed answers by operation.

        For each question, the executed answer from the response from
        the LLM is compared to the expected answer. The accuracy scores are
        grouped by the operation expected to be performed in the expected
        answer. These scores only include "operation" type questions.
        Accuracy for "retrieval" questions can be obtained using the
        `answer_accuracy_by_question_type` method instead.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated answer and the expected answer (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated answer and the expected answer (if they are
                floats)

        Returns:
            accuracies (Dict[Accuracy]): An dict of accuracy objects,
                containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
                It will contain one item for each possible operation that
                can be performed.
        """
        indices = self._get_indices(indices)

        accuracies = {op: Accuracy() for op in OP_MAP}
        for i in indices:
            if self._index_absent(i):
                continue
            entry = self.entries[i]
            operations = entry.answers
            expecteds = entry.exe_answers
            gots = self.conversations[i].exe_answers
            for question_number, (expected, got, operation)  in enumerate(zip(expecteds, gots, operations)):
                if not entry.is_operation(question_number):
                    continue
                op = operation.split("(")[0]
                if equivalent_val(expected, got, rel_tol, abs_tol):
                    accuracies[op].score += 1
                accuracies[op].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def operation_accuracy(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ):
        """Compute the accuracy of the generated operations.

        For each "operation" type question, the operation generated by the
        LLM is compared to the expected operation to be performed.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated arguments and the expected arguments (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated arguments and the expected arguments (if they are
                floats)

        Returns:
            accuracy (Accuracy): An accuracy object, containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
        """
        indices = self._get_indices(indices)

        accuracy = Accuracy()
        for i in indices:
            if self._index_absent(i):
                continue
            entry = self.entries[i]
            answers = self.conversations[i].answers
            for question_number, answer in enumerate(answers):
                if not entry.is_operation(question_number):
                    continue
                if entry.equivalent_operations(question_number, answer, rel_tol, abs_tol):
                    accuracy.score += 1
                accuracy.total += 1
        accuracy.calculate_acc()
        return accuracy

    def operation_accuracy_by_question_number(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> List[Accuracy]:
        """Compute the accuracy of the generated operations by question number.

        For each "operation" type question, the generated operation from the
        response from the LLM is compared to the expected operation. The accuracy
        scores are then grouped by question number within an entry. This allows
        for comparison in the accuracy between questions earlier and later on
        within an entry.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated arguments and the expected arguments (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated arguments and the expected arguments (if they are
                floats)

        Returns:
            accuracies (List[Accuracy]): A list of accuracy objects, 
                containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
                The list is indexed by question number.
            """
        indices = self._get_indices(indices)

        accuracies = []
        for i in indices:
            if self._index_absent(i):
                continue
            entry = self.entries[i]
            answers = self.conversations[i].answers
            for question_number, answer in enumerate(answers):
                if question_number == len(accuracies):
                    accuracies.append(Accuracy())
                if not entry.is_operation(question_number):
                    continue
                if entry.equivalent_operations(question_number, answer, rel_tol, abs_tol):
                    accuracies[question_number].score += 1
                accuracies[question_number].total += 1
        for acc_item in accuracies:
            acc_item.calculate_acc()
        return accuracies

    def operation_accuracy_by_operation(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        """Compute the accuracy of the generated operations by operation.

        For each "operation" type question, the generated operation from the
        response from the LLM is compared to the expected operation. The accuracy
        scores are grouped by the operation expected to be performed in the
        expected answer.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to include in the
                accuracy calculation.
            rel_tol (float): The maximum allowed difference between the
                calculated answer and the expected answer (if they are
                floats), relative to the larger absolute value of the
                two
            abs_tol (float): The minimum absolute tolerance between the
                calculated answer and the expected answer (if they are
                floats)

        Returns:
            accuracies (Dict[Accuracy]): An dict of accuracy objects,
                containing:
                    * `score`: total number correct
                    * `total`: total number of questions
                    * `accuracy`: `score` / `total`
                It will contain one item for each possible operation that
                can be performed.
        """
        indices = self._get_indices(indices)

        accuracies = {op: Accuracy() for op in OP_MAP}
        for i in indices:
            if self._index_absent(i):
                continue
            entry = self.entries[i]
            operations = entry.answers
            answers = self.conversations[i].answers
            for question_number, (answer, operation)  in enumerate(zip(answers, operations)):
                if not entry.is_operation(question_number):
                    continue
                op = operation.split("(")[0]
                if entry.equivalent_operations(question_number, answer, rel_tol, abs_tol):
                    accuracies[op].score += 1
                accuracies[op].total += 1
        for acc_item in accuracies.values():
            acc_item.calculate_acc()
        return accuracies

    def backward_subtraction(
        self,
        indices: Optional[EntryKeyCollection] = None,
        rel_tol: float = 0.001,
        abs_tol: float = 0.0,
    ) -> Dict[str, Accuracy]:
        """Mark subtractions as "correct" if the arguments are reversed.

        This function goes through all subtraction operations and views
        only the ones where the correct arguments are placed in reverse
        order as correct, to test how often the LLM puts the arguments
        in the wrong order.

        Returns:
            accuracy (Accuracy): An accuracy object, containing:
                    * `score`: total number reversed subtraction
                    * `total`: total number of subtraction questions
                    * `accuracy`: `score` / `total`
        """
        indices = self._get_indices(indices)

        accuracy = Accuracy()
        for i in indices:
            if self._index_absent(i):
                continue
            entry = self.entries[i]
            operations = entry.answers
            answers = self.conversations[i].answers
            for question_number, (answer, operation)  in enumerate(zip(answers, operations)):
                if not entry.is_operation(question_number):
                    continue
                op = operation.split("(")[0]
                if op != "subtract":
                    continue
                if entry.backward_subtraction(question_number, answer, rel_tol, abs_tol):
                    accuracy.score += 1
                accuracy.total += 1
        accuracy.calculate_acc()
        return accuracy

    def _get_indices(self, indices):
        if indices is None:
            indices = list(self.conversations.keys())
        return indices

    def _index_absent(self, i):
        if i in self.conversations:
            return False
        # print(f"No conversation for entry {i}")
        return True