from interpreter import Number, Context, SymbolTable, Interpreter
from lexer import Lexer
from parser import Parser

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
