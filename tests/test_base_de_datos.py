# Tests unitarios para aplicacion/base_de_datos.py

from unittest.mock import patch, MagicMock

from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db


def test_get_db_yields_session_and_closes():
    """Verifica que get_db() produce una sesión válida y la cierra al terminar."""
    mock_session = MagicMock(spec=Session)

    with patch("aplicacion.base_de_datos.SessionLocal", return_value=mock_session):
        gen = get_db()
        db = next(gen)

        # La sesión cedida debe ser la instancia creada por SessionLocal
        assert db is mock_session

        # Avanzar el generador para que ejecute el bloque finally
        try:
            next(gen)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()


def test_get_db_closes_session_on_exception():
    """Verifica que get_db() cierra la sesión incluso si ocurre una excepción."""
    mock_session = MagicMock(spec=Session)

    with patch("aplicacion.base_de_datos.SessionLocal", return_value=mock_session):
        gen = get_db()
        next(gen)

        # Simular una excepción durante el uso de la sesión
        try:
            gen.throw(Exception("error simulado"))
        except Exception:
            pass

        mock_session.close.assert_called_once()
