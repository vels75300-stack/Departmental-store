from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')

DEFAULT_USERNAME = 'admin'
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

    if conn.execute("SELECT value FROM settings WHERE key = 'admin_username'").fetchone() is None:
        conn.execute("INSERT INTO settings (key, value) VALUES ('admin_username', ?)", (DEFAULT_USERNAME,))

    if conn.execute("SELECT value FROM settings WHERE key = 'edit_password'").fetchone() is None:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('edit_password', ?)",
            (generate_password_hash(DEFAULT_PASSWORD),)
        )

    conn.commit()
    conn.close()


init_db()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'status': 'error', 'message': 'Please log in first'}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route('/')
def index():
    conn = get_db()
    fields = conn.execute('SELECT * FROM fields ORDER BY position ASC').fetchall()
    conn.close()
    return render_template(
        'index.html',
        fields=fields,
        logged_in=session.get('logged_in', False),
        username=session.get('username', '')
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        conn = get_db()
        stored_user = conn.execute("SELECT value FROM settings WHERE key = 'admin_username'").fetchone()
        stored_pw = conn.execute("SELECT value FROM settings WHERE key = 'edit_password'").fetchone()
        conn.close()

        valid_user = stored_user and stored_user['value'] == username
        valid_pw = stored_pw and check_password_hash(stored_pw['value'], password)

        if valid_user and valid_pw:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/save_all', methods=['POST'])
@login_required
def save_all():
    data = request.get_json(silent=True) or {}
    rows = data.get('fields', [])

    conn = get_db()
    for row in rows:
        field_id = row.get('id')
        label = (row.get('label') or '').strip()
        value = (row.get('value') or '').strip()
        if field_id is None:
            continue
        conn.execute('UPDATE fields SET label = ?, value = ? WHERE id = ?', (label, value, field_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


@app.route('/api/update_account', methods=['POST'])
@login_required
def update_account():
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or ''
    new_username = (data.get('new_username') or '').strip()
    new_password = data.get('new_password') or ''

    conn = get_db()
    stored_pw = conn.execute("SELECT value FROM settings WHERE key = 'edit_password'").fetchone()

    if not stored_pw or not check_password_hash(stored_pw['value'], current_password):
        conn.close()
        return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 401

    if new_username:
        conn.execute("UPDATE settings SET value = ? WHERE key = 'admin_username'", (new_username,))
        session['username'] = new_username

    if new_password:
        if len(new_password) < 4:
            conn.close()
            return jsonify({'status': 'error', 'message': 'New password must be at least 4 characters'}), 400
        conn.execute("UPDATE settings SET value = ? WHERE key = 'edit_password'", (generate_password_hash(new_password),))

    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


@app.route('/api/add_field', methods=['POST'])
@login_required
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


@app.route('/api/delete_field', methods=['POST'])
@login_required
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
@login_required
def clear_all():
    conn = get_db()
    conn.execute('DELETE FROM fields')
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
