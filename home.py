# main_app.py
from flask import Flask, render_template_string, request, redirect, url_for, session
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "main_secret_key_456"
app.config["SESSION_COOKIE_NAME"] = "main_session"

# ====== MySQL config (sửa cho đúng máy của bạn) ======
DB = {
    "host": "localhost",
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
              id INT AUTO_INCREMENT PRIMARY KEY,
              username VARCHAR(50) NOT NULL UNIQUE,
              password_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_tokens(
              token VARCHAR(64) PRIMARY KEY,
              username VARCHAR(50) NOT NULL,
              expires_at DATETIME NOT NULL,
              used TINYINT(1) NOT NULL DEFAULT 0
            )
        """)
init_db()

# ====== Dữ liệu demo cho UI ======
default_friends = ["Kha", "Cuc", "Lam", "Hung"]
users_demo = {
    "Kha":  {"avatar": "/static/avatars/kha.jpg",  "friends": [], "posts": ["Kha vừa đăng ký Chat Bubu!"], "messages": {}},
    "Cuc":  {"avatar": "/static/avatars/cuc.jpg",  "friends": [], "posts": ["Cúc rất vui khi có Chat Bubu!"], "messages": {}},
    "Lam":  {"avatar": "/static/avatars/lam.jpg",  "friends": [], "posts": ["Chào, mình là Lam!"], "messages": {}},
    "Hung": {"avatar": "/static/avatars/hung.jpg", "friends": [], "posts": ["Hưng vừa đăng nhập!"], "messages": {}},
}
def ensure_profile(u: str):
    if u not in users_demo:
        users_demo[u] = {
            "avatar": f"https://ui-avatars.com/api/?name={u}&background=4f46e5&color=fff",
            "friends": [], "posts": [], "messages": {}
        }

# ====== Templates (giao diện đẹp) ======
home_html = """<!doctype html><html lang="vi"><head>
<meta charset="UTF-8"><title>Trang chủ | Chat Bubu</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
 body{background:#f8fafc}.app-shell{max-width:1050px}
 .card-soft{border-radius:18px; box-shadow:0 8px 24px rgba(15,23,42,.06); border:1px solid #eef2f7}
 .avatar{width:44px;height:44px;object-fit:cover;border-radius:50%;border:1px solid #e5e7eb}
 .feed-item{background:#fff;border:1px solid #eef2f7;border-radius:14px;padding:14px 16px}
 .feed-item + .feed-item{margin-top:12px}.section-title{font-weight:700;color:#4f46e5}
 .btn-chip{border-radius:10px}.sticky-col{position:sticky;top:18px}
</style></head><body>
<div class="container app-shell py-4">
  <div class="card card-soft p-3 mb-4">
    <div class="d-flex align-items-center">
      <div class="fs-4 fw-bold text-primary"><i class="bi bi-house-door me-2"></i>TRANG CHỦ</div>
      <div class="ms-auto d-flex align-items-center gap-2">
        <span class="fw-semibold"><i class="bi bi-person-circle me-1"></i>{{ user }}</span>
        <a href="{{ url_for('logout') }}" class="btn btn-outline-secondary btn-sm btn-chip"><i class="bi bi-box-arrow-right me-1"></i>Đăng xuất</a>
      </div>
    </div>
  </div>

  <div class="row g-4">
    <div class="col-lg-4">
      <div class="card card-soft p-3 sticky-col">
        <div class="section-title mb-2">Bạn bè</div>
        <ul class="list-unstyled mb-3">
          {% for f in friends %}
          <li class="d-flex align-items-center py-2">
            <img class="avatar me-2" src="{{ avatars[f] }}" alt="{{ f }}">
            <div class="flex-grow-1 fw-semibold">{{ f }}</div>
            <a class="btn btn-outline-primary btn-sm btn-chip" href="{{ url_for('message', friend=f) }}">
              <i class="bi bi-chat-dots me-1"></i>Nhắn tin
            </a>
          </li>
          {% else %}<li><small class="text-muted">Bạn chưa có bạn nào!</small></li>{% endfor %}
        </ul>
        <form method="post" action="{{ url_for('add_friend') }}" class="d-flex">
          <input name="friend" class="form-control me-2" placeholder="Tên bạn mới..." required>
          <button class="btn btn-success btn-chip"><i class="bi bi-person-plus me-1"></i>Kết bạn</button>
        </form>
      </div>
    </div>

    <div class="col-lg-8">
      <div class="card card-soft p-3 mb-4">
        <div class="section-title mb-2">Bài đăng của bạn</div>
        <form method="post" action="{{ url_for('post') }}" class="d-flex">
          <input name="post" class="form-control me-2" placeholder="Bạn đang nghĩ gì?" required>
          <button class="btn btn-primary btn-chip"><i class="bi bi-send me-1"></i>Đăng</button>
        </form>
      </div>

      <div class="card card-soft p-3">
        <div class="section-title mb-2">Bảng tin bạn bè</div>
        {% if friend_posts %}
          {% for p in friend_posts %}
          <div class="feed-item d-flex align-items-start">
            <img class="avatar me-3" src="{{ avatars[p[0]] }}" alt="{{ p[0] }}">
            <div><div class="fw-semibold">{{ p[0] }}</div><div class="text-secondary">{{ p[1] }}</div></div>
          </div>
          {% endfor %}
        {% else %}<div class="text-muted"><small>Chưa có bài đăng nào từ bạn bè.</small></div>{% endif %}
      </div>
    </div>
  </div>
</div></body></html>"""

message_html = """<!doctype html><html lang="vi"><head>
<meta charset="UTF-8"><title>Nhắn tin | Chat Bubu</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
 body{background:#f8fafc}.chat{max-width:640px;margin:40px auto;box-shadow:0 10px 24px rgba(15,23,42,.08);border-radius:18px;background:#fff}
 .hd{border-bottom:1px solid #e2e8f0;padding:14px 18px}.msgs{height:340px;overflow-y:auto;padding:16px 18px;background:#f5f7fa}
 .me{background:#4f46e5;color:#fff;border-radius:16px 18px 6px 16px;padding:8px 12px;margin:6px 0 6px 60px;text-align:right}
 .fr{background:#e0e7ff;color:#23272f;border-radius:18px 16px 16px 6px;padding:8px 12px;margin:6px 60px 6px 0}
 .frm{padding:12px 18px 18px;border-top:1px solid #e2e8f0}.name{font-size:12px;opacity:.8;margin-bottom:2px}
</style></head><body>
<div class="chat">
  <div class="hd d-flex justify-content-between align-items-center">
    <div class="fw-semibold text-primary"><i class="bi bi-chat-dots me-1"></i> Nhắn tin với {{ friend }}</div>
    <a href="{{ url_for('home') }}" class="btn btn-outline-secondary btn-sm">Trang chủ</a>
  </div>

  <div class="msgs" id="chat-box">
    {% for m in messages %}
      {% if m[0] == user %}<div class="me ms-auto"><div class="name">Bạn</div>{{ m[1] }}</div>
      {% else %}<div class="fr me-auto"><div class="name">{{ friend }}</div>{{ m[1] }}</div>{% endif %}
    {% else %}<div class="text-center text-muted mt-4">Chưa có tin nhắn nào.</div>{% endfor %}
  </div>

  <form method="post" class="frm d-flex gap-2">
    <input name="msg" class="form-control" autocomplete="off" placeholder="Nhập tin nhắn..." required>
    <button class="btn btn-primary"><i class="bi bi-send"></i></button>
  </form>
</div>
<script>window.onload=function(){var c=document.getElementById("chat-box");c.scrollTop=c.scrollHeight;}</script>
</body></html>"""

# ====== SSO: nhận token từ app 5000 ======
@app.route("/sso")
def sso():
    token = request.args.get("token","")
    if not token:
        return redirect(url_for("login"))
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT username FROM login_tokens
            WHERE token=%s AND used=0 AND expires_at > NOW()
        """, (token,))
        row = cur.fetchone()
    if not row:
        # token không hợp lệ/hết hạn → quay lại login của app chính
        return redirect(url_for("login"))
    # set session và đánh dấu token đã dùng
    session["user"] = row["username"]
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE login_tokens SET used=1 WHERE token=%s", (token,))
    return redirect(url_for("home"))

# ====== (tuỳ chọn) Login trực tiếp trên app chính ======
login_html = """
<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Login 5001</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-light">
<div class="card p-4" style="max-width:400px;margin:60px auto">
  <h5 class="text-primary text-center">Đăng nhập (app chính)</h5>
  <form method="post">
    <div class="mb-3"><input name="username" class="form-control" placeholder="Username" required></div>
    <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="Password" required></div>
    <button class="btn btn-primary w-100">Đăng nhập</button>
  </form>
  <div class="mt-2 text-center"><small>Hoặc <a href="/" onclick="location.href=this.href;return false;">về trang Home nếu đã đăng nhập bằng 5000</a></small></div>
  {% if error %}<div class="alert alert-danger mt-3">{{ error }}</div>{% endif %}
</div></body></html>
"""

@app.route("/login", methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        u=request.form.get("username","").strip()
        p=request.form.get("password","")
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username=%s",(u,))
            row=cur.fetchone()
        if row and check_password_hash(row["password_hash"], p):
            session["user"]=u
            return redirect(url_for("home"))
        error="Sai thông tin đăng nhập!"
    return render_template_string(login_html, error=error)

# ====== Trang chủ, feed, nhắn tin ======
@app.route("/chatbubu/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    user=session["user"]
    ensure_profile(user)
    friends=list(set(users_demo[user]["friends"] + [f for f in default_friends if f!=user]))
    friend_posts=[]
    for f in friends:
        for post in users_demo.get(f,{}).get("posts",[]):
            friend_posts.append((f,post))
    avatars={}
    for u in users_demo:
        a = users_demo[u].get("avatar") or f"https://ui-avatars.com/api/?name={u}&background=4f46e5&color=fff"
        if a.startswith("static/"): a="/"+a
        avatars[u]=a
    return render_template_string(home_html, user=user, friends=friends,
                                  friend_posts=friend_posts, avatars=avatars)

@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user" not in session: return redirect(url_for("login"))
    u=session["user"]; f=request.form.get("friend","").strip()
    if f and f in users_demo and f!=u and f not in users_demo[u]["friends"]:
        users_demo[u]["friends"].append(f); users_demo[f]["friends"].append(u)
    return redirect(url_for("home"))

@app.route("/post", methods=["POST"])
def post():
    if "user" not in session: return redirect(url_for("login"))
    u=session["user"]; msg=request.form.get("post","").strip()
    if msg: users_demo[u]["posts"].append(msg)
    return redirect(url_for("home"))

@app.route("/message/<friend>", methods=["GET","POST"])
def message(friend):
    if "user" not in session or friend not in users_demo: return redirect(url_for("login"))
    u=session["user"]; ensure_profile(u); ensure_profile(friend)
    mybox=users_demo[u]["messages"].setdefault(friend, [])
    peer =users_demo[friend]["messages"].setdefault(u, [])
    if request.method=="POST":
        text=request.form.get("msg","").strip()
        if text: mybox.append((u,text))
    all_msgs = mybox + [(friend, m[1]) for m in peer if m[0]==friend]
    return render_template_string(message_html, friend=friend, messages=all_msgs, user=u)

@app.route("/logout")
def logout():
    session.clear()
    # redirect về trang login của app auth (5000)
    return redirect("http://127.0.0.1:5000/login")


if __name__ == "__main__":
    app.run("0.0.0.0", 5001, debug=True)
