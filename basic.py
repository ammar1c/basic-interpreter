from enum import Enum


class TokenType(Enum):
    INT = 0
    FLOAT = 1
    PLUS = 2
    MINUS = 3
    MULTIPLY = 4
    DIVIDE = 5
    LPAREN = 6
    RPAREN = 7


class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.error_name = error_name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end

    def as_string(self):
        result =  f"{self.error_name}: {self.details} \n"
        result += f'File {self.pos_start.file_name}, line {self.pos_start.line + 1}'
        return result


class IllegalCharError(Error):
    def __init__(self,  pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)


class Position:
    def __init__(self, index, line, column, file_name, file_text):
        self.index = index
        self.line = line
        self.column = column
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char = None):
        self.index += 1
        self.column += 1
        if current_char == '\n':
            self.line += 1
            self.column = 0

    def copy(self):
        return Position(self.index, self.line, self.column, self.file_name, self.file_text)

class Token:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value

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
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TokenType.INT, int(num_str))
        else:
            return Token(TokenType.FLOAT, float(num_str))

    def make_tokens(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char in " \t":
                self.advance()
            elif self.current_char.isdigit():
                tokens.append(self.make_number())

            elif self.current_char == '+':
                tokens.append(Token(TokenType.PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TokenType.MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TokenType.MINUS))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TokenType.DIVIDE))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RPAREN))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        return tokens, None


def run(filename, text):
    lexer = Lexer(filename, text)
    tokens, error = lexer.make_tokens()
    return tokens, error
