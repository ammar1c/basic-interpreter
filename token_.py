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
    EOF = 8
    KEYWORD = 9
    EQUALS = 10
    IDENTIFIER = 11
    EEQ = 12
    NE = 13
    LT = 14
    GT = 15
    LTE = 16
    GTE = 17
    COMMA = 18
    ARROW = 19
    STRING = 20


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
    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        return f"{self.type}" + (f":{self.value}" if self.value != None else "")
