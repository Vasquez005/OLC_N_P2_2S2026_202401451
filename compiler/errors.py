"""
Manejo de errores del compilador

Todas las fases (léxica, sintáctica, semántica) registran sus errores
en una misma lista para luego generar el reporte de errores.
"""
from dataclasses import dataclass


LEXICO = "Léxico"
SINTACTICO = "Sintáctico"
SEMANTICO = "Semántico"


@dataclass
class CompilerError:
    tipo: str          # LEXICO, SINTACTICO o SEMANTICO
    descripcion: str
    linea: int
    columna: int

    def __str__(self):
        # Formato de error para mostrar en consola
        return (f"[Error {self.tipo}] Línea {self.linea}, Columna {self.columna}\n"
                f"{self.descripcion}")

    def to_dictionary(self):
        # envia JSON al front-end
        return {
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "linea": self.linea,
            "columna": self.columna,
        }


class ErrorList:
    """Lista de errores compartida entre fases."""

    def __init__(self):
        self.errores = []

    def agregar(self, tipo, descripcion, linea, columna):
        self.errores.append(CompilerError(tipo, descripcion, linea, columna))

    def hay_errores(self):
        return len(self.errores) > 0

    def __iter__(self):
        return iter(self.errores)

    def __len__(self):
        return len(self.errores)