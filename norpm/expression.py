"""
Parse RPM expressions using Lark.
"""

import operator
from lark import Lark, Transformer, v_args, LarkError

from norpm.versions import rpmevrcmp
from norpm.exceptions import NorpmSyntaxError


_EXPR_GRAMMAR = r"""
?start: expression

?expression: logical_or
           | logical_or "?" expression ":" expression -> op_ternary

?logical_or: logical_and
           | logical_or "||" logical_and     -> op_or

?logical_and: comparison
            | logical_and "&&" comparison    -> op_and

?comparison: math_expr
           | math_expr OP_CMP math_expr      -> op_cmp
           | version   OP_CMP version        -> op_vercmp

?math_expr: term
          | math_expr OP_ADD term            -> op_math

?term: factor
     | term OP_MUL factor                    -> op_math

?factor: "-" factor                          -> op_neg
       | "!" factor                          -> op_not
       | "(" expression ")"
       | NUMBER                              -> t_number
       | STRING                              -> t_string

?version: VERSION                            -> t_version

VERSION: /v"([^"\\\n]|\\.)*"/
STRING:  /"([^"\\\n]|\\.)*"/
NUMBER:  /(\d|@\d+@)+/

// lexically greedy; short operators must be specified last
OP_CMP: "<=" | ">=" | "==" | "!=" |"<" | ">"
OP_ADD: "+" | "-"
OP_MUL: "*" | "/"

%import common.WS
%ignore WS
"""


@v_args(inline=True)
class _RPMExprTransformer(Transformer):
    """
    Transform RPM expression AST
    """
    def __init__(self, expander=None):
        super().__init__()
        self.expander = expander

    def _safe_int(self, val):
        if not val:
            return 0
        return int(val)

    def _expand(self, value):
        if self.expander:
            return self.expander(value)
        return value

    def t_number(self, value):
        """
        Get integer number
        """
        return lambda: self._safe_int(self._expand(value))

    def t_string(self, value):
        """
        Expand strings, e.g., "Hello world".
        """
        return lambda: self._expand(value[1:-1])

    def t_version(self, value):
        """
        Extract version strings, e.g., v"1.2".
        """
        return lambda: self._expand(value[2:-1])

    def op_math(self, lhs, op, rhs):
        """
        Normal math operators.
        """
        lhs = lhs()
        rhs = rhs()
        if isinstance(lhs, str) or isinstance(rhs, str):
            if op != '+':
                raise NorpmSyntaxError(f"Don't use '{op}' for strings")
            return lambda: lhs + rhs
        return lambda: {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.floordiv,
        }[op](lhs, rhs)

    def op_neg(self, factor):
        """
        Unary minus
        """
        return lambda: -self._safe_int(factor())

    def op_and(self, lhs, rhs):
        """Logical &&"""
        def _and_cb():
            lval = lhs()
            if not lval:
                return lval
            return rhs()
        return _and_cb

    def op_or(self, lhs, rhs):
        """Logical ||"""
        def _comparator():
            lval = lhs()
            if lval:
                return lval
            return rhs()
        return _comparator

    def op_not(self, factor):
        """Logical negation, !bool"""
        return lambda: 1 if not factor() else 0

    def op_ternary(self, condition, lhs, rhs):
        """Ternary op: condition ? lhs : rhs"""
        def _op():
            if condition():
                return lhs()
            return rhs()
        return _op

    def op_cmp(self, lhs, op, rhs):
        """Number/string comparisons"""
        def _comparator():
            the_op = {
                '==': operator.eq,
                '!=': operator.ne,
                '<': operator.lt,
                '<=': operator.le,
                '>': operator.gt,
                '>=': operator.ge,
            }[op]
            lhsv = lhs()
            rhsv = rhs()
            return int(the_op(lhsv, rhsv))

        return _comparator

    def op_vercmp(self, lhs, op, rhs):
        """Version comparisons"""
        def _comparator():
            lhsv = lhs()
            rhsv = rhs()
            result = rpmevrcmp(lhsv, rhsv)
            if result == 0 and op in ["==", ">=", "<="]:
                return 1
            if result == -1 and op in ["<", "<=", "!="]:
                return 1
            if result == 1 and op in [">", ">=", "!="]:
                return 1
            return 0
        return _comparator


# Instantiate just once.
_parser = Lark(_EXPR_GRAMMAR, parser='lalr')


def eval_rpm_expr(text: str, expander=None):
    """
    Evaluate RPM-style expression
    """
    try:
        tree = _parser.parse(text)
        return _RPMExprTransformer(expander).transform(tree)()
    except LarkError as e:
        raise NorpmSyntaxError(f"Expression parser error: {e}") from e
