from error import InvalidSyntaxError
from nodes import VarAccessNode, UnaryOpNode, NumberNode, VarAssignNode, BinOpNode
from token_ import TokenType


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advancement(self):
        self.advance_count += 1

    def register(self, res):
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
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
            res.register_advancement();
            self.advance()
            return res.success(VarAccessNode(toke))
        if toke.type in (TokenType.PLUS, TokenType.MINUS):
            res.register_advancement();
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(toke, factor))
        elif toke.type == TokenType.INT or toke.type == TokenType.FLOAT:
            res.register_advancement();
            self.advance()
            return res.success(NumberNode(toke))
        elif toke.type == TokenType.LPAREN:
            res.register_advancement();
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_token.type == TokenType.RPAREN:
                res.register_advancement();
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ')'"
                ))
        return res.failure(InvalidSyntaxError(toke.pos_start, toke.pos_end, "Expected int or float or identifer"))

    def term(self):
        return self.bin_op(self.factor, (TokenType.MULTIPLY, TokenType.DIVIDE))

    def matches(self, type_, value):
        return self.current_token.type == type_ and self.current_token.value == value

    def expr(self):
        res = ParseResult()
        if self.matches(TokenType.KEYWORD, 'VAR'):
            res.register_advancement()
            self.advance()
            if self.current_token.type != TokenType.IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected identifier"
                ))
            var_name = self.current_token
            res.register_advancement()
            self.advance()
            if self.current_token.type != TokenType.EQUALS:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected '='"
                ))
            res.register_advancement();
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr))
        node = res.register(self.bin_op(self.term, (TokenType.PLUS, TokenType.MINUS)))
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'VAR', int or float or identifier, '+', '-' or '('"
            ))
        return res.success(node)

    def bin_op(self, func_a, ops):
        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res
        while self.current_token.type in ops:
            op_token = self.current_token
            res.register_advancement()
            self.advance()
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
