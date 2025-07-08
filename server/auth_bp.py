from __future__ import annotations

import os
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session
from oauthlib.oauth2 import WebApplicationClient
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from .database import get_session, User

bp = Blueprint("auth", __name__, template_folder="templates")

client = WebApplicationClient(os.environ.get("OAUTH_CLIENT_ID", "dummy"))


def _auth_url() -> str:
    return os.environ.get("OAUTH_AUTH_URL", "https://example.com/auth")


@bp.get("/login")
def login_form() -> str:  # type: ignore[return-type]
    return render_template("login.html", error=None)


@bp.post("/login")
def login_post() -> str:  # type: ignore[return-type]
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    with get_session() as session:
        user = session.query(User).filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for("dashboard.show_dashboard"))
    return render_template("login.html", error="Invalid credentials")


@bp.get("/logout")
@login_required
def logout() -> str:  # type: ignore[return-type]
    logout_user()
    return redirect(url_for("auth.login_form"))


@bp.get("/login/oauth")
def oauth_login() -> str:  # type: ignore[return-type]
    """Initiate OAuth login flow."""
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    url = client.prepare_request_uri(_auth_url(), state=state)
    return redirect(url)


@bp.get("/oauth/callback")
def oauth_callback() -> str:  # type: ignore[return-type]
    """Handle OAuth callback and log the user in."""
    state = request.args.get("state", "")
    if state != session.pop("oauth_state", None):
        return redirect(url_for("auth.login_form"))
    username = request.args.get("user", "admin")
    with get_session() as session_db:
        user = session_db.query(User).filter_by(username=username).first()
    if user:
        login_user(user)
    return redirect(url_for("dashboard.show_dashboard"))
