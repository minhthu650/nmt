# home.py  -- Main app (5001)
from flask import Flask, render_template_string, request, redirect, url_for, session
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "main_secret_key_456"
app.config["SESSION_COOKIE_NAME"] = "main_session"

# --- MySQL config ---
DB = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",          # điền mật khẩu nếu root có
    "database": "chatbubu",
    "cursorclass": DictCursor,
    "autocommit": True,
    "port": 3306,
}

def get_conn():
    return pymysql.connect(**DB)

def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        # users
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
        # login_tokens (để xác thực SSO)
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

# ---- Demo dữ liệu giao diện ----
default_friends = ["Kha", "Cuc", "Lam", "Hung"]
users = {
    "Kha":  {"avatar": "/static/avatars/kha.jpg",  "friends": [], "posts": ["Kha vừa đăng ký Chat Bubu!"], "messages": {}},
    "Cuc":  {"avatar": "/static/avatars/cuc.jpg",  "friends": [], "posts": ["Cúc rất vui khi có Chat Bubu!"], "messages": {}},
    "Lam":  {"avatar": "/static/avatars/lam.jpg",  "friends": [], "posts": ["Chào, mình là Lam!"], "messages": {}},
    "Hung": {"avatar": "/static/avatars/hung.jpg", "friends": [], "posts": ["Hưng vừa đăng nhập!"], "messages": {}},
}
def ensure_profile(u: str):
    if u not in users:
        users[u] = {
            "avatar": f"https://ui-avatars.com/api/?name={u}&background=4f46e5&color=fff",
            "friends": [], "posts": [], "messages": {}
        }

# --- Helper: URL login 5000 ---
def login_5000_url():
    scheme = request.scheme or "http"
    host_only = request.host.split(":")[0]
    return f"{scheme}://{host_only}:5000/login"

