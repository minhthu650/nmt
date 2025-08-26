# main_app.py
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask import Flask, render_template_string, request, redirect, url_for
import uuid

app = Flask(__name__)
app.secret_key = "any_random_secret_string"
default_friends = ["Kha", "Cuc", "Lam", "Hung"]
app.secret_key = "main_secret_key_456"  # cũng cần secret key riêng
app.config["SESSION_COOKIE_NAME"] = "main_session"  # cookie riêng cho app chính

users = {
    "alice": {
        "password": "password",
        "avatar": "/static/avatars/kha.jpg",
        "friends": [],
        "posts": ["Xin chào, tôi là Alice!"],
        "messages": {}
    },
    "minhthu": {
        "password": "123456",
        "avatar": "https://ui-avatars.com/api/?name=Minhthu&background=10b981&color=fff",
        "friends": [],
        "posts": ["minh Thư đã vào mạng xã hội!"],
        "messages": {}
    },
    "Kha": {
        "password": "123",
        "avatar": "static/avatars/kha.jpg",
        "friends": [],
        "posts": ["Kha vừa đăng ký Chat Bubu!"],
        "messages": {}
    },
    "Cuc": {
        "password": "123",
        "avatar": "static/avatars/cuc.jpg",
        "friends": [],
        "posts": ["Cúc rất vui khi có Chat Bubu!"],
        "messages": {}
    },
    "Lam": {
        "password": "123",
        "avatar": "static/avatars/lam.jpg",
        "friends": [],
        "posts": ["Chào, mình là Lam!"],
        "messages": {}
    },
    "Hung": {
        "password": "123",
        "avatar": "static/avatars/hung.jpg",
        "friends": [],
        "posts": ["Hưng vừa đăng nhập!"],
        "messages": {}
    }
}


login_html = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Đăng nhập | Chat Bubu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
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

