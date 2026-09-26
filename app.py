from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')

DEFAULT_PASSWORD = 'admin123'  # change this after first deploy!


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            value TEXT,
            position INTEGER
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    count = conn.execute('SELECT COUNT(*) AS c FROM fields').fetchone()['c']
    if count == 0:
        defaults = [('Name', ''), ('Date of Birth', ''), ('Date', ''), ('Reg No', '')]
        for i, (label, value) in enumerate(defaults):
            conn.execute(
                'INSERT INTO fields (label, value, position) VALUES (?, ?, ?)',
                (label, value, i)
            )

    pw_row = conn.execute("SELECT value FROM settings WHERE key = 'edit_password'").fetchone()
    if pw_row is None:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('edit_password', ?)",
            (generate_password_hash(DEFAULT_PASSWORD),)
        )

    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    conn = get_db()
    fields = conn.execute('SELECT * FROM fields ORDER BY position ASC').fetchall()
    conn.close()
    return render_template('index.html', fields=fields)


@app.route('/api/check_password', methods=['POST'])
def check_password():
    data = request.get_json(silent=True) or {}
    submitted = data.get('password') or ''

    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = 'edit_password'").fetchone()
    conn.close()

    if row and check_password_hash(row['value'], submitted):
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error', 'message': 'Incorrect password'}), 401


@app.route('/api/set_password', methods=['POST'])
def set_password():
    data = request.get_json(silent=True) or {}
    current = data.get('current_password') or ''
    new = data.get('new_password') or ''

    if len(new) < 4:
        return jsonify({'status': 'error', 'message': 'New password must be at least 4 characters'}), 400

    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = 'edit_password'").fetchone()

    if not row or not check_password_hash(row['value'], current):
        conn.close()
        return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 401

    conn.execute(
        "UPDATE settings SET value = ? WHERE key = 'edit_password'",
        (generate_password_hash(new),)
    )
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


@app.route('/api/add_field', methods=['POST'])
def add_field():
    data = request.get_json(silent=True) or {}
    label = (data.get('label') or 'New field').strip()

    conn = get_db()
    max_pos = conn.execute('SELECT COALESCE(MAX(position), -1) AS m FROM fields').fetchone()['m']
    cur = conn.execute(
        'INSERT INTO fields (label, value, position) VALUES (?, ?, ?)',
        (label, '', max_pos + 1)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({'status': 'ok', 'id': new_id})


@app.route('/api/update_field', methods=['POST'])
def update_field():
    data = request.get_json(silent=True) or {}
    field_id = data.get('id')
    label = (data.get('label') or '').strip()
    value = (data.get('value') or '').strip()

    if field_id is None:
        return jsonify({'status': 'error', 'message': 'missing id'}), 400

    conn = get_db()
    conn.execute('UPDATE fields SET label = ?, value = ? WHERE id = ?', (label, value, field_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


@app.route('/api/delete_field', methods=['POST'])
def delete_field():
    data = request.get_json(silent=True) or {}
    field_id = data.get('id')

    if field_id is None:
        return jsonify({'status': 'error', 'message': 'missing id'}), 400

    conn = get_db()
    conn.execute('DELETE FROM fields WHERE id = ?', (field_id,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


@app.route('/api/clear_all', methods=['POST'])
def clear_all():
    conn = get_db()
    conn.execute('DELETE FROM fields')
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
