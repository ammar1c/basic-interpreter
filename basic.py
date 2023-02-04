from interpreter import Number, Context, SymbolTable, Interpreter, BuiltInFunction
from lexer import Lexer
from parser import Parser

global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number.null)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)
global_symbol_table.set("IS_STR", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)


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
