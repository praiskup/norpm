#! /usr/bin/python3

"""
Parse RPM expressions.
"""

from ply.lex import lex
from ply.yacc import yacc


tokens = [
    'NUMBER', 'STRING',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'AND','OR', 'NOT',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
    'LPAREN', 'RPAREN',
]


# pylint: disable=invalid-name
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_AND     = r'&&'
t_OR      = r'\|\|'
t_LE      = r'<='
t_LT      = r'<'
t_GE      = r'>='
t_GT      = r'>'
t_EQ      = r'=='
t_NE      = r'!='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_NOT     = r'!'

t_ignore = ' \t'


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_STRING(t):
    r'"([^\\\n]|(\\.))*?"'
    t.value = t.value[1:-1]  # Remove surrounding quotes
    return t


def t_error(t):
    "lexer error"
    raise SyntaxError(f"Illegal character '{t.value[0]}'")


def p_error(p):
    "parser error"
    raise SyntaxError(f"Syntax error at '{p.value}'")


lexer = lex()


precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('nonassoc', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'NOT'),
    ('right', 'UMINUS'),
)


def p_expression(p):
    'expression : expr'
    p[0] = p[1]


def p_expr_binop(p):
    """
    expr : expr PLUS expr
         | expr MINUS expr
         | expr TIMES expr
         | expr DIVIDE expr
    """
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        p[0] = p[1] // p[3]


def p_expr_comp(p):
    """
    expr : expr LT expr
         | expr LE expr
         | expr GT expr
         | expr GE expr
         | expr EQ expr
         | expr NE expr
    """
    ops = {'<': p[1] < p[3], '<=': p[1] <= p[3],
           '>': p[1] > p[3], '>=': p[1] >= p[3],
           '==': p[1] == p[3], '!=': p[1] != p[3]}
    p[0] = 1 if ops[p[2]] else 0


def p_expr_logic(p):
    """
    expr : expr AND expr
         | expr OR expr
    """
    if p[2] == '&&':
        p[0] = 1 if (p[1] and p[3]) else 0
    else:
        p[0] = 1 if (p[1] or p[3]) else 0


def p_expr_uminus(p):
    'expr : MINUS expr %prec UMINUS'
    p[0] = -p[2]


def p_expr_group(p):
    'expr : LPAREN expr RPAREN'
    p[0] = p[2]


def p_expr_number(p):
    'expr : NUMBER'
    p[0] = p[1]

def p_expr_string(p):
    'expr : STRING'
    p[0] = p[1]

def p_expr_not(p):
    'expr : NOT expr'
    p[0] = 1 if not p[2] else 0


parser = yacc(debug=False, write_tables=False, optimize=True)


def eval_rpm_expr(text: str) -> int:
    """
    Evaluate RPM-style expression
    """
    return parser.parse(text, lexer=lexer)
