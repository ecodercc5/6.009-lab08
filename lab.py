#!/usr/bin/env python3
"""6.009 Lab 8: Carlae (LISP) Interpreter"""

import doctest

# NO ADDITIONAL IMPORTS!


###########################
# Carlae-related Exceptions #
###########################


class CarlaeError(Exception):
    """
    A type of exception to be raised if there is an error with a Carlae
    program.  Should never be raised directly; rather, subclasses should be
    raised.
    """

    pass


class CarlaeSyntaxError(CarlaeError):
    """
    Exception to be raised when trying to evaluate a malformed expression.
    """

    pass


class CarlaeNameError(CarlaeError):
    """
    Exception to be raised when looking up a name that has not been defined.
    """

    pass


class CarlaeEvaluationError(CarlaeError):
    """
    Exception to be raised if there is an error during evaluation other than a
    CarlaeNameError.
    """

    pass


############################
# Tokenization and Parsing #
############################


def number_or_symbol(x):
    """
    Helper function: given a string, convert it to an integer or a float if
    possible; otherwise, return the string itself

    >>> number_or_symbol('8')
    8
    >>> number_or_symbol('-5.32')
    -5.32
    >>> number_or_symbol('1.2.3.4')
    '1.2.3.4'
    >>> number_or_symbol('x')
    'x'
    """
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            return x


parenthesis = ["(", ")"]
keywords = [":=", "function"]
whitespace = [" ", "\n"]
comment = "#"
delimiters = [*parenthesis, *whitespace]


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a Carlae
                      expression
    """
    tokens = []

    current_token = ""
    is_comment = False

    # loop thr the chars in source
    for char in source:
        if char in delimiters:
            # put current token into list of tokens if it exists
            if current_token:
                tokens.append(current_token)

            current_token = ""

        # ignore whitespaces
        if char in whitespace:
            if char == "\n":
                is_comment = False
            continue

        if is_comment:
            continue

        # add parenthesis then move on
        if char in parenthesis:
            tokens.append(char)

            continue

        # assuming no string type and # is not in string
        if char == comment:
            is_comment = True
            continue

        # build up current token
        current_token += char

        # check if current token is a keyword
        if current_token in keywords:
            tokens.append(current_token)
            current_token = ""

    # if remaining token, add to tokens
    if current_token:
        tokens.append(current_token)

    return tokens


def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    # print(tokens)

    # base case -> one token
    if len(tokens) == 1:
        # edge case -> single parenthesis
        if tokens[0] == "(" or tokens[0] == ")":
            raise CarlaeSyntaxError()

        return number_or_symbol(tokens[0])

    # check if enclosed in parenthesis
    if tokens[0] != "(" or tokens[-1] != ")":
        raise CarlaeSyntaxError()

    # recursive case
    groups = _group_tokens(tokens[1:-1])

    parsed_expression = [parse(group) for group in groups]

    # for group in groups:
    #     parsed_group = parse(group)

    #     parsed_expression.append(parsed_group)

    return parsed_expression


def _group_tokens(tokens):
    """ """

    groups = []
    opening_parenthesis_index = -1
    paren_stack = 0

    for i, token in enumerate(tokens):
        if token == "(":
            paren_stack += 1
            if opening_parenthesis_index < 0:
                opening_parenthesis_index = i

            continue

        if token == ")":

            paren_stack -= 1

            if paren_stack < 0:
                raise CarlaeSyntaxError()

            if paren_stack == 0:
                groups.append(tokens[opening_parenthesis_index : i + 1])
                opening_parenthesis_index = -1

            continue

        if opening_parenthesis_index >= 0:
            continue

        groups.append([token])

    # print(groups)

    if paren_stack > 0:
        raise CarlaeSyntaxError()

    return groups


######################
# Built-in Functions #
######################


def multiply(args):
    value = 1

    for arg in args:
        value *= arg

    return value


def divide(args):
    value = args[0]

    for arg in args[1:]:
        value /= arg

    return value


carlae_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": multiply,
    "/": divide,
}


##############
# Evaluation #
##############


def evaluate(tree):
    """
    Evaluate the given syntax tree according to the rules of the Carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    if tree == []:
        return []

    # check if tree is a number or a builtin carlae type
    if isinstance(tree, int) or isinstance(tree, float):
        return tree

    if isinstance(tree, str):
        builtin_object = carlae_builtins.get(tree)

        if builtin_object:
            return builtin_object

        raise CarlaeNameError()

    # evaluate each expression in the tree
    evaluated_expressions = [evaluate(expression) for expression in tree]

    # if length of evaluated expressions is 1 return that value
    if len(evaluated_expressions) == 1:
        return evaluated_expressions[0]

    # check if first evaluated expression is a function
    func = evaluated_expressions[0]

    if not callable(func):
        raise CarlaeEvaluationError()

    # call the func on rest of evaluated expressions
    evaluated = func(evaluated_expressions[1:])

    # print(evaluated)

    return evaluated


if __name__ == "__main__":
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)

    # uncommenting the following line will run doctests from above
    # doctest.testmod()

    while True:
        raw_carlae_str = input("in> ")

        if raw_carlae_str == "EXIT":
            break

        try:
            tokens = tokenize(raw_carlae_str)
            parsed = parse(tokens)
            evaluated = evaluate(parsed)

            print(f"out> {evaluated}")

        except Exception as e:
            exception_name = e.__class__.__name__
            print(exception_name)
