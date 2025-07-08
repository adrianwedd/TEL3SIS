from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from .database import get_session, User

bp = Blueprint("auth", __name__, template_folder="templates")


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
