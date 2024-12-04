# app/routes/__init__.py
from .main import main_bp
from .auth import auth_bp
from .host import host_bp
from .traveler import traveler_bp
from .settings import settings_bp

__all__ = ['main_bp', 'auth_bp', 'host_bp', 'traveler_bp', 'settings_bp']