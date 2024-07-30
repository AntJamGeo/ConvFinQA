import math
from typing import Tuple, Union

from client import Client
from _consts import INIT_MESSAGES, ASSISTANT_INITIAL_CONFIRMATION, OP_MAP

class ConversationHandler:
    """A class for conversing with an LLM given some initial context.

    Args:
        client (client.Client): A client that handles sending and
            receiving messages to and from an LLM.
        context (str): Some context to set the scene for the LLM so
            that it can refer back to it for question answering.

    Attributes:
        client (client.Client): A client that handles sending and
            receiving messages to and from an LLM.
        conversation (List[Dict[str, str]]): The message history of
            the conversation.
            Each entry in the list is a dict with two keys:
                - "role": the agent who sent the message (this can
                    either be the "user" or the LLM "assistant")
                - "content": the content of the message
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
        self.answers = []
        self.extracted_answers = []
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
            "content": f"{prefix}Q{self.question_count}: {question}"
        })

        # An answer will be generated in a "raw" form that will then
        # need to be processed to get a real output
        try:
            answer = self.client.generate(self.conversation)
        except Exception as e:
            self._log_new_error("N/A", e)
            return float("nan"), self.err_log[-1]
        
        # Add the response in "raw" form to the conversation to keep
        # the conversation history up-to-date so that the LLM can
        # refer to previous answers
        self.conversation.append({
            "role": "assistant",
            "content": answer
        })
        self.question_count += 1
        self.answers.append(answer)

        # Attempt to process the generated answer
        try:
            extracted_answer = self._extract_raw_answer(answer)
            exe_answer = self._execute_answer(extracted_answer)
            error = None
        except Exception as e:
            self._log_new_error(answer, e)
            extracted_answer = "n/a"
            exe_answer = float("nan")
            error = self.err_log[-1]

        self.extracted_answers.append(extracted_answer)
        self.exe_answers.append(exe_answer)
        return exe_answer, error

    def _extract_raw_answer(self, answer: str) -> str:
        """Extract the raw answer from the LLM response.

        The answer from the LLM should be in the form:
            ANS{n} = {raw answer}
        So we would expect there to be one equals sign and the raw
        answer to the right of it.
        """
        if "=" not in answer:
            raise FormatException("Answer from the LLM should include an \"=\" sign")
        answer = answer.split("=")
        return answer[1].strip()

    def _execute_answer(self, answer: str) -> float:
        """Execute the operation in the answer.
        
        The answer from the LLM should either be a float already that
        was extracted from the context, or an operation with two args.
        We first try to convert the answer to a float, and if not, we
        expect to have an operation that can be performed in order to
        get the final answer.

        An operation is of the form:
            operation(arg1, arg2)
        so this method will check that "(", ")" and "," characters are
        present, and process the arguments to get the final answer.
        """
        try:
            return self._process_arg(answer)
        except ArgumentException:
            pass

        if "(" not in answer:
            raise FormatException(
                "Non-float answer should be an operation but found no \"(\""
            )

        op_and_args = answer.split("(")
        if len(op_and_args) != 2:
            raise FormatException(
                "Non-float answer should be an operation of the form "
                "\"operation(arg1, arg2)\", but got the following: "
                f"{answer}"
            )

        op, args = op_and_args
        if op not in OP_MAP:
            raise OperationException(
                f"Non-float answer should have a valid operation, got \"{op}\""
            )

        if ")" not in args:
            raise FormatException(
                "Non-float answer should be an operation but found no \")\""
            )
        args = args.split(")")[0]

        if "," not in args:
            raise FormatException(
                "Non-float answer should be an operation but found no \",\""
            )
        arg1, arg2 = args.split(",")
        arg1, arg2 = self._process_arg(arg1), self._process_arg(arg2)

        try:
            exe_answer = OP_MAP[op](arg1, arg2)
        except Exception as e:
            raise OperationException(
                f"Error handling the operation of {op}({arg1}, {arg2}): {e}"
            )

        return exe_answer

    def _process_arg(self, arg):
        """Process the provided argument.

        First remove all spaces, and then check if the argument is a
        reference to another answer (in which case, it starts with
        "ANS"), or is a numerical value. If it is a percentage, we
        have to also divide by 100.
        """
        arg = arg.replace(" ", "")
        try:
            if arg.startswith("ANS"):
                answer_index = int(arg[3:])
                processed_arg = self.exe_answers[answer_index]
                if math.isnan(processed_arg):
                    raise ArgumentException(
                        "Operation requires use of nan value"
                    )
            else:
                arg = arg.replace(",", "")
                arg = arg.replace("$", "")
                if arg.endswith("%"):
                    processed_arg = float(arg[:-1]) / 100
                else:
                    processed_arg = float(arg)
        except ArgumentException as e:
            raise e
        except Exception as e:
            raise ArgumentException(
                f"Error processing the argument \"{arg}\": {e}"
            )
        return processed_arg
        
    def _log_new_error(self, answer, error):
        self.err_log.append(
            f"Question {self.question_count}: Answer {answer}\nError: {error}"
        )
        self.err_indices.append(self.question_count)


class ConversationException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class AnswerException(ConversationException):
    def __init__(self, message):
        super().__init__(message)

class FormatException(AnswerException):
    def __init__(self, message):
        super().__init__(message)

class OperationException(AnswerException):
    def __init__(self, message):
        super().__init__(message)

class ArgumentException(AnswerException):
    def __init__(self, message):
        super().__init__(message)