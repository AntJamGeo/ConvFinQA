from client import Client
from _consts import INIT_MESSAGES, OP_MAP

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
        exe_answers (List[float]): The executed versions of the each
            answer in answers.
        question_count (int): The number of questions asked by the
            user in the conversation so far.
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
                "content": "Understood. And what are your questions? I will make sure to only answer with a number, or in the form operation(arg1, arg2)."
            },
        ])
        self.answers = []
        self.exe_answers = []
        self.question_count = 0

    def ask(self, question: str) -> float:
        """Ask the LLM a question based on the provided context.

        Args:
            question (str): The question to ask the LLM.

        Returns:
            answer (float): The executed answer.

        Raises:
            ConversationException: If there is an issue with the format
                of the LLM's response, this will need to be handled
                gracefully by taking care of any ConversationException
                raised.
        """

        # Add the provided question to the conversation, prefixed with
        # a question index to allow the LLM to more easily refer to
        # specific answers
        self.conversation.append({
            "role": "user",
            "content": f"Q{self.question_count}: {question}"
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
        
        answer = self._extract_raw_answer(answer)
        self.answers.append(answer)
        exe_answer = self._execute_answer(answer)
        self.exe_answers.append(exe_answer)

        return self.exe_answers[-1]

    def _extract_raw_answer(answer: str) -> str:
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
            return float(answer)
        except ValueError:
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
                f"{op_and_args}"
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
        arg = arg.strip()
        try:
            if arg.startswith("ANS"):
                answer_index = int(arg[3:])
                processed_arg = self.exe_answers[answer_index]
            else:
                processed_arg = float(arg)
        except Exception as e:
            raise ArgumentException(
                f"Error processing the argument \"{arg}\": {e}"
            )
        return processed_arg
        

class ConversationException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class FormatException(ConversationException):
    def __init__(self, message):
        super().__init__(message)

class OperationException(ConversationException):
    def __init__(self, message):
        super().__init__(message)

class ArgumentException(ConversationException):
    def __init__(self, message):
        super().__init__(message)