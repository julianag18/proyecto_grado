"""
scheduler/frequency_parser.py
──────────────────────────────────────────────────────────────────────────────
Convierte el texto de frecuencia ("Anual", "Semestral", etc.) a número
de días enteros. Soporta variantes y errores tipográficos comunes en el PAME.
──────────────────────────────────────────────────────────────────────────────
"""

# Mapa principal de frecuencia → días
_FRECUENCIA_DIAS: dict[str, int] = {
    "anual":      365,
    "semestral":  182,
    "trimestral": 91,
    "bimestral":  60,
    "mensual":    30,
}

# Alias y variantes que pueden aparecer en archivos Excel
_ALIAS: dict[str, str] = {
    "1 año":        "anual",
    "1 ano":        "anual",
    "12 meses":     "anual",
    "cada año":     "anual",
    "cada año":     "anual",
    "6 meses":      "semestral",
    "cada 6 meses": "semestral",
    "3 meses":      "trimestral",
    "cada 3 meses": "trimestral",
    "2 meses":      "bimestral",
    "cada 2 meses": "bimestral",
    "1 mes":        "mensual",
    "mensualmente": "mensual",
}


def frecuencia_a_dias(frecuencia: str | None) -> int | None:
    """
    Convierte un texto de frecuencia a número de días.

    Parámetros
    ----------
    frecuencia : str | None
        Texto de frecuencia p.ej. "Anual", "Semestral", "6 meses".

    Retorna
    -------
    int | None
        Número de días correspondiente, o None si no se reconoce el texto.

    Ejemplos
    --------
    >>> frecuencia_a_dias("Anual")
    365
    >>> frecuencia_a_dias("semestral")
    182
    >>> frecuencia_a_dias("6 meses")
    182
    >>> frecuencia_a_dias("Desconocido")
    None
    """
    if frecuencia is None:
        return None

    clave = frecuencia.strip().lower()

    # Buscar en el mapa principal
    if clave in _FRECUENCIA_DIAS:
        return _FRECUENCIA_DIAS[clave]

    # Buscar en alias
    if clave in _ALIAS:
        return _FRECUENCIA_DIAS[_ALIAS[clave]]

    # Buscar coincidencia parcial (por si hay texto adicional)
    for k, v in _FRECUENCIA_DIAS.items():
        if k in clave:
            return v

    return None
