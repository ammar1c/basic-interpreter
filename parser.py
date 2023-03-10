import interpreter
from error import InvalidSyntaxError
from nodes import VarAccessNode, UnaryOpNode, NumberNode, VarAssignNode, BinOpNode, IfNode, WhileNode, ForNode, \
    FuncDefNode, CallNode, StringNode, ListNode
from token_ import TokenType


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        self.advance_count += 1

    def register(self, res):
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)

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
        self.update_current_tok()
        return self.current_token

    def reverse(self, amount=1):
        self.token_index -= amount
        self.update_current_tok()
        return self.current_token

    def update_current_tok(self):
        if 0 <= self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]

    def statements(self):
        res = ParseResult()
        statements = []
        pos_start = self.current_token.pos_start.copy()
        while self.current_token.type == TokenType.NEWLINE:
            res.register_advancement()
            self.advance()
        expr = res.register(self.expr())
        if res.error: return res
        statements.append(expr)
        more_statements = True
        while True:
            newline_count = 0
            while self.current_token.type == TokenType.NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements = False
            if not more_statements:
                break
            stmt = res.try_register(self.expr())
            if not stmt:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(stmt)
        return res.success(ListNode(
            statements,
            pos_start,
            self.current_token.pos_end.copy()
        ))

    def call(self):
        res = ParseResult()
        factor_ = res.register(self.factor())
        if res.error: return res
        if self.current_token.type == TokenType.LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []
            if self.current_token.type == TokenType.RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        "Expected ')', 'VAR', int, float, identifier, '+', '-' or '('"
                    ))
                while self.current_token.type == TokenType.COMMA:
                    res.register_advancement()
                    self.advance()
                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res
                if self.current_token.type != TokenType.RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        f"Expected ',' or ')'"
                    ))
                res.register_advancement()
                self.advance()
            return res.success(CallNode(factor_, arg_nodes))
        return res.success(factor_)

    def factor(self):
        res = ParseResult()
        toke = self.current_token

        if self.matches(TokenType.KEYWORD, 'IF'):
            if_res = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_res)
        elif self.matches(TokenType.KEYWORD, "FOR"):
            if_res = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(if_res)
        elif self.matches(TokenType.KEYWORD, "WHILE"):
            if_res = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(if_res)
        elif self.matches(TokenType.KEYWORD, "FUN"):
            if_res = res.register(self.func_def())
            if res.error:
                return res
            return res.success(if_res)
        if toke.type == TokenType.IDENTIFIER and toke.value not in interpreter.KEYWORDS:
            res.register_advancement()
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
        elif toke.type == TokenType.STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(toke))
        elif toke.type == TokenType.LSQAURE:
            list = res.register(self.list_expr())
            if res.error:
                return res
            return res.success(list)
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
        return res.failure(InvalidSyntaxError(toke.pos_start, toke.pos_end,
                                              "Expected int or float or identifer or FUN or WHILE or FOR or IF"))

    def if_expr_b(self):
        return self.if_expr_cases('ELIF')

    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None
        if self.matches(TokenType.KEYWORD, 'ELIF'):
            all_cases = res.register(self.if_expr_b())
            if res.error:
                return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error:
                return res
        return res.success((cases, else_case))

    def if_expr_c(self):
        res = ParseResult()
        else_case = None
        if self.matches(TokenType.KEYWORD, 'ELSE'):
            res.register_advancement()
            self.advance()
            if self.current_token.type == TokenType.NEWLINE:
                res.register_advancement()
                self.advance()
                statements = res.register(self.statements())
                if res.error:
                    return res
                else_case = (statements, True)
                if self.matches(TokenType.KEYWORD, 'END'):
                    res.register_advancement()
                    self.advance()
                else:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        "Expected 'END'"
                    ))
            else:
                expr = res.register(self.expr())
                if res.error:
                    return res
                else_case = (expr, False)
        return res.success(else_case)
    def if_expr_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None
        if not self.matches(TokenType.KEYWORD, case_keyword):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected {case_keyword}"
            ))
        res.register_advancement()
        self.advance()
        condition = res.register(self.expr())
        if res.error: return res
        if not self.matches(TokenType.KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected THEN"
            ))
        res.register_advancement()
        self.advance()
        if self.current_token.type == TokenType.NEWLINE:
            res.register_advancement()
            self.advance()
            statements = res.register(self.statements())
            if res.error: return res
            cases.append((condition, statements, True))
            if self.matches(TokenType.KEYWORD, 'END'):
                res.register_advancement()
                self.advance()
            else:
                all_cases = res.register(self.if_expr_b_or_c())
                if res.error: return res
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            cases.append((condition, expr, False))
            all_cases = res.register(self.if_expr_b_or_c())
            if res.error: return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)
        return res.success((cases, else_case))

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases("IF"))
        if res.error:
            return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))

    def term(self):
        return self.bin_op(self.call, (TokenType.MULTIPLY, TokenType.DIVIDE))

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
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr))

        node = res.register(self.bin_op(self.comp_expr, ((TokenType.KEYWORD, "AND"), (TokenType.KEYWORD, "OR"))))
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int or float or identifier, '+', '-' or '(' or '['"
            ))
        return res.success(node)

    def comp_expr(self):
        res = ParseResult()
        if self.matches(TokenType.KEYWORD, 'NOT'):
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_token, node))
        node = res.register(self.bin_op(self.arith_expr, (
            TokenType.EEQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE)))
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected int, float, identifier, '+', '-', '(', '[' or 'NOT'"
            ))
        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, (TokenType.PLUS, TokenType.MINUS))

    def bin_op(self, func_a, ops):
        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res
        while self.current_token.type in ops or (self.current_token.type, self.current_token.value) in ops:
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            right = res.register(func_a())
            if res.error: return res
            left = BinOpNode(left, op_token, right)
        return res.success(left)

    def parse(self):
        res = self.statements()
        if not res.error and self.current_token.type != TokenType.EOF:
            return res.failure(
                InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected +-*/"))
        return res

    def for_expr(self):
        res = ParseResult()
        if not self.matches(TokenType.KEYWORD, 'FOR'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'FOR'"
            ))
        res.register_advancement()
        self.advance()
        if (self.current_token.type != TokenType.IDENTIFIER) or (self.current_token.value in interpreter.KEYWORDS):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected identifier"
            ))
        var_name = self.current_token
        res.register_advancement()
        self.advance()
        if not self.current_token.type != TokenType.EEQ:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected = "
            ))
        res.register_advancement()
        self.advance()
        var_start = res.register(self.expr())
        if res.error:
            return res
        if not self.matches(TokenType.KEYWORD, 'TO'):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected keyword 'TO'"
                )
            )
        res.register_advancement()
        self.advance()
        to_end = res.register(self.expr())
        if res.error:
            return res
        step = None
        if self.matches(TokenType.KEYWORD, "STEP"):
            res.register_advancement()
            self.advance()
            step = res.register(self.expr())
            if res.error:
                return res
        if not self.matches(TokenType.KEYWORD, "THEN"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected = "
            ))
        if self.current_token.type == TokenType.NEWLINE:
            res.register_advancement()
            self.advance()
            body = res.register(self.statements())
            if res.error:
                return res
            if not self.matches(TokenType.KEYWORD, "END"):
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected 'END'"
                ))
            res.register_advancement()
            self.advance()
            return res.success(ForNode(var_name, var_start, to_end, step, body, True))
        res.register_advancement()
        self.advance()
        body = res.register(self.expr())
        if res.error:
            return res
        return res.success(ForNode(
            var_name_tok=var_name,
            start_value_node=var_start,
            end_value_node=to_end,
            step_value_node=step if step else None,
            body_value_node=body,
            should_return_null=False
        ))

    def while_expr(self):
        res = ParseResult()

        if not self.matches(TokenType.KEYWORD, 'WHILE'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'WHILE'"
            ))
        res.register_advancement()
        self.advance()
        expr = res.register(self.expr())

        if res.error:
            return res
        if not self.matches(TokenType.KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'THEN'"
            ))
        res.register_advancement()
        self.advance()
        if self.current_token.type == TokenType.NEWLINE:
            res.register_advancement()
            self.advance()
            body = res.register(self.statements())
            if res.error:
                return res
            if not self.matches(TokenType.KEYWORD, 'END'):
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected 'END'"
                ))
            res.register_advancement()
            self.advance()
            return res.success(WhileNode(expr, body, True))
        res.register_advancement()
        self.advance()
        body = self.expr()
        if res.error:
            return res
        return res.success(WhileNode(expr, body.node, False))

    def func_def(self):
        res = ParseResult()
        if not self.matches(TokenType.KEYWORD, 'FUN'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'FUN'"
            ))
        res.register_advancement()
        self.advance()
        if self.current_token.type == TokenType.IDENTIFIER:
            var_name_tok = self.current_token
            res.register_advancement()
            self.advance()
            if self.current_token.type != TokenType.LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected '('"
                ))
        else:
            var_name_tok = None
            if self.current_token.type != TokenType.LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected identifier or '('"
                ))

        res.register_advancement()
        self.advance()
        arg_name_toks = []
        if self.current_token.type == TokenType.IDENTIFIER:
            arg_name_toks.append(self.current_token)
            res.register_advancement()
            self.advance()
            while self.current_token.type == TokenType.COMMA:
                res.register_advancement()
                self.advance()
                if self.current_token.type != TokenType.IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        "Expected identifier"
                    ))
                arg_name_toks.append(self.current_token)
                res.register_advancement()
                self.advance()
            if self.current_token.type != TokenType.RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ',' or ')'"
                ))
        else:
            if self.current_token.type != TokenType.RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected identifier or ')'"
                ))

        res.register_advancement()
        self.advance()
        if self.current_token.type == TokenType.ARROW:
            res.register_advancement()
            self.advance()
            body = res.register(self.expr())
            if res.error: return res
            return res.success(FuncDefNode(
                var_name_tok,
                arg_name_toks,
                body,
                False
            ))
        if self.current_token.type != TokenType.NEWLINE:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected '->' or NEWLINE"
            ))

        res.register_advancement()
        self.advance()
        statements = res.register(self.statements())
        if res.error: return res

        if not self.matches(TokenType.KEYWORD, 'END'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'END'"
            ))
        res.register_advancement()
        self.advance()
        return res.success(FuncDefNode(
            var_name_tok,
            arg_name_toks,
            statements,
            True
        ))

    def list_expr(self):
        res = ParseResult()
        pos_start = self.current_token.pos_start.copy()
        res.register_advancement()
        self.advance()

        arg_nodes = []
        if self.current_token.type == TokenType.RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            arg_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ']', 'VAR', int, float, identifier"
                ))
            while self.current_token.type == TokenType.COMMA:
                res.register_advancement()
                self.advance()
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res
            if self.current_token.type != TokenType.RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    f"Expected ',' or ']'"
                ))
            res.register_advancement()
            self.advance()
        return res.success(ListNode(arg_nodes, pos_start=pos_start, pos_end=self.current_token.pos_end.copy()))


