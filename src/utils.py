import math
import numbers
from typing import List

from _consts import OP_MAP

def is_operation(answer):
    return "(" in answer

def equivalent_operation(program1, program2, exe_answers, rel_tol, abs_tol):
    try:
        op_1, arg1_1, arg2_1 = split_operation(program1)
        op_2, arg1_2, arg2_2 = split_operation(program2)
        arg1_1 = process_arg(arg1_1, exe_answers)
        arg2_1 = process_arg(arg2_1, exe_answers)
        arg1_2 = process_arg(arg1_2, exe_answers)
        arg2_2 = process_arg(arg2_2, exe_answers)
    except Exception as e:
        return False
    if op_1 != op_2:
        return False
    if op_1 in ["subtract", "divide", "exp", "greater"]:
        return equivalent_val(arg1_1, arg1_2, rel_tol, abs_tol) and equivalent_val(arg2_1, arg2_2, rel_tol, abs_tol)
    elif op_1 in ["add", "multiply"]:
        return (
            (equivalent_val(arg1_1, arg1_2, rel_tol, abs_tol) and equivalent_val(arg2_1, arg2_2, rel_tol, abs_tol))
            or (equivalent_val(arg1_1, arg2_2, rel_tol, abs_tol) and equivalent_val(arg1_1, arg2_2, rel_tol, abs_tol))
        )
    else:
        raise AssertionError("should be unreachable")

def equivalent_val(expected, got, rel_tol=0.01, abs_tol=0):
    if isinstance(expected, numbers.Number) and isinstance(got, numbers.Number):
        return math.isclose(expected, got, rel_tol=rel_tol, abs_tol=abs_tol)
    return expected == got

def extract_raw_answer(answer: str) -> str:
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

def execute_answer(answer: str, exe_answers: List[float]) -> float:
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
        return process_arg(answer, exe_answers)
    except ArgumentException:
        pass

    op, arg1, arg2 = split_operation(answer)
    arg1, arg2 = process_arg(arg1, exe_answers), process_arg(arg2, exe_answers)

    try:
        exe_answer = OP_MAP[op](arg1, arg2)
    except Exception as e:
        raise OperationException(
            f"Error handling the operation of {op}({arg1}, {arg2}): {e}"
        )

    return exe_answer

def split_operation(answer: str):
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
    return op, arg1, arg2

def process_arg(arg: str, exe_answers: List[float]):
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
            processed_arg = exe_answers[answer_index]
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
    

class AnswerException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class FormatException(AnswerException):
    def __init__(self, message):
        super().__init__(message)

class OperationException(AnswerException):
    def __init__(self, message):
        super().__init__(message)

class ArgumentException(AnswerException):
    def __init__(self, message):
        super().__init__(message)