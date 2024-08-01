import math
from typing import Tuple, Union

from client import Client
from utils import extract_raw_answer, execute_answer
from _consts import INIT_MESSAGES, ASSISTANT_INITIAL_CONFIRMATION, SUFFIX

class ConversationHandler:
    """A class for conversing with an LLM given some initial context.

    Args:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        context (str): Some context to set the scene for the LLM so
            that it can refer back to it for question answering.

    Attributes:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        conversation (Conversation): The message history.
        answers (List[str]): A list of the responses from the LLM so
            far in the conversation. These can either be numbers or
            a description of an operation, in the form:
                operation(arg1, arg2)
        extracted_answers (List[str]): The portion of each answer to
            the right-hand side of the "=" sign, to allow for easy
            comparison with answers as formatted in the dataset.
        exe_answers (List[float]): The executed versions of the each
            answer in answers.
        question_count (int): The number of questions asked by the
            user in the conversation so far.
        err_log (List[str]): A list of messages from each error in the
            conversation.
        err_indices (List[int]): The indices of the questions where an
            error occured.
    """

    def __init__(self, client: Client, context: str):
        self.client = client
        self.conversation = INIT_MESSAGES.copy()
        self.conversation.extend([
            {
                "role": "user",
                "content": context
            },
            {
                "role": "assistant",
                "content": ASSISTANT_INITIAL_CONFIRMATION
            },
        ])
        self.full_answers = []
        self.answers = []
        self.exe_answers = []
        self.question_count = 0
        self.err_log = []
        self.err_indices = []

    def ask(self, question: str) -> Tuple[float, Union[None, str]]:
        """Ask the LLM a question based on the provided context.

        Args:
            question (str): The question to ask the LLM.

        Returns:
            answer (float): The executed answer.
            error (Union[None, str]): An error message if there was a
                problem handling the request.
        """
        # Add the provided question to the conversation, prefixed with
        # a question index to allow the LLM to more easily refer to
        # specific answers, as well as the calculated value of the last
        # question's response
        if self.exe_answers and not math.isnan(self.exe_answers[-1]):
            prefix = f"Ok, so ANS{self.question_count-1} = {self.exe_answers[-1]}. Now the next question:\n"
        else:
            prefix = ""
        self.conversation.append({
            "role": "user",
            "content": f"{prefix}Q{self.question_count}: {question}\n{SUFFIX}"
        })

        # An answer will be generated in a "raw" form that will then
        # need to be processed to get a real output
        answer = self.client.generate(self.conversation)
        
        # Add the response in "raw" form to the conversation to keep
        # the conversation history up-to-date so that the LLM can
        # refer to previous answers
        self.conversation.append({
            "role": "assistant",
            "content": answer
        })
        self.question_count += 1
        self.full_answers.append(answer)

        # Attempt to process the generated answer
        try:
            extracted_answer = extract_raw_answer(answer)
        except Exception as e:
            self._log_new_error(answer, e)
            extracted_answer = "n/a"
            exe_answer = float("nan")
            error = self.err_log[-1]
        else:
            try:
                exe_answer = execute_answer(extracted_answer, self.exe_answers)
                error = None
            except Exception as e:
                self._log_new_error(answer, e)
                exe_answer = float("nan")
                error = self.err_log[-1]

        self.answers.append(extracted_answer)
        self.exe_answers.append(exe_answer)
        return exe_answer, error

    def _log_new_error(self, answer, error):
        self.err_log.append(
            f"Question {self.question_count}: Answer {answer}\nError: {error}"
        )
        self.err_indices.append(self.question_count)