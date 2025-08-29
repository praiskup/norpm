"""
Parse RPM expressions.
"""

import operator
from ply.lex import lex
from ply.yacc import yacc

from norpm.versions import rpmevrcmp


tokens = [
    'VERSION', 'NUMBER', 'STRING',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'AND','OR', 'NOT',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
    'LPAREN', 'RPAREN',
    'QUESTION', 'COLON',
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
t_QUESTION = r'\?'
t_COLON = r':'

t_ignore = ' \t\n'


def t_NUMBER(t):
    r'(\d|@\d+@)+'
    orig_value = t.value
    def _expanding_value(expander=None):
        if expander:
            expanded = expander(orig_value)
            if not expanded:
                return 0
            return int(expanded)
        return int(orig_value)
    t.value = _expanding_value
    return t


def t_VERSION(t):
    r'v"([^\\\n]|(\\.))*?"'
    t.value = t.value[2:-1]  # Remove surrounding quotes
    orig_value = t.value
    def _expanding_value(expander=None):
        if expander:
            return expander(orig_value)
        return orig_value
    t.value = _expanding_value
    return t


def t_STRING(t):
    r'"([^\\\n]|(\\.))*?"'
    t.value = t.value[1:-1]  # Remove surrounding quotes
    orig_value = t.value

    def _expanding_value(expander=None):
        if expander:
            return expander(orig_value)
        return orig_value

    t.value = _expanding_value
    return t


def t_error(t):
    "lexer error"
    raise SyntaxError(f"Illegal character '{t.value[0]}'")


def p_error(p):
    "parser error"
    raise SyntaxError(f"Syntax error at '{p.value}'")


lexer = lex()


precedence = (
    ('right', 'QUESTION', 'COLON'),
    ('left', 'AND'),
    ('left', 'OR'),
    ('left', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'NOT'),
    ('right', 'UMINUS'),
)


def p_expression_ternary(p):
    'expression : expression QUESTION expression COLON expression'
    expr = p[1]
    lhs = p[3]
    rhs = p[5]
    p[0] = lambda x=None: lhs(x) if expr(x) else rhs(x)


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
    lhs = p[1]
    rhs = p[3]
    if p[2] == '+':
        p[0] = lambda x=None: lhs(x) + rhs(x)
    elif p[2] == '-':
        p[0] = lambda x=None: lhs(x) - rhs(x)
    elif p[2] == '*':
        p[0] = lambda x=None: lhs(x) * rhs(x)
    elif p[2] == '/':
        p[0] = lambda x=None: lhs(x) // rhs(x)


def p_expr_comp(p):
    """
    expr : expr LT expr
         | expr LE expr
         | expr GT expr
         | expr GE expr
         | expr EQ expr
         | expr NE expr
    """
    lhs = p[1]
    rhs = p[3]
    op = {
        '==': operator.eq,
        '!=': operator.ne,
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
    }[p[2]]
    p[0] = lambda x=None: int(op(lhs(x), rhs(x)))


def p_expr_logic(p):
    """
    expr : expr AND expr
         | expr OR expr
    """
    lhs = p[1]
    rhs = p[3]
    if p[2] == '&&':
        p[0] = lambda x=None: lhs(x) and rhs(x)
    else:
        p[0] = lambda x=None: lhs(x) or rhs(x)


def p_expr_uminus(p):
    'expr : MINUS expr %prec UMINUS'
    num = p[2]
    p[0] = lambda x=None: -num(x)


def p_expr_group(p):
    'expr : LPAREN expr RPAREN'
    p[0] = p[2]


def p_expr_number(p):
    'expr : NUMBER'
    p[0] = p[1]

def p_expr_string(p):
    'expr : STRING'
    p[0] = p[1]


def p_expr_version(p):
    """
    expr : VERSION LT VERSION
         | VERSION LE VERSION
         | VERSION GT VERSION
         | VERSION GE VERSION
         | VERSION EQ VERSION
         | VERSION NE VERSION
    """
    lhs = p[1]
    rhs = p[3]
    op = p[2]

    def _compare_versions(expander=None):
        result = rpmevrcmp(lhs(expander), rhs(expander))

        if result == 0 and op in ["==", ">=", "<="]:
            return 1
        if result == -1 and op in ["<", "<=", "!="]:
            return 1
        if result == 1 and op in [">", ">=", "!="]:
            return 1
        return 0

    p[0] = _compare_versions


def p_expr_not(p):
    'expr : NOT expr'
    expr = p[2]
    p[0] = lambda x=None: int(not expr(x))


parser = yacc(debug=False, write_tables=False, optimize=True)


def eval_rpm_expr(text: str, expander=None):
    """
    Evaluate RPM-style expression
    """
    tree = parser.parse(text, lexer=lexer)
    return tree(expander)