# ---------- Templates ----------
home_html = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Trang chủ | Chat Bubu</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
  <style>
    :root{
      --card-radius:18px;
      --shadow:0 10px 30px rgba(15,23,42,.06);
      --border:#eef2f7;
      --brand:#2563eb;
    }
    body{background:#f7f9fc}
    .shell{max-width:1200px}
    .card-soft{border:1px solid var(--border); border-radius:var(--card-radius); box-shadow:var(--shadow); background:#fff}
    /* Header */
    .header{position:sticky; top:18px; z-index:5}
    .title{font-weight:800; color:#1e40af; letter-spacing:.4px}
    /* Friends */
    .friend-item{padding:.35rem .25rem; border-radius:12px}
    .friend-item:hover{background:#f5f7fb}
    .avatar{width:44px;height:44px;object-fit:cover;border-radius:50%;border:1px solid #e5e7eb}
    /* Post box */
    .post-input{border-radius:14px; height:46px}
    .btn-pill{border-radius:12px}
    /* Feed */
    .feed-item{border:1px solid var(--border); border-radius:14px; padding:14px 16px; background:#fff}
    .feed-item + .feed-item{margin-top:12px}
    .feed-name{font-weight:700}
    .feed-text{color:#475569}
    /* Sections */
    .section-title{font-weight:800; color:#1d4ed8; letter-spacing:.3px}
  </style>
</head>
<body>
  <div class="container shell py-4">

    <!-- Header -->
    <div class="card-soft p-3 mb-4 header">
      <div class="d-flex align-items-center">
        <div class="fs-4 title"><i class="bi bi-house-door me-2"></i>TRANG CHỦ</div>
        <div class="ms-auto d-flex align-items-center gap-2">
          <span class="fw-semibold"><i class="bi bi-person-circle me-1"></i>{{ user }}</span>
          <a href="{{ url_for('logout') }}" class="btn btn-outline-secondary btn-sm btn-pill">
            <i class="bi bi-box-arrow-right me-1"></i>Đăng xuất
          </a>
        </div>
      </div>
    </div>

    <div class="row g-4">
      <!-- LEFT: Friends -->
      <div class="col-lg-4">
        <div class="card-soft p-3">
          <div class="section-title mb-2">Bạn bè</div>

          <ul class="list-unstyled">
            {% for f in friends %}
              <li class="friend-item d-flex align-items-center">
                <img class="avatar me-2" src="{{ avatars[f] }}" alt="{{ f }}">
                <div class="fw-semibold flex-grow-1">{{ f }}</div>
                <a class="btn btn-outline-primary btn-sm btn-pill" href="{{ url_for('message', friend=f) }}">
                  <i class="bi bi-chat-dots me-1"></i>Nhắn tin
                </a>
              </li>
            {% else %}
              <li class="text-muted"><small>Chưa có bạn nào.</small></li>
            {% endfor %}
          </ul>

          <form method="post" action="{{ url_for('add_friend') }}" class="d-flex mt-2">
            <input name="friend" class="form-control me-2 post-input" placeholder="Tên bạn mới..." required>
            <button class="btn btn-success btn-pill"><i class="bi bi-person-plus me-1"></i>Kết bạn</button>
          </form>
        </div>
      </div>

      <!-- RIGHT: Post + Feed -->
      <div class="col-lg-8">
        <!-- Post box -->
        <div class="card-soft p-3 mb-3">
          <div class="section-title mb-2">Bài đăng của bạn</div>
          <form method="post" action="{{ url_for('post') }}" class="d-flex">
            <input name="post" class="form-control me-2 post-input" placeholder="Bạn đang nghĩ gì?" required>
            <button class="btn btn-primary btn-pill px-4">
              <i class="bi bi-send me-1"></i>Đăng
            </button>
          </form>
        </div>

        <!-- Feed -->
        <div class="card-soft p-3">
          <div class="section-title mb-2">Bảng tin bạn bè</div>
          {% if friend_posts %}
            {% for p in friend_posts %}
              <div class="feed-item d-flex">
                <img class="avatar me-3" src="{{ avatars[p[0]] }}" alt="{{ p[0] }}">
                <div>
                  <div class="feed-name">{{ p[0] }}</div>
                  <div class="feed-text">{{ p[1] }}</div>
                </div>
              </div>
            {% endfor %}
          {% else %}
            <div class="text-muted"><small>Chưa có bài đăng nào từ bạn bè.</small></div>
          {% endif %}
        </div>
      </div>
    </div>

  </div>
</body>
</html>
"""


message_html = """
<!doctype html><html lang="vi"><head>
<meta charset="UTF-8"><title>Nhắn tin | Chat Bubu</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="bg-light">
<div class="container py-4" style="max-width:600px">
  <div class="card p-3 mb-3 shadow-sm">
    <h5 class="text-primary">Nhắn tin với {{ friend }}</h5>
    <a href="{{ url_for('home') }}" class="btn btn-outline-secondary btn-sm">Trang chủ</a>
  </div>
  <div class="card p-3 shadow-sm mb-3" style="height:300px;overflow-y:auto">
    {% for m in messages %}
      {% if m[0] == user %}
        <div class="text-end text-white bg-primary p-2 rounded mb-2">{{ m[1] }}</div>
      {% else %}
        <div class="text-start bg-light p-2 border rounded mb-2">{{ m[1] }}</div>
      {% endif %}
    {% else %}
      <div class="text-muted">Chưa có tin nhắn nào.</div>
    {% endfor %}
  </div>
  <form method="post" class="d-flex">
    <input name="msg" class="form-control me-2" placeholder="Nhập tin nhắn..." required>
    <button class="btn btn-primary">Gửi</button>
  </form>
</div></body></html>
"""

# ---------- SSO nhận token từ 5000 ----------
@app.route("/sso")
def sso():
    token = request.args.get("token", "")
    if not token:
        return redirect(login_5000_url())
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT username FROM login_tokens
            WHERE token=%s AND used=0 AND expires_at > NOW()
        """, (token,))
        row = cur.fetchone()
    if not row:
        return redirect(login_5000_url())
    session["user"] = row["username"]
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE login_tokens SET used=1 WHERE token=%s", (token,))
    return redirect(url_for("home"))

# ---------- Home / Feed / Friends ----------
@app.route("/chatbubu/home")
def home():
    if "user" not in session:
        return redirect(login_5000_url())
    user = session["user"]
    ensure_profile(user)

    friends = list(set(users[user]["friends"] + [f for f in default_friends if f != user]))
    friend_posts = []
    for f in friends:
        for post in users.get(f, {}).get("posts", []):
            friend_posts.append((f, post))

    avatars = {u: ("/" + users[u]["avatar"] if users[u].get("avatar","").startswith("static/") else users[u].get("avatar"))
               for u in users}

    return render_template_string(home_html, user=user, friends=friends,
                                  friend_posts=friend_posts, avatars=avatars)

@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user" not in session: return redirect(login_5000_url())
    u = session["user"]; f = request.form.get("friend","").strip()
    if f and f in users and f != u and f not in users[u]["friends"]:
        users[u]["friends"].append(f); users[f]["friends"].append(u)
    return redirect(url_for("home"))

@app.route("/post", methods=["POST"])
def post():
    if "user" not in session: return redirect(login_5000_url())
    u = session["user"]; msg = request.form.get("post","").strip()
    if msg: users[u]["posts"].append(msg)
    return redirect(url_for("home"))

@app.route("/message/<friend>", methods=["GET", "POST"])
def message(friend):
    if "user" not in session or friend not in users:
        return redirect(login_5000_url())
    u = session["user"]; ensure_profile(u); ensure_profile(friend)
    mybox = users[u]["messages"].setdefault(friend, [])
    peer  = users[friend]["messages"].setdefault(u, [])
    if request.method == "POST":
        text = request.form.get("msg","").strip()
        if text: mybox.append((u, text))
    all_msgs = mybox + [(friend, m[1]) for m in peer if m[0] == friend]
    return render_template_string(message_html, friend=friend, messages=all_msgs, user=u)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(login_5000_url())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
