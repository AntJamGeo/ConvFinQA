OP_MAP = {
    "add": lambda x, y: x + y,
    "subtract": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "divide": lambda x, y: x / y,
    "exp": lambda x, y: x ** y,
    "greater": lambda x, y: "yes" if x > y else "no" ,
}

# A simple HTML table to use as context for the example
_context = "<table class='wikitable'><tr><td>1</td><td>year</td><td>1993</td><td>1994</td><td>1995</td></tr><tr><td>2</td><td>revenue</td><td>£23,456</td><td>£43,219</td><td>£101,129</td></tr><tr><td>3</td><td>costs</td><td>£40,987</td><td>£47,231</td><td>£60,943</td></tr></table>"

# A collection of messages to pass as some initial context for the model
INIT_MESSAGES = [
    {
        "role": "user",
        "content": """You will be given a some context and then some questions that you will need to answer based on that context.

Each of your answers must start with a prefix ANS{i} = {your answer}, where {i} is replaced by the current question number (e.g. ANS0 for question 0, ANS1 for question 1, etc.), and {your answer} is filled with your answer.
Your answer will take one of two forms. You will need to understand whether the question is asking for retrieval of data from the context, or an operation to be performed on two retrieved or derived figures.
In the first case (retrieval), you must find the correct number that answers the question, and replace {your answer} with that exact number, but only the digits, so no comma separation or units.
In the second case (operation), you must tell me the correct operation as well as the correct arguments for that operation. This must be written in the form "operation(arg1, arg2)". The following operations are permitted:
* add
* subtract
* multiply
* divide
* exp
* greater

The arguments must either be lifted from the text, with no comma separation or units, or must be references to previous answers, written as ANS{i} where {i} is replaced with the index of the suitable answer.
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
        "content": f"This is the context:\n{_context}"
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
        "content": "Q1: What was the profit in 1993?"
    },
    {
        "role": "assistant",
        "content": "ANS1 = subtract(ANS0, 40987)"
    },
    {
        "role": "user",
        "content": "Q2: What was the profit in 1994?",
    },
    {
        "role": "assistant",
        "content": "ANS2 = subtract(43219, 47231)",
    },
    {
        "role": "user",
        "content": "Q3: What was the percentage change in profit between 1993 and 1994?",
    },
    {
        "role": "assistant",
        "content": "ANS3 = divide(ANS2, ANS1)"
    },
    {
        "role": "user",
        "content": "Q4: What was the total revenue in 1993 and 1994?",
    },
    {
        "role": "assistant",
        "content": "ANS4 = add(ANS0, 43219)"
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