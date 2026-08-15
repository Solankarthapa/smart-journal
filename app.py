from datetime import date
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
        g.db.execute("PRAGMA foreign_keys = ON")

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
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            amount REAL,
            category_id INTEGER,
            entry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
                ON DELETE SET NULL
        )
        """
    )

    entry_columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(entries)").fetchall()
    }

    if "tags" not in entry_columns:
        db.execute(
            "ALTER TABLE entries ADD COLUMN tags TEXT NOT NULL DEFAULT ''"
        )

    if "amount" not in entry_columns:
        db.execute(
            "ALTER TABLE entries ADD COLUMN amount REAL"
        )

    if "category_id" not in entry_columns:
        db.execute(
            "ALTER TABLE entries ADD COLUMN category_id INTEGER"
        )

    if "entry_date" not in entry_columns:
        db.execute(
            "ALTER TABLE entries ADD COLUMN entry_date DATE"
        )

    db.execute(
        """
        UPDATE entries
        SET entry_date = DATE(created_at)
        WHERE entry_date IS NULL
        """
    )

    default_categories = (
        "Subscription",
        "One-off",
        "Food",
        "Transport",
        "Shopping",
        "Income",
        "Investment",
        "Health",
        "Other",
    )

    for category_name in default_categories:
        db.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (category_name,),
        )

    db.commit()


def get_entry(entry_id):
    return get_db().execute(
        """
        SELECT
            entries.id,
            entries.title,
            entries.content,
            entries.tags,
            entries.amount,
            entries.category_id,
            entries.entry_date,
            entries.created_at,
            categories.name AS category_name
        FROM entries
        LEFT JOIN categories
            ON entries.category_id = categories.id
        WHERE entries.id = ?
        """,
        (entry_id,),
    ).fetchone()


def get_categories():
    return get_db().execute(
        """
        SELECT id, name, created_at
        FROM categories
        ORDER BY name COLLATE NOCASE
        """
    ).fetchall()


def parse_amount(raw_amount):
    raw_amount = raw_amount.strip()

    if not raw_amount:
        return None

    try:
        return float(raw_amount)
    except ValueError:
        return None


def parse_entry_date(raw_date):
    raw_date = raw_date.strip()

    return raw_date if raw_date else date.today().isoformat()


def get_summary():
    db = get_db()

    summary = db.execute(
        """
        SELECT
            COUNT(*) AS total_entries,
            COALESCE(SUM(amount), 0) AS total_amount
        FROM entries
        """
    ).fetchone()

    category_count = db.execute(
        "SELECT COUNT(*) AS total_categories FROM categories"
    ).fetchone()

    return {
        "total_entries": summary["total_entries"],
        "total_amount": summary["total_amount"],
        "total_categories": category_count["total_categories"],
    }


@app.route("/")
def index():
    search_query = request.args.get("q", "").strip()

    if search_query:
        search_pattern = f"%{search_query}%"

        entries = get_db().execute(
            """
            SELECT
                entries.id,
                entries.title,
                entries.content,
                entries.tags,
                entries.amount,
                entries.category_id,
                entries.entry_date,
                entries.created_at,
                categories.name AS category_name
            FROM entries
            LEFT JOIN categories
                ON entries.category_id = categories.id
            WHERE entries.title LIKE ?
               OR entries.content LIKE ?
               OR entries.tags LIKE ?
               OR categories.name LIKE ?
            ORDER BY entries.entry_date DESC, entries.id DESC
            """,
            (
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        ).fetchall()
    else:
        entries = get_db().execute(
            """
            SELECT
                entries.id,
                entries.title,
                entries.content,
                entries.tags,
                entries.amount,
                entries.category_id,
                entries.entry_date,
                entries.created_at,
                categories.name AS category_name
            FROM entries
            LEFT JOIN categories
                ON entries.category_id = categories.id
            ORDER BY entries.entry_date DESC, entries.id DESC
            """
        ).fetchall()

    return render_template(
        "index.html",
        entries=entries,
        categories=get_categories(),
        search_query=search_query,
        today=date.today().isoformat(),
        summary=get_summary(),
    )


@app.route("/entries", methods=("POST",))
def create_entry():
    title = request.form["title"].strip()
    content = request.form["content"].strip()
    amount = parse_amount(request.form.get("amount", ""))
    entry_date = parse_entry_date(request.form.get("entry_date", ""))
    category_id = request.form.get("category_id", "").strip()

    if not title or not content:
        return redirect(url_for("index"))

    category_id = int(category_id) if category_id.isdigit() else None

    db = get_db()

    db.execute(
        """
        INSERT INTO entries
            (title, content, tags, amount, category_id, entry_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            content,
            "",
            amount,
            category_id,
            entry_date,
        ),
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
        amount = parse_amount(request.form.get("amount", ""))
        entry_date = parse_entry_date(request.form.get("entry_date", ""))
        category_id = request.form.get("category_id", "").strip()

        if title and content:
            category_id = (
                int(category_id)
                if category_id.isdigit()
                else None
            )

            db = get_db()

            db.execute(
                """
                UPDATE entries
                SET title = ?,
                    content = ?,
                    amount = ?,
                    category_id = ?,
                    entry_date = ?
                WHERE id = ?
                """,
                (
                    title,
                    content,
                    amount,
                    category_id,
                    entry_date,
                    entry_id,
                ),
            )

            db.commit()

            return redirect(url_for("index"))

    return render_template(
        "edit.html",
        entry=entry,
        categories=get_categories(),
        today=date.today().isoformat(),
    )


@app.route("/entries/<int:entry_id>/delete", methods=("POST",))
def delete_entry(entry_id):
    db = get_db()

    db.execute(
        "DELETE FROM entries WHERE id = ?",
        (entry_id,),
    )

    db.commit()

    return redirect(url_for("index"))


@app.route("/categories", methods=("GET", "POST"))
def manage_categories():
    if request.method == "POST":
        name = request.form["name"].strip()

        if name:
            db = get_db()

            db.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (name,),
            )

            db.commit()

        return redirect(url_for("manage_categories"))

    return render_template(
        "categories.html",
        categories=get_categories(),
    )


@app.route("/categories/<int:category_id>/delete", methods=("POST",))
def delete_category(category_id):
    db = get_db()

    db.execute(
        "DELETE FROM categories WHERE id = ?",
        (category_id,),
    )

    db.commit()

    return redirect(url_for("manage_categories"))


with app.app_context():
    init_db()
