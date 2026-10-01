import functools
import secrets

from authlib.integrations.flask_client import OAuth
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    session,
    url_for,
)

from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")
oauth = OAuth()


def init_oauth(app):
    """Register Google OpenID Connect using Google's discovery document."""
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )


@bp.route("/login")
def login():
    if not current_app.config["GOOGLE_CLIENT_ID"] or not current_app.config["GOOGLE_CLIENT_SECRET"]:
        flash("Google sign-in is not configured.")
        return redirect(url_for("index"))

    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/callback")
def callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        current_app.logger.exception("Google OAuth callback failed")
        flash("Google sign-in failed. Please try again.")
        return redirect(url_for("auth.login"))

    userinfo = token.get("userinfo")
    if not userinfo:
        try:
            userinfo = oauth.google.userinfo(token=token)
        except Exception:
            current_app.logger.exception("Unable to retrieve Google user information")
            flash("Google sign-in failed. Please try again.")
            return redirect(url_for("auth.login"))

    subject = userinfo.get("sub")
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)

    if not subject or not email or not email_verified:
        flash("Google did not provide a verified email address.")
        return redirect(url_for("auth.login"))

    db = get_db()
    identity = db.execute(
        """
        SELECT user.id, user.username
        FROM user_identity
        JOIN user ON user.id = user_identity.user_id
        WHERE user_identity.provider = ? AND user_identity.subject = ?
        """,
        ("google", subject),
    ).fetchone()

    if identity is None:
        # Preserve existing user IDs and foreign-key relationships. New
        # Google-only accounts receive a random unusable password hash.
        user = db.execute(
            "SELECT id, username FROM user WHERE username = ?",
            (email,),
        ).fetchone()

        if user is None:
            from werkzeug.security import generate_password_hash

            user_id = db.execute(
                "INSERT INTO user (username, password) VALUES (?, ?)",
                (email, generate_password_hash(secrets.token_urlsafe(32))),
            ).lastrowid
        else:
            user_id = user["id"]

        try:
            db.execute(
                """
                INSERT INTO user_identity (user_id, provider, subject, email)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, "google", subject, email),
            )
            db.commit()
        except db.IntegrityError:
            db.rollback()
            flash("This Google account could not be linked.")
            return redirect(url_for("auth.login"))
    else:
        user_id = identity["id"]

    session.clear()
    session["user_id"] = user_id
    session["auth_provider"] = "google"
    return redirect(url_for("index"))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view
