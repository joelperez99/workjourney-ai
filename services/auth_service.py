"""
Autenticación multiusuario respaldada por la hoja 'Users' de Google Sheets.

Usa streamlit-authenticator para el manejo de sesión/cookies y bcrypt
(incluido en streamlit-authenticator) para el hash de contraseñas.
"""
from __future__ import annotations

import streamlit_authenticator as stauth

from config.settings import (
    AUTH_COOKIE_EXPIRY_DAYS,
    AUTH_COOKIE_KEY,
    AUTH_COOKIE_NAME,
    SHEET_USERS,
)
from database.repository import SheetRepository
from helpers.logger import get_logger
from utils.formatters import now_str
from utils.validators import is_valid_email

logger = get_logger(__name__)


class AuthService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_USERS)

    def _build_credentials(self) -> dict:
        df = self.repo.fetch_all()
        usernames = {}
        for _, row in df.iterrows():
            if not row.get("username"):
                continue
            usernames[row["username"]] = {
                "name": row.get("name") or row["username"],
                "email": row.get("email", ""),
                "password": row.get("password_hash", ""),
            }
        return {"usernames": usernames}

    def get_authenticator(self) -> stauth.Authenticate:
        credentials = self._build_credentials()
        return stauth.Authenticate(
            credentials,
            AUTH_COOKIE_NAME,
            AUTH_COOKIE_KEY,
            AUTH_COOKIE_EXPIRY_DAYS,
        )

    def has_users(self) -> bool:
        df = self.repo.fetch_all()
        return not df.empty and df["username"].astype(str).str.strip().ne("").any()

    def register_user(
        self, username: str, name: str, email: str, password: str, role: str = "user"
    ) -> tuple[bool, str]:
        if not username or not name or not password:
            return False, "Todos los campos son obligatorios."
        if email and not is_valid_email(email):
            return False, "El correo electrónico no es válido."

        df = self.repo.fetch_all()
        if not df.empty and username in df["username"].astype(str).values:
            return False, "Ese nombre de usuario ya existe."

        password_hash = stauth.Hasher.hash(password)
        self.repo.create(
            {
                "username": username,
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "avatar_url": "",
                "theme": "light",
                "created_at": now_str(),
            }
        )
        logger.info("Usuario registrado: %s", username)
        return True, "Usuario creado correctamente."

    def get_user(self, username: str) -> dict | None:
        df = self.repo.fetch_all()
        match = df[df["username"] == username]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def update_profile(self, username: str, data: dict) -> bool:
        df = self.repo.fetch_all()
        match = df[df["username"] == username]
        if match.empty:
            return False
        record_id = match.iloc[0]["id"]
        return self.repo.update(record_id, data)
