import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_PATH = "events.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            venue TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            assignee TEXT NOT NULL,
            deadline TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
        )
    """)
    # Seed sample data if empty
    count = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    if count == 0:
        cur.execute(
            "INSERT INTO events (title, event_date, event_time, venue) VALUES (?, ?, ?, ?)",
            ("Winter Showcase Live", "2026-12-12", "21:00", "The Echo Lounge — Dallas, TX")
        )
        e1 = cur.lastrowid
        cur.execute(
            "INSERT INTO events (title, event_date, event_time, venue) VALUES (?, ?, ?, ?)",
            ("New Year's Eve Rooftop Session", "2026-12-31", "22:00", "Skyline Terrace — Uptown")
        )
        e2 = cur.lastrowid
        sample_tasks = [
            (e1, "Confirm soundcheck & stage plot with venue manager", "Bradley", "2026-12-08", 1),
            (e1, "Publish final flyer & ticket link on social channels", "Eri", "2026-12-05", 0),
            (e2, "Finalize VIP table layout and security headcount", "UE", "2026-12-20", 0),
        ]
        cur.executemany(
            "INSERT INTO tasks (event_id, description, assignee, deadline, completed) VALUES (?, ?, ?, ?, ?)",
            sample_tasks
        )
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    events = conn.execute("SELECT * FROM events ORDER BY event_date ASC").fetchall()
    tasks = conn.execute("""
        SELECT tasks.*, events.title AS event_title
        FROM tasks
        JOIN events ON tasks.event_id = events.id
        ORDER BY tasks.completed ASC, tasks.deadline ASC
    """).fetchall()
    conn.close()
    open_tasks = sum(1 for t in tasks if t["completed"] == 0)
    completed_tasks = sum(1 for t in tasks if t["completed"] == 1)
    return render_template(
        "index.html",
        events=events,
        tasks=tasks,
        open_tasks=open_tasks,
        completed_tasks=completed_tasks
    )

@app.route("/events/add", methods=["POST"])
def add_event():
    conn = get_db()
    conn.execute(
        "INSERT INTO events (title, event_date, event_time, venue) VALUES (?, ?, ?, ?)",
        (request.form["title"], request.form["event_date"], request.form["event_time"], request.form["venue"])
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/events/edit/<int:event_id>", methods=["POST"])
def edit_event(event_id):
    conn = get_db()
    conn.execute(
        "UPDATE events SET title = ?, event_date = ?, event_time = ?, venue = ? WHERE id = ?",
        (request.form["title"], request.form["event_date"], request.form["event_time"], request.form["venue"], event_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/events/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE event_id = ?", (event_id,))
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/tasks/add", methods=["POST"])
def add_task():
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (event_id, description, assignee, deadline, completed) VALUES (?, ?, ?, ?, 0)",
        (request.form["event_id"], request.form["description"], request.form["assignee"], request.form["deadline"])
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/tasks/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    conn = get_db()
    conn.execute("UPDATE tasks SET completed = CASE WHEN completed = 1 THEN 0 ELSE 1 END WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
