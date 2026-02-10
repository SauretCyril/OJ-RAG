"""
cy_limiter.py — Rate limiting centralisé (Flask-Limiter)
Importer `limiter` ici pour l'utiliser comme décorateur dans les blueprints.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=[],   # pas de limite globale — on applique route par route
)
