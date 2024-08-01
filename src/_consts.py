OP_MAP = {
    "add": lambda x, y: x + y,
    "subtract": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "divide": lambda x, y: x / y,
    "exp": lambda x, y: x ** y,
    "greater": lambda x, y: "yes" if x > y else "no" ,
}

# Simple HTML tables to use as context for the examples
_context1 = "<table class='wikitable'><tr><td>1</td><td>year</td><td>1993</td><td>1994</td><td>1995</td></tr><tr><td>2</td><td>revenue</td><td>£23,456</td><td>£43,219</td><td>£101,129</td></tr><tr><td>3</td><td>costs</td><td>£40,987</td><td>£47,231</td><td>£60,943</td></tr></table>"
_context2 = "<table class='wikitable'><tr><td>customer</td><td>loan value (€)</td><td>interest rate (%)</td></tr><tr><td>1</td><td>2,014.45</td><td>9.27</td></tr><tr><td>2</td><td>23,015.13</td><td>9.11</td></tr><tr><td>3</td><td>1,095.42</td><td>8.77</td></tr><tr><td>4</td><td>13,732.56</td><td>10.10</td></tr></table>"

SUFFIX = "Remember to only answer with a number from the text, or an operation with two arguments in the form operation(arg1, arg2)."

# A collection of messages to pass as some initial context for the model
INIT_MESSAGES = [
    {
        "role": "user",
        "content": """You will be given a some context and then some questions that you will need to answer based on that context.

Each of your answers must start with a prefix ANS{i} = {your answer}, where {i} is replaced by the current question number (e.g. ANS0 for question 0, ANS1 for question 1, etc.), and {your answer} is filled with your answer.
Your answer will take one of two forms. You will need to understand whether the question is asking for retrieval of data from the context, or an operation to be performed on two retrieved or derived figures.
In the first case (retrieval), you must find the correct number that answers the question, and replace {your answer} with that exact number. If the value is a percentage, make sure to include the percentage sign at the end.
In the second case (operation), you must tell me the correct operation as well as the correct arguments for that operation. This must be written in the form "operation(arg1, arg2)". The following operations are permitted:
* add
* subtract
* multiply
* divide
* exp
* greater

Each argument must either be lifted from the text, in the same format as a you would provide for the retrieval case, or must be references to previous answers, written as ANS{i} where {i} is replaced with the index of the suitable answer.
For example, if you determine that the correct operation is to divide 3456 by ANS3, {your answer} will be replaced by "divide(3456, ANS3)".
I will provide an example conversation.
"""
    },
    {
        "role": "assistant",
        "content": "Understood. Please provide your example conversation."
    },
    {
        "role": "user",
        "content": f"This is the context:\n{_context1}"
    },
    {
        "role": "assistant",
        "content": "Understood. What are your questions?"
    },
    {
        "role": "user",
        "content": "Q0: What was the revenue in 1993?"
    },
    {
        "role": "assistant",
        "content": "ANS0 = 23456"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS0 = 23456. Now the next question:\n"
            "Q1: What was the profit in 1993?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS1 = subtract(ANS0, 40987)"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS1 = -17531. Now the next question:\n"
            "Q2: What was the profit in 1994?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS2 = subtract(43219, 47231)",
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS2 = -4012. Now the next question:\n"
            "Q3: What was the percentage change in profit between 1993 and 1994?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS3 = divide(ANS2, ANS1)"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS3 = 0.22885174833. Now the next question:\n"
            "Q4: What was the total revenue in 1993 and 1994?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS4 = add(ANS0, 43219)"
    },
    {
        "role": "user",
        "content": "Good. Now we will do another example."
    },
    {
        "role": "assistant",
        "content": "Ok, what is the context?",
    },
    {
        "role": "user",
        "content": _context2,
    },
    {
        "role": "assistant",
        "content": "Understood. What are your questions?"
    },
    {
        "role": "user",
        "content": "Q0: What is the interest rate for customer 3's loan?",
    },
    {
        "role": "assistant",
        "content": "ANS0 = 8.77%"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS0 = 0.0877. Now the next question:\n"
            "Q1: What do I have to multiply customer 3's loan value by to get the loan's value in a year?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS1 = add(1, ANS0)"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS1 = 1.0877. Now the next question:\n"
            "Q2: How about after 7 years?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS2 = exp(ANS1, 7)"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS2 = 1.80120813492. Now the next question:\n"
            "Q3: So what is the loan's value after 7 years assuming no repayments?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS3 = multiply(1095.42, ANS2)"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS3 = 1973.07941515. Now the next question:\n"
            "Q4: What do I have to multiply customer 2's loan value by to get the loan's value in a year?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS4 = add(1, 9.11%)"
    },
    {
        "role": "user",
        "content": (
            "Ok, so ANS4 = 1.0911. Now the next question:\n"
            "Q5: Is customer 3's loan after 7 years less than customer 2's loan after 1 year, assuming no repayments?"
        )
    },
    {
        "role": "assistant",
        "content": "ANS5 = greater(ANS4, ANS3)"
    },
    {
        "role": "user",
        "content": "Good. Now we will start the actual exercise."
    },
    {
        "role": "assistant",
        "content": "Great! What is the context?",
    },
]

ASSISTANT_INITIAL_CONFIRMATION = "Understood. And what are your questions? I will make sure to only answer with a number, including a percentage sign \"%\" if I am asked for a percentage, or in the form operation(arg1, arg2)."