# login_demo.py  -- Auth app (5000)
from flask import Flask, render_template_string, request, redirect, session
from urllib.parse import quote
import secrets                       # <-- thêm (dùng tạo SSO token)
import pymysql
import re
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
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Đăng nhập | Chat Bubu</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
  <style>
    :root{
      --brand:#2563eb; --brand-dark:#1e40af;
      --bg:#f8fafc; --card:#ffffff;
      --muted:#64748b; --ink:#0f172a;
    }
    body{background:var(--bg); font-family: 'Segoe UI', sans-serif;}
    .auth-card{
      max-width: 420px; margin: 8vh auto; background:var(--card);
      border-radius:18px; box-shadow:0 8px 28px rgba(37,99,235,.15);
      border:1px solid #e5e7eb; padding:2rem;
    }
    .auth-title{ font-weight:800; color:var(--brand); text-align:center; }
    .form-label{ font-weight:600; color:var(--ink); }
    .form-control{ height:50px; border-radius:12px; }
    .form-control:focus{ border-color:var(--brand); box-shadow:0 0 0 .2rem rgba(37,99,235,.25);}
    .btn-brand{
      background:var(--brand); border:none; height:50px; font-weight:700;
      border-radius:12px; font-size:1rem;
    }
    .btn-brand:hover{ background:var(--brand-dark);}
    .input-group .btn{ border-radius:12px; }
    .helper{text-align:center; color:var(--muted);}
  </style>
</head>
<body>
  <div class="auth-card">
    <h2 class="auth-title mb-4">ĐĂNG NHẬP</h2>

    <form method="post">
      <div class="mb-3">
        <label class="form-label">Username</label>
        <input name="username" class="form-control" required placeholder="Nhập username">
      </div>

      <div class="mb-4">
        <label class="form-label">Password</label>
        <div class="input-group">
          <input type="password" id="login_password" name="password" class="form-control" required placeholder="Nhập mật khẩu">
          <button class="btn btn-outline-secondary" type="button" onclick="togglePwd('login_password', this)">
            <i class="bi bi-eye"></i>
          </button>
        </div>
      </div>

      <button class="btn btn-brand w-100" type="submit">Đăng nhập</button>
    </form>

    <p class="helper mt-3 mb-0">
      Chưa có tài khoản? <a href="/register">Đăng ký</a>
    </p>

    {% if error %}
      <div class="alert alert-danger mt-3 text-center">{{ error }}</div>
    {% endif %}
  </div>

  <script>
    function togglePwd(id, btn){
      const i=document.getElementById(id);
      const show=i.type==='password';
      i.type=show?'text':'password';
      btn.innerHTML=show?'<i class="bi bi-eye-slash"></i>':'<i class="bi bi-eye"></i>';
    }
  </script>
</body>
</html>
"""

register_html = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Đăng ký | Chat Bubu</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
  <style>
    :root{ --brand:#16a34a; --ring:#c6f6d5; --muted:#64748b; --bg:#f6f8fc; }
    body{background:var(--bg); font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;}
    .auth-card{ max-width: 520px; margin:8vh auto; background:#fff; border:1px solid #eef2f7; border-radius:20px; box-shadow:0 18px 48px rgba(16,24,40,.08);}
    .auth-title{ text-align:center; color:var(--brand); font-weight:900; letter-spacing:.4px;}
    .form-label{ font-weight:600 }
    .form-control{ height:52px; border-radius:14px; border:1px solid #e5e7eb; }
    .form-control:focus{ border-color:var(--brand); box-shadow:0 0 0 .25rem var(--ring); }
    .input-group .btn{ border-radius:14px; height:52px; }
    .btn-brand{ background:var(--brand); border-color:var(--brand); border-radius:14px; height:52px; font-weight:700; }
    .btn-brand:hover{ filter:brightness(.95); }
    .helper{text-align:center; color:var(--muted)}
  </style>
</head>
<body>
  <div class="auth-card p-4 p-md-5">
    <h2 class="auth-title mb-4">ĐĂNG KÝ</h2>

    <form method="post" autocomplete="on">
      <div class="mb-3">
        <label class="form-label">Username</label>
        <input name="username" class="form-control" required autocomplete="username" placeholder="Ví dụ: minhthu">
      </div>

      <div class="mb-1">
        <label class="form-label d-flex align-items-center justify-content-between">
          <span>Password</span><small class="text-muted"></small>
        </label>
        <div class="input-group">
          <input type="password" id="reg_password" name="password" class="form-control" required autocomplete="new-password" placeholder="Tạo mật khẩu">
          <button class="btn btn-outline-secondary" type="button" onclick="togglePwd('reg_password', this)" aria-label="Hiện/Ẩn mật khẩu">
            <i class="bi bi-eye"></i>
          </button>
        </div>
      </div>

      <small class="text-muted">Gợi ý: nên có chữ in hoa và ký tự đặc biệt.</small>

      <button class="btn btn-brand w-100 mt-3" type="submit">Đăng ký</button>
    </form>

    <p class="helper mt-3 mb-0">
      Đã có tài khoản? <a href="/login">Đăng nhập</a>
    </p>

    {% if error %}
      <div class="alert alert-danger mt-3 text-center">{{ error }}</div>
    {% endif %}
  </div>

  <script>
    function togglePwd(id, btn){
      const i = document.getElementById(id);
      const show = i.type === 'password';
      i.type = show ? 'text' : 'password';
      btn.innerHTML = show ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
    }
  </script>
</body>
</html>
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
        if row and row["password_hash"] == p:
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

        # --- Validate cơ bản ---
        if not u or not p:
            error = "Thiếu username hoặc password!"
        # Bắt buộc có ÍT NHẤT 1 chữ in hoa
        elif not re.search(r"[A-Z]", p):
            error = "Mật khẩu phải có ít nhất 1 chữ in hoa (A-Z)!"
        # Bắt buộc có ÍT NHẤT 1 ký tự đặc biệt (không phải chữ hoặc số)
        elif not re.search(r"[^A-Za-z0-9]", p):
            error = "Mật khẩu phải có ít nhất 1 ký tự đặc biệt (ví dụ: !@#$%^&*)."
        else:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username=%s", (u,))
                if cur.fetchone():
                    error = "Tên đã tồn tại!"
                else:
                    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (u, p))

                    return redirect("/login")
    return render_template_string(register_html, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
