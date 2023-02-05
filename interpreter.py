import os

from error import RTError
from token_ import TokenType

KEYWORDS = ["VAR", "AND", "OR", "NOT", "IF",
            "THEN", "ELSE", "ELIF", "FOR", "TO", "STEP", "WHILE", "FUN", "END"]


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


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_context(self, context=None):
        self.context = context
        return self

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def illegal_operation(self, other):
        if not other: other = self
        return RTError(
            other.pos_start, other.pos_end,
            "Illegal operation",
            self.context
        )


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, 'Division by zero', self.context)
            return Number(self.value / other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def neq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None

        else:
            return None, Value.illegal_operation(self, other)

    def gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                           other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                           other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def and_(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                             other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def notted(self):
        return Number(int(not self.value)).set_context(self.context).set_pos(self.pos_start,
                                                                             self.pos_end), None

    def or_(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context).set_pos(self.pos_start,
                                                                                            other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)


class BaseFunction(Value):
    def __int__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        res = RTResult()
        if len(args) > len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(arg_names)} too many args passed into '{self.name}'",
                self.context
            ))
        if len(args) < len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(arg_names) - len(args)} too few args passed into '{self.name}'",
                self.context
            ))
        return res.success(None)

    def populate_args(self, arg_names, args, exec_ctx):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(exec_ctx)
            exec_ctx.symbol_table.set(arg_name, arg_value)
        return exec_ctx

    def check_and_populate_args(self, arg_names, args, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.error: return res
        self.populate_args(arg_names, args, exec_ctx)
        return res.success(None)


class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_return_null):
        super().__init__()
        self.name = name or "<anonymous>"
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_return_null = should_return_null

    def execute(self, args):
        res = RTResult()
        interpreter = Interpreter()
        exec_context = self.generate_new_context()
        self.check_and_populate_args(self.arg_names, args, exec_context)

        value = res.register(interpreter.interpret(self.body_node, exec_context))
        if res.error: return res
        return res.success(Number.null if self.should_return_null else value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names, self.should_return_null)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def execute(self, args):
        res = RTResult()
        exe_ctx = self.generate_new_context()
        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)
        res.register(self.check_and_populate_args(method.arg_names, args, exe_ctx))
        if res.error: return res
        return_value = res.register(method(exe_ctx))
        if res.error: return res
        return res.success(return_value)

    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined')

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def execute_print(self, exec_ctx):
        print(str(exec_ctx.symbol_table.get('value')))
        return RTResult().success(Number.null)

    execute_print.arg_names = ['value']

    def execute_print_ret(self, exec_ctx):
        return RTResult().success(str(exec_ctx.symbol_table.get('value')))

    execute_print_ret.arg_names = ['value']

    def execute_input(self, exec_ctx):
        text = input()
        return RTResult().success(String(text))

    execute_input.arg_names = []

    def execute_input_int(self, exec_ctx):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except:
                pass
        return RTResult().success(Number(number))

    execute_input_int.arg_names = []

    def execute_clear(self, exec_ctx):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RTResult().success(Number.null)

    execute_clear.arg_names = []

    def execute_is_number(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get('value'), Number)
        return RTResult().success(Number.true if is_number else Number.false)

    execute_is_number.arg_names = ['value']

    def execute_is_string(self, exec_ctx):
        is_string = isinstance(exec_ctx.symbol_table.get('value'), String)
        return RTResult().success(Number.true if is_string else Number.false)

    execute_is_string.arg_names = ['value']

    def execute_is_list(self, exec_ctx):
        is_list = isinstance(exec_ctx.symbol_table.get('value'), ListValue)
        return RTResult().success(Number.true if is_list else Number.false)

    execute_is_list.arg_names = ['value']

    def execute_is_function(self, exec_ctx):
        is_function = isinstance(exec_ctx.symbol_table.get('value'), BaseFunction)
        return RTResult().success(Number.true if is_function else Number.false)

    execute_is_function.arg_names = ['value']

    def execute_append(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get('list')
        value = exec_ctx.symbol_table.get('value')
        if not isinstance(list_, ListValue):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))
        list_.elements.append(value)
        return RTResult().success(Number.null)

    execute_append.arg_names = ['list', 'value']

    def execute_pop(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get('list')
        index = exec_ctx.symbol_table.get('index')
        if not isinstance(list_, ListValue):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))
        if not isinstance(index, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be number",
                exec_ctx
            ))
        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Element at index could not be removed from list, either because index is out of bounds or the list is empty",
                exec_ctx
            ))
        return RTResult().success(element)

    execute_pop.arg_names = ['list', 'index']

    def execute_extend(self, exec_ctx):
        list_a = exec_ctx.symbol_table.get('list_a')
        list_b = exec_ctx.symbol_table.get('list_b')
        if not isinstance(list_a, ListValue):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))
        if not isinstance(list_b, ListValue):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be list",
                exec_ctx
            ))
        list_a.elements.extend(list_b.elements)
        return RTResult().success(Number.null)

    execute_extend.arg_names = ['list_a', 'list_b']

    def __repr__(self):
        return f"<built-in function {self.name}>"


BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
BuiltInFunction.is_number = BuiltInFunction("is_number")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_list = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append = BuiltInFunction("append")
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend")


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context).set_pos(self.pos_start,
                                                                                      other.pos_end), None
        else:
            return None, Value.illegal_operation(self, other)

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    def __str__(self):
        return self.value

    def __repr__(self):
        return f'"{self.value}"'


class ListValue(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def added_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def multed_by(self, other):
        if isinstance(other, ListValue):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            try:
                new_list = self.copy()
                new_list.elements.pop(other.value)
                return new_list, None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    "Element at this index could not be removed from list, because index is out of bounds",
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    "Element at this index could not be retrieved from list, because index is out of bounds",
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = ListValue(self.elements)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __str__(self):
        return f"{', '.join([str(x) for x in self.elements])}"

    def __repr__(self):
        return f"[{', '.join([str(x) for x in self.elements])}]"


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

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
        value = value.copy().set_context(context).set_pos(node.pos_start, node.pos_end)
        return res.success(value)

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_IfNode(self, node, context):
        res = RTResult()
        for condition, expr, should_return_null in node.cases:
            condition_value = res.register(self.interpret(condition, context))
            if res.error:
                return res
            if condition_value.value:
                expr_value = res.register(self.interpret(expr, context))
                if res.error:
                    return res
                return res.success(Number.null if should_return_null else expr_value)
        if node.else_case:
            expr, should_return_null = node.else_case
            else_value = res.register(self.interpret(expr, context))
            if res.error:
                return res
            return res.success(Number.null if should_return_null else else_value)
        return res.success(Number.null)

    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []
        for element_node in node.element_nodes:
            elements.append(res.register(self.interpret(element_node, context)))
            if res.error:
                return res
        return res.success(
            ListValue(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

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

    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []
        start = res.register(self.interpret(node.start_value_node, context))
        if res.error: return res
        end = res.register(self.interpret(node.end_value_node, context))
        if res.error: return res
        context.symbol_table.set(node.var_name_tok.value, Number(start))
        step = res.register(
            self.interpret(node.step_value_node, context) if node.step_value_node else RTResult().success(Number(1)))
        if res.error: return res
        final_res = None
        print(start, end, step)
        for x in range(start.value, end.value, step.value):
            context.symbol_table.set(node.var_name_tok.value, Number(x))
            final_res = res.register(self.interpret(node.body_value_node, context))
            elements.append(final_res)
            if res.error: return res
        context.symbol_table.remove(node.var_name_tok.value)
        return res.success(
            Number.null if node.should_return_null else
            ListValue(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_WhileNode(self, node, context):
        res = RTResult()
        val = res.register(self.interpret(node.condition_node, context))
        if res.error: return res
        final_res = None
        elements = []
        while val.value:
            final_res = res.register(self.interpret(node.body_node, context))
            if res.error: return res
            val = res.register(self.interpret(node.condition_node, context))
            elements.append(val)
        return res.success(
            Number.null if node.should_return_null else
            ListValue(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_FuncDefNode(self, node, context):
        res = RTResult()
        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = Function(func_name, body_node, arg_names, node.should_return_null).set_context(context).set_pos(node.pos_start,
                                                                                            node.pos_end)
        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)
        return res.success(func_value)

    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []
        value_to_call = res.register(self.interpret(node.node_to_call, context))
        if res.error:
            return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)
        for arg_node in node.arg_nodes:
            args.append(res.register(self.interpret(arg_node, context)))
            if res.error:
                return res
        return_value = res.register(value_to_call.execute(args))
        if res.error: return res
        return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(return_value)

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
