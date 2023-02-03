from error import RTError
from token_ import TokenType

KEYWORDS = ["VAR", "AND", "OR", "NOT", "IF", "THEN", "ELSE", "ELIF"]


class RTResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        if res.error:
            self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


class Number:
    def __init__(self, value):
        self.value = value
        self.set_pos()
        self.set_context(None)

    def set_context(self, context):
        self.context = context
        return self

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None

    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, 'Division by zero', self.context)
            return Number(self.value / other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
    def eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                           other.pos_end), None
    def neq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None
    def gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None

    def gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                           other.pos_end), None
    def lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None

    def lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                           other.pos_end), None

    def and_(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None

    def notted(self):
        return Number(int(not self.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                             self.pos_end), None
    def or_(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                             other.pos_end), None

    def __repr__(self):
        return str(self.value)


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def get(self, name):
        value = self.symbols.get(name, None)
        if value is None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


class Interpreter:

    def interpret(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)
        if not value:
            return res.failure(RTError(
                node.pos_start, node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))
        return res.success(value)

    def visit_IfNode(self, node, context):
        res = RTResult()
        for condition, expr in node.cases:
            condition_value = res.register(self.interpret(condition, context))
            if res.error:
                return res
            if condition_value.value:
                expr_value = res.register(self.interpret(expr, context))
                if res.error:
                    return res
                return res.success(expr_value)
        if node.else_case:
            else_value = res.register(self.interpret(node.else_case, context))
            if res.error:
                return res
            return res.success(else_value)
        return res.success(0)

    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_token.value
        value = res.register(self.interpret(node.value_node, context))
        if res.error:
            return res
        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_NumberNode(self, node, context):

        return RTResult().success(
            Number(node.token.value).set_context(context).set_pos(node.token.pos_start, node.token.pos_end))

    def visit_BinOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.interpret(node.left_node, context))
        if res.error: return res
        right = res.register(self.interpret(node.right_node, context))
        if res.error: return res
        if node.op_token.type == TokenType.PLUS:
            result, error = left.added_to(right)
        elif node.op_token.type == TokenType.MINUS:
            result, error = left.subbed_by(right)
        elif node.op_token.type == TokenType.MULTIPLY:
            result, error = left.multed_by(right)
        elif node.op_token.type == TokenType.DIVIDE:
            result, error = left.dived_by(right)
        elif node.op_token.type == TokenType.EEQ:
            result, error = left.eq(right)
        elif node.op_token.type == TokenType.NE:
            result, error = left.neq(right)
        elif node.op_token.type == TokenType.LT:
            result, error = left.lt(right)
        elif node.op_token.type == TokenType.GT:
            result, error = left.gt(right)
        elif node.op_token.type == TokenType.LTE:
            result, error = left.lte(right)
        elif node.op_token.type == TokenType.GTE:
            result, error = left.gte(right)
        elif node.op_token.matches(TokenType.KEYWORD, 'AND'):
            result, error = left.and_(right)
        elif node.op_token.matches(TokenType.KEYWORD, 'OR'):
            result, error = left.or_(right)
        if error:
            return res.failure(error)
        return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.interpret(node.node, context))
        if res.error: return res
        error = None
        if node.op_token.type == TokenType.MINUS:
            number, error = number.multed_by(Number(-1))
        elif node.op_token.matches(TokenType.KEYWORD, 'NOT'):
            number, error = number.notted()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))
