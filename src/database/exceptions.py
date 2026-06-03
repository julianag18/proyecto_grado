"""
src/database/exceptions.py
──────────────────────────────────────────────────────────────────────────────
Excepciones personalizadas para el módulo de base de datos PAME.
──────────────────────────────────────────────────────────────────────────────
"""

class FirestoreIndexError(Exception):
    """Excepción lanzada cuando una consulta en Firestore requiere un índice compuesto ausente."""
    def __init__(self, message: str, index_url: str = None):
        super().__init__(message)
        self.index_url = index_url
