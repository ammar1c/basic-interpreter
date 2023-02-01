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
    EOF    = 8


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
                tokens.append(Token(TokenType.DIVIDE,   pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RPAREN, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        tokens.append(Token(TokenType.EOF, pos_start=self.pos))
        return tokens, None


class NumberNode:
    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return f"{self.token}"


class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node

    def __repr__(self):
        return f"({self.left_node}, {self.op_token}, {self.right_node})"

class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node

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
        res  = ParseResult()
        toke = self.current_token

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

    def expr(self):
        return self.bin_op(self.term, (TokenType.PLUS, TokenType.MINUS))

    def bin_op(self, func_a, ops):
        res  = ParseResult()
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
        res =  self.expr()
        if not res.error and self.current_token.type != TokenType.EOF:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected +-*/"))
        return res



def run(filename, text):
    lexer = Lexer(filename, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error
    parser = Parser(tokens)

    ast = parser.parse()

    return ast.node, ast.error
