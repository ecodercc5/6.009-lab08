#!/usr/bin/env python3
"""6.009 Lab 8: Carlae (LISP) Interpreter"""

import doctest
import pprint

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
    # base case -> one token
    if len(tokens) == 1:
        # edge case -> single parenthesis
        if tokens[0] == "(" or tokens[0] == ")":
            raise CarlaeSyntaxError()

        return number_or_symbol(tokens[0])

    # recursive case
    groups = _group_tokens(tokens)
    parsed_expression = [parse(group) for group in groups]

    return parsed_expression


def _group_tokens(tokens):
    """ """
    # check if enclosed in parenthesis
    if tokens[0] != "(" or tokens[-1] != ")":
        raise CarlaeSyntaxError()

    inner_tokens = tokens[1:-1]
    groups = []
    opening_parenthesis_index = -1
    paren_stack = 0

    for i, token in enumerate(inner_tokens):
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
                groups.append(inner_tokens[opening_parenthesis_index : i + 1])
                opening_parenthesis_index = -1

            continue

        if opening_parenthesis_index >= 0:
            continue

        groups.append([token])

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


def assignment(variable, value, env):
    env.set(variable, value)

    return value


carlae_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": multiply,
    "/": divide,
    ":=": assignment,
}


##############
# Evaluation #
##############


class Environment:
    def __init__(self, init_bindings, parent_env=None):
        self.variables = init_bindings
        self.parent = parent_env

    def get(self, variable):
        # get the variable binding
        value = self.variables.get(variable)

        # if binding exists
        if value:
            return value

        # binding doesn't exist, check if parent env exists
        if not self.parent:
            return None

        # get variable from parent env
        return self.parent.get(variable)

    def set(self, variable, value):
        """
        Set a variable binding in the current env
        """

        self.variables[variable] = value

    def __str__(self):
        return f"(variables: {pprint.pformat(self.variables)})"


def _create_env(env):
    if env:
        return env

    builtins = Environment(carlae_builtins)

    return Environment({}, builtins)


class CarlaeFunction:
    def __init__(self, parameters, body, enclosing_env):
        self.parameters = parameters
        self.body = body
        self.enclosing_env = enclosing_env

    def call(self, arguments):

        # print("-----")
        # print(f"calling {self.parameters}")
        # print(f"args: {arguments}")
        # print()

        # different number of parameters -> error
        if len(self.parameters) != len(arguments):
            # print(self.parameters)
            # print(arguments)
            raise CarlaeEvaluationError()

        # print("calling function")

        # print(arguments)

        # evaluate arguments of function
        evaluated_arguments = [evaluate(arg, self.enclosing_env) for arg in arguments]

        # print(evaluated_arguments)

        # create environment for function
        func_env = Environment({}, self.enclosing_env)

        # bind variables to environment
        for var, val in zip(self.parameters, evaluated_arguments):
            func_env.set(var, val)

        # print(func_env)

        # evalute the function body in the function environment
        return_value = evaluate(self.body, func_env)

        # print("return value")

        # print(return_value)

        return return_value

    def __str__(self):
        return f"parameters: {self.parameters}, body: {self.body}"


def create_function(parameters, body, enclosing_env):
    return CarlaeFunction(parameters, body, enclosing_env)


def evaluate(tree, env=None):
    """
    Evaluate the given syntax tree according to the rules of the Carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """

    env = _create_env(env)

    if tree == []:
        return []

    # check if tree is a number or a builtin carlae type
    if isinstance(tree, int) or isinstance(tree, float):
        return tree

    if isinstance(tree, str):
        val = env.get(tree)

        if val is None:
            raise CarlaeNameError()

        return val

    if isinstance(tree, CarlaeFunction):
        # function with no arguments
        return tree.call([])

    print("tree")
    print(tree)
    keyword = tree[0]

    # variable assignment
    if keyword == ":=":

        # handle function assignment -> shorthand
        is_shorthand_func_def = isinstance(tree[1], list)

        if is_shorthand_func_def:
            # print("is short hand function def")

            func_name = tree[1][0]
            parameters = tree[1][1:]
            body = tree[2]

            # print("parameters")
            # print(parameters)

            # print(func_name, parameters, body)

            func = create_function(parameters, body, env)

            # print(func)

            return assignment(func_name, func, env)

        # get parts from assignment expression
        _, variable, expression = tree

        evaluated_expression = evaluate(expression, env)

        # set variable binding
        return assignment(variable, evaluated_expression, env)
    elif keyword == "function":
        # get parameters and body of function
        _, parameters, body = tree

        return create_function(parameters, body, env)

    # evaluate each expression in the tree
    evaluated_expressions = [evaluate(expression, env) for expression in tree]

    # check if first evaluated expression is a function
    func = evaluated_expressions[0]

    # check if it's a CarlaeFunction
    if isinstance(func, CarlaeFunction):
        # print("is a carlae function")

        # print(evaluated_expressions)

        if len(evaluated_expressions) == 1:
            # function with no arguments
            return func.call([])

        # get the args
        # [] if evaluated_expressions[1] == [] else evaluated_expressions[1:]

        args = evaluated_expressions[1:]

        # args = [] if evaluated_expressions[1] == [] else evaluated_expressions[1:]

        # print("ed shit happened")

        # print(args)
        # print(args)

        # print(args)

        # call the function on the args
        return func.call(args)

    # if length of evaluated expressions is 1 return that value
    if len(evaluated_expressions) == 1:
        return evaluated_expressions[0]

    if not callable(func):
        raise CarlaeEvaluationError()

    # call the func on rest of evaluated expressions
    evaluated = func(evaluated_expressions[1:])

    return evaluated


