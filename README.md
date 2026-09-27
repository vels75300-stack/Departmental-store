# Editable Document Site

A single page where every field (heading, Name, Date of Birth, Date, Reg No)
is editable, controlled by an Edit ON/OFF toggle. Data is saved to a SQLite
database (`data.db`) through a Flask backend, so changes persist.

## How it works
- **Viewers** (not logged in) see the fields as read-only, with a
  "Login to edit" button.
- **Login** at `/login` with the admin username and password.
- Once logged in: flip the Edit switch, make your changes, then click
  **Save** to commit them — changes are no longer autosaved on blur.
  Adding or removing a field still happens immediately.
- **Default login:** username `admin`, password `admin123` — change both
  right away via the **Account** link that appears once you're logged in
  and editing.
- **Forgot the password?** There's no reset link by design (this is a
  lightweight single-account gate, not full user management). If you get
  locked out, edit `DEFAULT_USERNAME` / `DEFAULT_PASSWORD` in `app.py`,
  delete `data.db`, and restart the app — it reseeds with those values.
- **SECRET_KEY:** for a real deployment, set a `SECRET_KEY` environment
  variable (Render → your service → Environment) to a long random string,
  so login sessions are signed with something other than the placeholder
  in the code.

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