home_html = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Trang chủ | Chat Bubu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8fafc; }
        .bubu-card { box-shadow: 0 2px 16px #e5e7eb; border-radius: 18px;}
        .bubu-title {font-weight: bold; color: #4f46e5;}
        .feed-post {background:#fff; border-radius:12px; padding:14px 18px; margin-bottom:12px; border:1px solid #f1f1f1;}
        .friend-list li {margin-bottom:10px;}
        .post-form input {border-radius:10px;}
        .post-form button {border-radius:10px;}
    </style>
</head>
<body>
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card bubu-card p-4 mb-4">
               <div class="d-flex align-items-center mb-3">
                    <span class="fs-4 fw-bold text-primary"><i class="bi bi-house-door me-2"></i> TRANG CHỦ</span>
                    <div class="ms-auto">
                        <span class="fw-semibold"><i class="bi bi-person-circle"></i> {{user}}</span>
                        <a href="/logout" class="btn btn-outline-secondary btn-sm ms-2">Đăng xuất</a>
                    </div>
                </div>

                </div>
                <div class="row">
                    <div class="col-md-4 border-end">
                        <h5 class="mb-3 text-primary">Bạn bè</h5>
                          <ul class="list-unstyled friend-list">
                                {% for f in friends %}
                                <li class="d-flex align-items-center mb-3">
                                    <img src="{{avatars[f]}}" width="38" height="38" class="rounded-circle me-2 border" alt="{{f}} avatar">
                                    <span class="fw-semibold me-2" style="width:60px; display:inline-block;">{{f}}</span>
                                    <a href="/message/{{f}}" class="btn btn-outline-primary btn-sm d-flex align-items-center ms-auto" style="min-width:100px;">
                                    <i class="bi bi-chat-dots me-1"></i>Nhắn tin
                                    </a>
                                </li>
                                {% else %}
                                <li><small>Bạn chưa có bạn nào!</small></li>
                                {% endfor %}
                                </ul>


                        <form method="post" action="/add_friend" class="d-flex mb-3">
                          <input name="friend" class="form-control me-2" placeholder="Tên bạn mới..." required>
                          <button class="btn btn-success" type="submit">Kết bạn</button>
                        </form>
                    </div>
                    <div class="col-md-8">
                    <h5 class="mb-3 text-primary">Bảng tin bạn bè</h5>
                        <div>
                        {% for post in friend_posts %}
                        <div class="d-flex align-items-center feed-post mb-3 shadow-sm" style="background:#f8fafc;">
                            <img src="{{avatars[post[0]]}}" width="40" height="40" class="rounded-circle me-3 border" alt="{{post[0]}} avatar">
                            <div>
                            <div class="fw-semibold text-dark" style="font-size: 1.05rem;">{{post[0]}}</div>
                            <div class="text-secondary" style="font-size:0.98rem;">{{post[1]}}</div>
                            </div>
                        </div>
                        {% else %}
                        <div><small>Chưa có bài đăng nào từ bạn bè.</small></div>
                        {% endfor %}
                        </div>

                        <hr>
                        <h5 class="mb-3 text-primary">Bài đăng của bạn</h5>
                        <form method="post" action="/post" class="d-flex post-form mb-2">
                          <input name="post" class="form-control me-2" placeholder="Bạn đang nghĩ gì?" required>
                          <button class="btn btn-primary" type="submit">Đăng bài</button>
                        </form>
                        <ul class="list-unstyled">
                        {% for p in my_posts %}
                          <li class="feed-post">{{p}}</li>
                        {% else %}
                          <li><small>Bạn chưa đăng bài nào!</small></li>
                        {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
</body>
</html>
"""

message_html = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Nhắn tin với {{friend}} | Chat Bubu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8fafc; }
        .bubu-chat { max-width: 520px; margin: 40px auto; box-shadow:0 2px 18px #e5e7eb; border-radius:22px; background:#fff; }
        .chat-header { border-bottom:1px solid #e2e8f0; padding:16px 22px; }
        .chat-messages { height:340px; overflow-y:auto; padding:24px 22px 18px 22px; background: #f5f7fa;}
        .bubble-me { background: #4f46e5; color: #fff; border-radius:16px 18px 5px 16px; padding:10px 16px; margin-bottom:8px; margin-left:70px; text-align: right; }
        .bubble-friend { background: #e0e7ff; color: #23272f; border-radius:18px 16px 16px 5px; padding:10px 16px; margin-bottom:8px; margin-right:70px;}
        .chat-form { padding:18px 22px 20px 22px; border-top:1px solid #e2e8f0; }
        .bubble-user { font-size: 13px; opacity: 0.8; margin-bottom: 2px; }
        @media (max-width: 650px) {.bubu-chat {max-width: 99vw;}}
    </style>
</head>
<body>
    <div class="bubu-chat">
        <div class="chat-header d-flex align-items-center justify-content-between">
    <div>
        <span class="fs-5 fw-semibold text-primary"><i class="bi bi-chat-dots"></i> NHẮN TIN với {{friend}}</span>
    </div>
    <a href="/" class="btn btn-outline-secondary btn-sm">Trang chủ</a>
    </div>

        <div class="chat-messages" id="chat-box">
            {% for m in messages %}
                {% if m[0] == user %}
                    <div class="bubble-me ms-auto">
                        <div class="bubble-user">Bạn</div>
                        {{ m[1] }}
                    </div>
                {% else %}
                    <div class="bubble-friend me-auto">
                        <div class="bubble-user">{{ friend }}</div>
                        {{ m[1] }}
                    </div>
                {% endif %}
            {% else %}
                <div class="text-center text-muted mt-4">Chưa có tin nhắn nào.</div>
            {% endfor %}
        </div>
        <form method="post" class="chat-form d-flex">
            <input name="msg" autocomplete="off" autofocus class="form-control me-2" placeholder="Nhập tin nhắn..." required>
            <button class="btn btn-primary" type="submit">Gửi</button>
        </form>
    </div>
    <script>
        window.onload = function() {
            var chatBox = document.getElementById("chat-box");
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
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
            session["user"] = u
            return redirect(url_for("home"))
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
            users[u] = {"password": p, "friends": [], "posts": [], "messages": {}}
            return redirect(url_for("login"))
    return render_template_string(register_html, error=error)
@app.route("/home", methods=["GET"])
def home():
    q_user = request.args.get("user")
    # Nếu URL có ?user=... thì luôn đồng bộ session theo user đó
    if q_user and session.get("user") != q_user:
        session.clear()
        session["user"] = q_user
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    # Danh sách bạn bè gồm friends thật + 4 bạn mặc định (loại trùng user)
    friends = list(set(users[user]["friends"] + [f for f in default_friends if f != user]))
    my_posts = users[user]["posts"]
    # Lấy bài đăng bạn bè
    friend_posts = []
    for f in friends:
        for post in users.get(f, {}).get("posts", []):
            friend_posts.append((f, post))
    # Truyền avatar từng user cho template
    avatars = {u: users[u]["avatar"] for u in users}
    return render_template_string(
        home_html, user=user, friends=friends, my_posts=my_posts, friend_posts=friend_posts, avatars=avatars
    )


@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    new_friend = request.form.get("friend")
    if new_friend in users and new_friend != user:
        if new_friend not in users[user]["friends"]:
            users[user]["friends"].append(new_friend)
            users[new_friend]["friends"].append(user)
    return redirect(url_for("home"))

@app.route("/post", methods=["POST"])
def post():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    msg = request.form.get("post")
    if msg:
        users[user]["posts"].append(msg)
    return redirect(url_for("home"))

@app.route("/message/<friend>", methods=["GET", "POST"])
def message(friend):
    if "user" not in session or friend not in users:
        return redirect(url_for("login"))
    user = session["user"]
    messages = users[user]["messages"].setdefault(friend, [])
    friend_messages = users[friend]["messages"].setdefault(user, [])
    all_msgs = messages + [(friend, m[1]) for m in friend_messages if m[0] == friend]
    all_msgs.sort(key=lambda x: x[0])  # Sắp xếp lại nếu cần
    if request.method == "POST":
        msg = request.form.get("msg")
        if msg:
            messages.append((user, msg))
    return render_template_string(message_html, friend=friend, messages=all_msgs, user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run("0.0.0.0", 5001, debug=True)