def result_and_env(tree, env=None):
    # initialize environment for evaluation
    current_env = _create_env(env)
    evaluated = evaluate(tree, current_env)

    return evaluated, current_env


def run_carlae(raw_carlae_str, env=None):
    tokens = tokenize(raw_carlae_str)
    parsed = parse(tokens)
    evaluated = result_and_env(parsed, env)

    return evaluated[0]


def run_repl():
    builtins = Environment(carlae_builtins)
    global_env = Environment({}, builtins)

    while True:
        raw_carlae_str = input("in> ")

        if raw_carlae_str == "EXIT":
            break

        try:
            value = run_carlae(raw_carlae_str, global_env)
            print(f"out> {value}")

            # print(global_env)

        except Exception as e:
            exception_name = e.__class__.__name__
            print(exception_name)


if __name__ == "__main__":
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)

    # uncommenting the following line will run doctests from above
    # doctest.testmod()

    # run_repl()

    builtins = Environment(carlae_builtins)
    global_env = Environment({}, builtins)

    # print(global_env)
    # print(builtins)

    a = run_carlae("(:= ham 42)", global_env)
    print(a)

    a = run_carlae(
        "(:= bacon (function (var100) ((function (var99) ((function (var98) ((function (var97) ((function (var96) ((function (var95) ((function (var94) ((function (var93) ((function (var92) ((function (var91) ((function (var90) ((function (var89) ((function (var88) ((function (var87) ((function (var86) ((function (var85) ((function (var84) ((function (var83) ((function (var82) ((function (var81) ((function (var80) ((function (var79) ((function (var78) ((function (var77) ((function (var76) ((function (var75) ((function (var74) ((function (var73) ((function (var72) ((function (var71) ((function (var70) ((function (var69) ((function (var68) ((function (var67) ((function (var66) ((function (var65) ((function (var64) ((function (var63) ((function (var62) ((function (var61) ((function (var60) ((function (var59) ((function (var58) ((function (var57) ((function (var56) ((function (var55) ((function (var54) ((function (var53) ((function (var52) ((function (ham) ((function (var50) ((function (var49) ((function (var48) ((function (var47) ((function (var46) ((function (var45) ((function (var44) ((function (var43) ((function (var42) ((function (var41) ((function (var40) ((function (var39) ((function (var38) ((function (var37) ((function (var36) ((function (var35) ((function (var34) ((function (var33) ((function (var32) ((function (var31) ((function (var30) ((function (var29) ((function (var28) ((function (var27) ((function (var26) ((function (var25) ((function (var24) ((function (var23) ((function (var22) ((function (var21) ((function (var20) ((function (var19) ((function (var18) ((function (var17) ((function (var16) ((function (var15) ((function (var14) ((function (var13) ((function (var12) ((function (var11) ((function (var10) ((function (var9) ((function (var8) ((function (var7) ((function (var6) ((function (var5) ((function (var4) ((function (var3) ((function (var2) ((function (var1) ((function (var0) ham) 0)) 1)) 2)) 3)) 4)) 5)) 6)) 7)) 8)) 9)) 10)) 11)) 12)) 13)) 14)) 15)) 16)) 17)) 18)) 19)) 20)) 21)) 22)) 23)) 24)) 25)) 26)) 27)) 28)) 29)) 30)) 31)) 32)) 33)) 34)) 35)) 36)) 37)) 38)) 39)) 40)) 41)) 42)) 43)) 44)) 45)) 46)) 47)) 48)) 49)) 50)) (function (x) (+ x x x)))) 52)) 53)) 54)) 55)) 56)) 57)) 58)) 59)) 60)) 61)) 62)) 63)) 64)) 65)) 66)) 67)) 68)) 69)) 70)) 71)) 72)) 73)) 74)) 75)) 76)) 77)) 78)) 79)) 80)) 81)) 82)) 83)) 84)) 85)) 86)) 87)) 88)) 89)) 90)) 91)) 92)) 93)) 94)) 95)) 96)) 97)) 98)) 99)))",
        global_env,
    )

    print(a)

    a = run_carlae("((bacon 7) 19)", global_env)

    print(a)
