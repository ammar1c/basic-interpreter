from interpreter import KEYWORDS
from error import IllegalCharError, ExpectedCharError
from position import Position
from token_ import Token, TokenType


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
            elif self.current_char in ';\n':
                tokens.append(Token(TokenType.NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char.isdigit():
                tokens.append(self.make_number())
            elif self.current_char.isalpha():
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TokenType.PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())
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
            elif self.current_char == '[':
                tokens.append(Token(TokenType.LSQAURE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TokenType.RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TokenType.COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '!':
                tok, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(tok)
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
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
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()
        tok_type = TokenType.KEYWORD if id_str in KEYWORDS else TokenType.IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TokenType.NE, pos_start=pos_start, pos_end=self.pos), None
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "Expected '=' after '!'")
    def make_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TokenType.EEQ, pos_start=pos_start, pos_end=self.pos)
        return Token(TokenType.EQUALS, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TokenType.LTE, pos_start=pos_start, pos_end=self.pos)
        return Token(TokenType.LT, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TokenType.GTE, pos_start=pos_start, pos_end=self.pos)
        return Token(TokenType.GT, pos_start=pos_start, pos_end=self.pos)

    def make_minus_or_arrow(self):
        tok_type = TokenType.MINUS
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '>':
            self.advance()
            tok_type = TokenType.ARROW
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escape_character = False
        self.advance()
        escape_characters = {
            'n': '\n',
            't': '\t'
        }
        while self.current_char and (self.current_char != '"' or escape_character):
            if escape_character:
                string += escape_characters.get(self.current_char, self.current_char)
            else:
                if self.current_char == '\\':
                    escape_character = True
                else:
                    string += self.current_char

            self.advance()
            escape_character = False
        self.advance()
        return Token(TokenType.STRING, string, pos_start, self.pos)


