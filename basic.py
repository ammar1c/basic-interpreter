from enum import Enum
from string_with_arrows import string_with_arrows


class TokenType(Enum):
    INT = 0
    FLOAT = 1
    PLUS = 2
    MINUS = 3
    MULTIPLY = 4
    DIVIDE = 5
    LPAREN = 6
    RPAREN = 7
    EOF = 8
    KEYWORD = 9
    EQUALS = 10
    IDENTIFIER = 11


KEYWORDS = ["VAR"]


class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.error_name = error_name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end

    def as_string(self):
        result = f"{self.error_name}: {self.details} \n"
        result += f'File {self.pos_start.file_name}, line {self.pos_start.line + 1}'
        result += "\n\n " + string_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Invalid Syntax", details)


class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        result += "\n\n" + string_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx = self.context
        while ctx:
            result = f' File {pos.file_name}, line {str(pos.line + 1)}, in {ctx.display_name} \n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent
        return "Traceback (most recent call last): \n" + result


class Position:
    def __init__(self, index, line, column, file_name, file_text):
        self.index = index
        self.line = line
        self.column = column
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char=None):
        self.index += 1
        self.column += 1
        if current_char == '\n':
            self.line += 1
            self.column = 0

    def copy(self):
        return Position(self.index, self.line, self.column, self.file_name, self.file_text)


class Token:
    def __init__(self, type, value=None, pos_start=None, pos_end=None):
        self.type = type
        self.value = value
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end

    def __repr__(self):
        return f"{self.type}" + (f":{self.value}" if self.value != None else "")


class Lexer:
    def __init__(self, filename, text):
        self.filename = filename
        self.text = text
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance()
        if self.pos.index >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos.index]

    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TokenType.INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TokenType.FLOAT, float(num_str), pos_start, self.pos)

    def make_tokens(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char in " \t":
                self.advance()
            elif self.current_char.isdigit():
                tokens.append(self.make_number())
            elif self.current_char.isalpha():
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TokenType.PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TokenType.MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TokenType.MULTIPLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TokenType.DIVIDE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '=':
                tokens.append(Token(TokenType.EQUALS, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        tokens.append(Token(TokenType.EOF, pos_start=self.pos))
        return tokens, None

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()
        while self.current_char is not None and self.current_char.isalnum():
            id_str += self.current_char
            self.advance()
        tok_type = TokenType.KEYWORD if id_str in KEYWORDS else TokenType.IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)


class NumberNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f"{self.token}"


class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end

    def __repr__(self):
        return f"{self.var_name_token}"


class VarAssignNode:
    def __init__(self, var_name_token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.value_node.pos_end

    def __repr__(self):
        return f"{self.var_name_token} = {self.value_node}"


class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.op_token}, {self.right_node})"


class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node
        self.pos_start = self.op_token.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f"({self.op_token}, {self.node})"


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error:
                self.error = res.error
            return res.node
        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        self.advance()

    def advance(self):
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        return self.current_token

    def factor(self):
        res = ParseResult()
        toke = self.current_token

        if toke.type == TokenType.IDENTIFIER:
            res.register(self.advance())
            return res.success(VarAccessNode(toke))
        if toke.type in (TokenType.PLUS, TokenType.MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(toke, factor))
        elif toke.type == TokenType.INT or toke.type == TokenType.FLOAT:
            res.register(self.advance())
            return res.success(NumberNode(toke))
        elif toke.type == TokenType.LPAREN:
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_token.type == TokenType.RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ')'"
                ))
        return res.failure(InvalidSyntaxError(toke.pos_start, toke.pos_end, "Expected int or float"))

    def term(self):
        return self.bin_op(self.factor, (TokenType.MULTIPLY, TokenType.DIVIDE))

    def matches(self, type_, value):
        return self.current_token.type == type_ and self.current_token.value == value

    def expr(self):
        res = ParseResult()
        if self.matches(TokenType.KEYWORD, 'VAR'):
            res.register(self.advance())
            if self.current_token.type != TokenType.IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected identifier"
                ))
            var_name = self.current_token
            res.register(self.advance())
            if self.current_token.type != TokenType.EQUALS:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected '='"
                ))
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr))
        return self.bin_op(self.term, (TokenType.PLUS, TokenType.MINUS))

    def bin_op(self, func_a, ops):
        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res
        while self.current_token.type in ops:
            op_token = self.current_token
            res.register(self.advance())
            right = res.register(func_a())
            if res.error: return res
            left = BinOpNode(left, op_token, right)
        return res.success(left)

    def parse(self):
        res = self.expr()
        if not res.error and self.current_token.type != TokenType.EOF:
            return res.failure(
                InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected +-*/"))
        return res


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
        if error:
            res.failure(error)
        else:
            res.success(number.set_pos(node.pos_start, node.pos_end))

global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number(0))

def run(filename, text):
    lexer = Lexer(filename, text)
    tokens, error = lexer.make_tokens()

    if error:
        return None, error
    print(tokens)
    parser = Parser(tokens)

    ast = parser.parse()
    if ast.error:
        return None, ast.error
    print(ast.node)
    interpreter = Interpreter()

    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.interpret(ast.node, context)
    return result.value, result.error
