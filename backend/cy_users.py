"""
Gestion des utilisateurs — IACAS OTA
Stockage dans data/users.json (pas de base de données).
"""
import os
import json
import uuid
import logging
from datetime import datetime

import bcrypt
from flask_login import UserMixin
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Chemin vers le fichier des comptes
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(_BASE_DIR, "data", "users.json")
USERS_DIR = os.path.join(_BASE_DIR, "data", "users")


# ---------------------------------------------------------------------------
# Modèle User (Flask-Login)
# ---------------------------------------------------------------------------

class User(UserMixin):
    def __init__(self, data: dict):
        self._data = data

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def username(self) -> str:
        return self._data["username"]

    @property
    def email(self) -> str:
        return self._data.get("email", "")

    @property
    def role(self) -> str:
        return self._data.get("role", "user")

    @property
    def active(self) -> bool:
        return self._data.get("active", True)

    def is_active(self) -> bool:
        return self.active

    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_public(self) -> dict:
        """Données sûres à envoyer au frontend (sans hash mdp)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "active": self.active,
        }


# ---------------------------------------------------------------------------
# Lecture / écriture users.json
# ---------------------------------------------------------------------------

def _load_raw() -> list:
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Erreur lecture users.json : {e}")
        return []


def _save_raw(users: list) -> None:
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def load_all_users() -> list[User]:
    return [User(u) for u in _load_raw()]


def find_by_id(user_id: str) -> User | None:
    for u in _load_raw():
        if u["id"] == user_id:
            return User(u)
    return None


def find_by_username(username: str) -> User | None:
    for u in _load_raw():
        if u["username"].lower() == username.lower():
            return User(u)
    return None


def verify_password(username: str, password: str) -> User | None:
    """Vérifie le mot de passe. Retourne l'User si correct, None sinon."""
    user_data = next(
        (u for u in _load_raw() if u["username"].lower() == username.lower()), None
    )
    if not user_data:
        return None
    if not user_data.get("active", True):
        return None
    stored_hash = user_data.get("password_hash", "")
    if not stored_hash:
        return None
    try:
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            return User(user_data)
    except Exception as e:
        logger.error(f"Erreur vérification mdp : {e}")
    return None


def create_user(username: str, password: str, email: str = "", role: str = "user") -> User:
    """Crée un nouvel utilisateur. Lève ValueError si le username existe déjà."""
    if find_by_username(username):
        raise ValueError(f"L'utilisateur '{username}' existe déjà")
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")
    new_user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "active": True,
    }
    users = _load_raw()
    users.append(new_user)
    _save_raw(users)
    _init_user_profile(username)
    return User(new_user)


def update_user(user_id: str, **kwargs) -> bool:
    """Met à jour les champs d'un utilisateur (active, email, role...)."""
    users = _load_raw()
    for u in users:
        if u["id"] == user_id:
            for key, value in kwargs.items():
                if key != "password_hash":  # Le hash n'est pas mis à jour ici
                    u[key] = value
            _save_raw(users)
            return True
    return False


def change_password(user_id: str, new_password: str) -> bool:
    users = _load_raw()
    for u in users:
        if u["id"] == user_id:
            u["password_hash"] = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)
            ).decode("utf-8")
            _save_raw(users)
            return True
    return False


def delete_user(user_id: str) -> bool:
    users = _load_raw()
    new_users = [u for u in users if u["id"] != user_id]
    if len(new_users) == len(users):
        return False
    _save_raw(new_users)
    return True


# ---------------------------------------------------------------------------
# Profils utilisateurs
# ---------------------------------------------------------------------------

def _init_user_profile(username: str) -> None:
    """Crée le dossier de profil et les fichiers JSON vides si inexistants."""
    profile_dir = get_profile_dir(username)
    os.makedirs(profile_dir, exist_ok=True)
    defaults = {
        "config.json": {},
        "prompts.json": [],
        "filters.json": {},
        "directories.json": [],
    }
    for filename, default in defaults.items():
        path = os.path.join(profile_dir, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)


def get_profile_dir(username: str) -> str:
    return os.path.join(USERS_DIR, username)


def load_profile_file(username: str, filename: str) -> dict | list:
    path = os.path.join(get_profile_dir(username), filename)
    if not os.path.exists(path):
        _init_user_profile(username)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {} if filename.endswith(".json") and filename != "prompts.json" and filename != "directories.json" else []


def save_profile_file(username: str, filename: str, data) -> None:
    path = os.path.join(get_profile_dir(username), filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Initialisation admin au démarrage
# ---------------------------------------------------------------------------

def ensure_admin_exists() -> None:
    """
    Crée le compte admin au premier démarrage si users.json est vide.
    Lit ADMIN_USERNAME et ADMIN_PASSWORD depuis les variables d'environnement.
    """
    if _load_raw():
        return  # Des utilisateurs existent déjà
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin_change_me")
    try:
        create_user(admin_user, admin_pass, role="admin")
        logger.info(f"Compte admin '{admin_user}' créé automatiquement.")
        print(f"[IACAS] Compte admin '{admin_user}' créé. Changez le mot de passe !")
    except ValueError:
        pass  # Déjà existant
