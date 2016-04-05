import mathlib as ml
import parsing
from modules.ieuler.lib import *
import re
from pyparsing import *
from importlib import import_module

ParserElement.enablePackrat()  # Vastly improves pyparsing performance


def get_variable_value(toks):
    var, op = parsing.parse_unary_operator(toks)
    if type(var) is ml.Variable:
        if var.value in user_variables:
            return user_variables[var.value]
    if type(var) is ml.Ans:
        return var.value
    return var


def get_decorator(toks):
    value, op = parsing.parse_unary_operator(toks)
    if type(value) is ml.Unit:
        value = value.convert_to_variable()
    value.add_decorator(op)
    return value


def get_equality_op(toks):
    t = toks[0]
    value1, value2, op = parsing.parse_binary_operator(
        toks, get_equality_op)
    hidden = False
    assignment = False
    if "equals" in t:
        type = "="
        if t["equals"]["modifier"]:
            if "#" in t["equals"]["modifier"]:
                value2 = evaluate_expression(value2, t["equals"]["option"])
            if "::" in t["equals"]["modifier"]:
                hidden = True
                if evaluate:
                    assign_variable(value1, value2)
            elif ":" in t["equals"]["modifier"]:
                if evaluate:
                    assign_variable(value1, value2)
    else:
        type = op[0]

    return ml.Equality(type, value1, value2, assignment, hidden)


def assign_variable(variable, value):
    global user_variables
    if type(variable) is ml.Equality:
        variable = variable.get_first()
    if type(variable) is ml.Unit:
        variable = variable.convert_to_variable()
    if type(variable) is ml.Variable:
        user_variables[variable.value] = value
    else:
        raise NameError(
            'Can only assign variables, not {}!'.format(type(variable)))


def evaluate_expression(expr, calculator="", convert=True):
    if evaluate:
        if not calculator:
            calculator = workspace["default_calculator"]
        return import_module("modules.{}.process".format(calculator)).evaluate(expr, convert)
    return expr


ParserElement.setDefaultWhitespaceChars(' ')

deco_kw_list = parsing.make_keyword_list(decorator_keywords)
equality_kw_list = parsing.make_keyword_list(equality_keywords)
units_list = oneOf(units)
unit_prefixes_list = oneOf(unit_prefixes)


expression = Forward()

unit = Optional(Word(nums).setParseAction(parsing.get_value)) + Suppress(Literal(unit_escape_character) + parsing.no_white) + (
    units_list + NotAny(parsing.no_white + Word(parsing.chars)) | (
        Optional(unit_prefixes_list + parsing.no_white) + units_list +
        NotAny(parsing.no_white + Word(parsing.chars)))
) + NotAny(parsing.no_white + Literal(unit_escape_character))

name = NotAny(deco_kw_list | equality_kw_list | Keyword('cross')) + Word(
    parsing.letters, parsing.chars)

variable = Forward()
number = Forward()

ans = Literal('ans') + Optional(~White() + Word(nums))

variable << name + Optional(parsing.no_white + Literal('_') + parsing.no_white
                            + (variable | number))

function = Combine(name + Suppress("(")) + \
    delimitedList(expression, delim=',') + Suppress(")")

matrix = Suppress(oneOf(matrix_delimiters["start"]) + Optional(White())) + expression + ZeroOrMore(oneOf(matrix_delimiters[
    "horizontal"] + matrix_delimiters["vertical"]) + NotAny(oneOf(matrix_delimiters["end"])) + expression) + Suppress(Optional(White()) + oneOf(matrix_delimiters["end"]))

number << (Combine(Word(nums) + Optional("." + NotAny(Literal('.')) + Optional(Word(nums)))) +
           Optional(NotAny(White()) + (function | unit | variable)))

eval_field = Suppress('#') + expression + Suppress('#')

eval_direct_field = Suppress('$') + expression + Suppress('$')

operand = (
    eval_field.setParseAction(lambda x: evaluate_expression(x[0]))
    | eval_direct_field.setParseAction(
        lambda x: evaluate_expression(x[0], False))
    | function.setParseAction(lambda x: parsing.get_function(x, functions))
    | unit.setParseAction(lambda x: parsing.get_unit(x, user_variables))
    | ans.setParseAction(lambda x: parsing.get_ans(x, workspace))
    | variable.setParseAction(
        lambda x: parsing.get_variable(x, variables, symbols))
    | matrix.setParseAction(lambda x: parsing.get_matrix(x, matrix_delimiters))
    | number.setParseAction(parsing.get_value)
)

insert_value = parsing.word_start + Literal('@') + parsing.no_white
factop = parsing.no_white + Literal('!') + parsing.word_end
signop = parsing.word_start + Literal('-') + parsing.no_white
expop = Literal('^')
fracop = Literal('/')
multop1 = parsing.space.copy()
multop2 = Literal('*')
crossop = Keyword('cross')
rangeop = Literal('..')
plusop = oneOf('+ -')
equals = Group(Regex(
    r'((?P<modifier>[:#])+(?P<option>[a-zA-Z]*))?=')).setResultsName(
        "equals")
other_equals = oneOf('== <= >= < > ~~ ~ ~= ~== !=')
equalop = Group(other_equals) | equals | Group(equality_kw_list)

right = opAssoc.RIGHT
left = opAssoc.LEFT
expression << infixNotation(operand, [
    (insert_value, 1, right, get_variable_value),
    (factop, 1, left, parsing.get_factorial_op),
    (deco_kw_list, 1, right, get_decorator),
    (signop, 1, right, parsing.get_minus_op),
    (expop, 2, right, parsing.get_pow_op),
    (fracop, 2, left, parsing.get_div_op),
    (crossop, 2, left, parsing.get_cross_op),
    (multop1, 2, left, parsing.get_mul_op),
    (multop2, 2, left, parsing.get_mul_op),
    (plusop, 2, left, parsing.get_add_op),
    (rangeop, 2, left, parsing.get_range_op),
    (equalop, 2, left, get_equality_op)
])
expression.parseWithTabs()


def parse(text, eval, worksp):
    # print(workspace)
    global workspace
    global user_variables
    global evaluate
    evaluate = eval
    workspace = worksp
    user_variables = worksp["user_variables"]
    return expression.parseString(text)[0]
