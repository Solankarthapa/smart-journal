from pathlib import Path
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "journal.db"

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.commit()


def get_entry(entry_id):
    return get_db().execute(
        """
        SELECT id, title, content, created_at
        FROM entries
        WHERE id = ?
        """,
        (entry_id,),
    ).fetchone()


@app.route("/")
def index():
    entries = get_db().execute(
        """
        SELECT id, title, content, created_at
        FROM entries
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()

    return render_template("index.html", entries=entries)


@app.route("/entries", methods=("POST",))
def create_entry():
    title = request.form["title"].strip()
    content = request.form["content"].strip()

    if not title or not content:
        return redirect(url_for("index"))

    db = get_db()
    db.execute(
        "INSERT INTO entries (title, content) VALUES (?, ?)",
        (title, content),
    )
    db.commit()

    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/edit", methods=("GET", "POST"))
def edit_entry(entry_id):
    entry = get_entry(entry_id)

    if entry is None:
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()

        if title and content:
            db = get_db()
            db.execute(
                """
                UPDATE entries
                SET title = ?, content = ?
                WHERE id = ?
                """,
                (title, content, entry_id),
            )
            db.commit()

            return redirect(url_for("index"))

    return render_template("edit.html", entry=entry)


@app.route("/entries/<int:entry_id>/delete", methods=("POST",))
def delete_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()

    return redirect(url_for("index"))


with app.app_context():
    init_db()
