# auth_app.py
from flask import Flask, render_template_string, request, redirect, url_for, session
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = "auth_secret_key_123"                # chỉ cần 1 secret_key
app.config["SESSION_COOKIE_NAME"] = "auth_session"    # cookie riêng cho app login

def home_url_for_current_host(user: str) -> str:
    scheme = request.scheme or "http"                 # http/https
    host_only = request.host.split(":")[0]            # ví dụ 172.16.41.34
    return f"{scheme}://{host_only}:5001/home?user={quote(user)}"

# Không thay đổi dữ liệu
users = {
    "alice": {"password": "password"},
    "minhthu": {"password": "123456"},
    "Kha": {"password": "123"},
    "Cuc": {"password": "123"},
    "Lam": {"password": "123"},
    "Hung": {"password": "123"},
}

login_html = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Đăng nhập | Chat Bubu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Thêm Bootstrap Icons để hiện icon bi bi-... -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
      body {background: #f8fafc;}
      .bubu-card {max-width: 400px; margin: 60px auto; box-shadow:0 4px 24px #e9e9e9;}
      .bubu-title {font-weight: bold; color: #4f46e5;}
    </style>
</head>
<body>
  <div class="card bubu-card p-4">
    <h2 class="bubu-title text-center mb-3">Chat Bubu</h2>
    <h4 class="text-center mb-4 text-primary"><i class="bi bi-box-arrow-in-right"></i> ĐĂNG NHẬP (LOGIN)</h4>

    <form method="post">
        <div class="mb-3">
            <label>Username:</label>
            <input name="username" class="form-control" required>
        </div>
        <div class="mb-3">
            <label>Password:</label>
            <input type="password" name="password" class="form-control" required>
        </div>
        <button class="btn btn-primary w-100" type="submit">Đăng nhập</button>
    </form>
    <div class="mt-3 text-center">
      <small>Chưa có tài khoản? <a href="/register">Đăng ký</a></small>
    </div>
    {% if error %}
    <div class="alert alert-danger mt-3 py-2 text-center">{{ error }}</div>
    {% endif %}
  </div>
</body>
</html>
"""

register_html = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Đăng ký | Chat Bubu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Thêm Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
      body {background: #f8fafc;}
      .bubu-card {max-width: 400px; margin: 60px auto; box-shadow:0 4px 24px #e9e9e9;}
      .bubu-title {font-weight: bold; color: #4f46e5;}
    </style>
</head>
<body>
  <div class="card bubu-card p-4">
    <h2 class="bubu-title text-center mb-3">Chat Bubu</h2>
    <h4 class="text-center mb-4 text-primary"><i class="bi bi-person-plus"></i> ĐĂNG KÝ (REGISTER)</h4>

    <form method="post">
        <div class="mb-3">
            <label>Username:</label>
            <input name="username" class="form-control" required>
        </div>
        <div class="mb-3">
            <label>Password:</label>
            <input type="password" name="password" class="form-control" required>
        </div>
        <button class="btn btn-success w-100" type="submit">Đăng ký</button>
    </form>
    <div class="mt-3 text-center">
      <small>Đã có tài khoản? <a href="/login">Đăng nhập</a></small>
    </div>
    {% if error %}
    <div class="alert alert-danger mt-3 py-2 text-center">{{ error }}</div>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u in users and users[u]["password"] == p:
            # Tạo session cho app login (cookie: auth_session)
            session["user"] = u
            # Redirect sang app home theo HOST hiện tại (Windows/Kali/điện thoại đều đúng)
            return redirect(home_url_for_current_host(u))
        else:
            error = "Sai thông tin đăng nhập!"
    return render_template_string(login_html, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u in users:
            error = "Tên đã tồn tại!"
        else:
            users[u] = {"password": p}
            return redirect(url_for("login"))
    return render_template_string(register_html, error=error)

if __name__ == "__main__":
    # Lắng nghe mọi địa chỉ để máy khác (Kali/điện thoại) truy cập qua IP Windows
    app.run(host="0.0.0.0", port=5000, debug=True)
