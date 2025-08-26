# login_demo.py  -- Auth app (5000)
from flask import Flask, render_template_string, request, redirect, session
from urllib.parse import quote
import secrets                       # <-- thêm (dùng tạo SSO token)
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash

# --- MySQL config: sửa cho đúng máy ---
DB = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",          # điền nếu root có mật khẩu
    "database": "chatbubu",
    "cursorclass": DictCursor,
    "autocommit": True,
    "port": 3306,
}

def get_conn():
    return pymysql.connect(**DB)

def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        # Bảng users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INT AUTO_INCREMENT PRIMARY KEY,
              username VARCHAR(50) NOT NULL UNIQUE,
              password_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Bảng login_tokens phục vụ SSO (token 1 lần)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS login_tokens (
              token VARCHAR(64) PRIMARY KEY,
              username VARCHAR(50) NOT NULL,
              expires_at DATETIME NOT NULL,
              used TINYINT(1) NOT NULL DEFAULT 0
            )
            """
        )
init_db()

app = Flask(__name__)
app.secret_key = "auth_secret_key_123"
app.config["SESSION_COOKIE_NAME"] = "auth_session"

# Giữ lại hàm cũ nếu bạn còn dùng nơi khác (không dùng tới nữa)
def home_url_for_current_host(user: str) -> str:
    scheme = request.scheme or "http"
    host_only = request.host.split(":")[0]
    return f"{scheme}://{host_only}:5001/chatbubu/home?user={quote(user)}"  # KHÔNG dùng nữa

# ---------- TEMPLATES ----------
login_html = """
<!doctype html>
<html lang="vi"><head>
<meta charset="utf-8"><title>Đăng nhập | Chat Bubu</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="bg-light">
<div class="card p-4" style="max-width:400px;margin:60px auto">
  <h4 class="text-primary text-center mb-3">ĐĂNG NHẬP</h4>
  <form method="post">
    <div class="mb-3"><label class="form-label">Username</label><input name="username" class="form-control" required></div>
    <div class="mb-3"><label class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
    <button class="btn btn-primary w-100">Đăng nhập</button>
  </form>
  <div class="mt-3 text-center"><small>Chưa có tài khoản? <a href="/register">Đăng ký</a></small></div>
  {% if error %}<div class="alert alert-danger mt-3">{{ error }}</div>{% endif %}
</div></body></html>
"""

register_html = """
<!doctype html>
<html lang="vi"><head>
<meta charset="utf-8"><title>Đăng ký | Chat Bubu</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="bg-light">
<div class="card p-4" style="max-width:400px;margin:60px auto">
  <h4 class="text-success text-center mb-3">ĐĂNG KÝ</h4>
  <form method="post">
    <div class="mb-3"><label class="form-label">Username</label><input name="username" class="form-control" required></div>
    <div class="mb-3"><label class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
    <button class="btn btn-success w-100">Đăng ký</button>
  </form>
  <div class="mt-3 text-center"><small>Đã có tài khoản? <a href="/login">Đăng nhập</a></small></div>
  {% if error %}<div class="alert alert-danger mt-3">{{ error }}</div>{% endif %}
</div></body></html>
"""

# ---------- ROUTES ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username=%s", (u,))
            row = cur.fetchone()
        if row and check_password_hash(row["password_hash"], p):
            session["user"] = u
            # Tạo token SSO (hết hạn 2 phút), redirect sang 5001/sso
            token = secrets.token_urlsafe(32)
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO login_tokens(token, username, expires_at, used)
                    VALUES(%s, %s, NOW() + INTERVAL 2 MINUTE, 0)
                """, (token, u))
            scheme = request.scheme or "http"
            host_only = request.host.split(":")[0]
            return redirect(f"{scheme}://{host_only}:5001/sso?token={token}")
        else:
            error = "Sai thông tin đăng nhập!"
    return render_template_string(login_html, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        if not u or not p:
            error = "Thiếu username hoặc password!"
        else:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username=%s", (u,))
                if cur.fetchone():
                    error = "Tên đã tồn tại!"
                else:
                    ph = generate_password_hash(p)
                    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (u, ph))
                    return redirect("/login")
    return render_template_string(register_html, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
