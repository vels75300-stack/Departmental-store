# Editable Document Site

A single page where every field (heading, Name, Date of Birth, Date, Reg No)
is editable, controlled by an Edit ON/OFF toggle. Data is saved to a SQLite
database (`data.db`) through a Flask backend, so changes persist.

## How it works
- **Edit OFF** (default): fields are plain read-only text — safe for viewers.
- **Edit ON**: flip the switch, enter the edit password, and fields become
  editable. Changes to a field autosave as soon as you click away from it
  (no separate Save button needed).
- **Default password:** `admin123` — change it immediately via the
  "Change password" link that appears once you're in edit mode.
- **Forgot the password?** There's no reset link by design (this is a
  lightweight single-password gate, not full user accounts). If you get
  locked out, edit the `DEFAULT_PASSWORD` value in `app.py`, delete
  `data.db`, and restart the app — it will reseed with that password.

## Run it locally
```bash
pip install -r requirements.txt
python app.py
```
Then open http://localhost:5000

## Deploy online for free (Render.com example)
1. Push this folder to a GitHub repo.
2. Go to https://render.com → New → Web Service → connect the repo.
3. Settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Deploy. Render gives you a public URL like `https://yourapp.onrender.com`.

Any Python host that supports Flask + gunicorn works the same way
(Railway, PythonAnywhere, Fly.io, etc.).

## Extending it
- **Multiple records instead of one document:** change the `document` table
  to allow multiple rows (drop the `id=1` constraint), add a list page, and
  pass a record id into `/api/update`.
- **Password-protect editing:** add a simple login check before allowing the
  toggle to turn on (Flask sessions + a password field).
- **More fields:** add a column to the `document` table in `app.py`, add a
  matching `<input>` in `templates/index.html`, and include it in the
  `payload` object in the JavaScript Save handler.
