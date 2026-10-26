"""
Genera la gramática formal de OxigenNative (en BNF) a partir de las
producciones REALES del parser de PLY, para que la documentación nunca
quede desactualizada respecto al código.

    python docs/generar_gramatica.py > docs/gramatica.md
"""
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.parser import Parser          # noqa: E402
from compiler.lexer import Lexer            # noqa: E402

# Cómo se escribe cada token en el código fuente
LEXEMAS = {
    'PLUS': "'+'", 'MINUS': "'-'", 'TIMES': "'*'", 'DIVIDE': "'/'", 'MOD': "'%'",
    'ASSIGN': "'='", 'PLUS_ASSIGN': "'+='", 'MINUS_ASSIGN': "'-='", 'TIMES_ASSIGN': "'*='",
    'DIVIDE_ASSIGN': "'/='", 'MOD_ASSIGN': "'%='",
    'EQ': "'=='", 'NE': "'!='", 'GT': "'>'", 'GE': "'>='", 'LT': "'<'", 'LE': "'<='",
    'AND': "'&&'", 'OR': "'||'", 'NOT': "'!'",
    'LPAREN': "'('", 'RPAREN': "')'", 'LBRACE': "'{'", 'RBRACE': "'}'",
    'LBRACKET': "'['", 'RBRACKET': "']'", 'SEMI': "';'", 'COMMA': "','", 'COLON': "':'",
    'DCOLON': "'::'", 'DOT': "'.'", 'DOTDOT': "'..'", 'DOTDOTEQ': "'..='",
    'ARROW': "'->'", 'FATARROW': "'=>'", 'AMP': "'&'", 'UNDERSCORE': "'_'",
    'PRINTLN': "'println!'",
    'ID': '<id>', 'INT': '<entero>', 'FLOAT': '<decimal>', 'STRING': '<cadena>',
    'CHAR': '<caracter>', 'LABEL': '<etiqueta>',
}
for palabra, token in Lexer.reserved.items():
    LEXEMAS[token] = f"'{palabra}'"


def simbolo(s):
    if s in LEXEMAS:
        return LEXEMAS[s]
    if s == 'error':
        return 'error'          # token especial de PLY para recuperarse de errores
    if s == 'empty':
        return 'ε'
    return f'<{s}>'


def main():
    p = Parser()
    reglas = OrderedDict()
    for prod in p.parser.productions[1:]:          # la 0 es S' -> programa
        if prod.name == 'empty':
            continue
        derecha = ' '.join(simbolo(s) for s in prod.prod) or 'ε'
        reglas.setdefault(prod.name, [])
        if derecha not in reglas[prod.name]:
            reglas[prod.name].append(derecha)

    print('```bnf')
    for nombre, alternativas in reglas.items():
        izquierda = f'<{nombre}>'
        print(f'{izquierda} ::= {alternativas[0]}')
        for alt in alternativas[1:]:
            print(f"{' ' * len(izquierda)}   | {alt}")
        print()
    print('```')


if __name__ == '__main__':
    main()
