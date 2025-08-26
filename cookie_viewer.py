from flask import Flask, render_template_string, request, redirect, Response, url_for
from urllib.parse import urljoin, quote
import requests
import re

app = Flask(__name__)

# ===== UI (minimal, calm colors) =====
HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <title>Cookie Web Viewer</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root { --bg:#f5f6f8; --card:#fff; --text:#1f2937; --muted:#6b7280; --border:#e5e7eb; --ring:#93c5fd; --btn:#4b5563; --btnh:#374151; }
    body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    .wrap { max-width: 640px; margin: 56px auto; padding: 0 12px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; box-shadow: 0 6px 20px rgba(0,0,0,.04); }
    .help { color: var(--muted); }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
    .form-control { border-radius: 10px; border-color: var(--border); }
    .form-control:focus { box-shadow: 0 0 0 .16rem var(--ring); border-color: var(--ring); }
    .btn-primary { background: var(--btn); border-color: var(--btn); border-radius: 10px; }
    .btn-primary:hover { background: var(--btnh); border-color: var(--btnh); }
    hr { border-color: var(--border); }
  </style>
</head>
<body>
<div class="wrap">
  <div class="card p-4">
    <h3 class="mb-2">Cookie Web Viewer</h3>
    <p class="help mb-4">Nhập URL và cookie — tool sẽ hiển thị trang ngay trong ứng dụng (proxy giữ cookie). Mặc định path=/, không set domain.</p>
    <form method="POST">
      <div class="mb-3">
        <label for="url" class="form-label">URL</label>
        <input type="text" id="url" name="url" class="form-control" placeholder="http://localhost:5001/home" required>
        <div class="help mt-1 small">URL phải đúng domain bạn muốn đặt cookie.</div>
      </div>
      <div class="mb-3">
        <label class="form-label">Cookie</label>
        <textarea class="form-control mono" rows="4" name="cookie" placeholder="main_session=eyJhbGciOi...; theme=dark" required></textarea>
        <div class="help mt-1 small">Hỗ trợ nhiều cookie; phân tách bằng dấu chấm phẩy <code>;</code>.</div>
      </div>
      <button class="btn btn-primary" type="submit">Mở & hiển thị</button>
    </form>
  </div>
</div>
</body>
</html>
"""

def normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not re.match(r"^https?://", u, flags=re.IGNORECASE):
        u = "http://" + u
    return u

def parse_cookie_string(s: str):
    parts = [p.strip() for p in (s or "").split(";") if p.strip()]
    pairs = []
    for p in parts:
        if "=" in p:
            name, value = p.split("=", 1)
            pairs.append({"name": name.strip(), "value": value.strip()})
    return pairs

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = normalize_url(request.form.get("url", ""))
        raw_cookie = request.form.get("cookie", "").strip()
        # chuyển thẳng qua endpoint hiển thị
        return redirect(url_for("view", url=url, cookie=raw_cookie))
    return render_template_string(HTML)

# ===== Reverse proxy that keeps cookies and rewrites links =====
@app.route("/view", methods=["GET"])
def view():
    raw_url = request.args.get("url", "").strip()
    raw_cookie = request.args.get("cookie", "").strip()
    if not raw_url or not raw_cookie:
        return "Missing url or cookie", 400

    url = normalize_url(raw_url)

    sess = requests.Session()
    # gắn cookie (không set domain để theo host của URL)
    for kv in parse_cookie_string(raw_cookie):
        sess.cookies.set(kv["name"], kv["value"], path="/")

    try:
        resp = sess.get(url, timeout=20, verify=False)
    except Exception as e:
        return Response(f"<pre>Lỗi tải URL: {e}</pre>", mimetype="text/html")

    content_type = resp.headers.get("Content-Type", "") or ""
    data = resp.content

    # 1) CSS: rewrite url(...)
    if "text/css" in content_type.lower():
        css = resp.text
        base_url = url
        def repl_url(m):
            quote_ch = m.group(1)
            target = (m.group(2) or "").strip()
            if target.startswith(("data:", "about:", "javascript:")):
                return m.group(0)
            absu = urljoin(base_url, target)
            prox = url_for("view") + "?url=" + quote(absu, safe="") + "&cookie=" + quote(raw_cookie, safe="")
            return f"url({quote_ch}{prox}{quote_ch})"
        css = re.sub(r"url\(\s*([\'\"]?)([^\'\")]+)\1\s*\)", repl_url, css, flags=re.IGNORECASE)
        data = css.encode(resp.encoding or "utf-8")
        content_type = "text/css; charset=utf-8"

    # 2) HTML: rewrite href/src/action
    if "text/html" in content_type.lower():
        html = resp.text
        base_url = url

        def to_abs(href: str) -> str:
            try:
                return urljoin(base_url, href)
            except Exception:
                return href

        def rewrite_attr(html_text: str, attr: str) -> str:
            pattern = rf'({attr}\s*=\s*[\'"])([^\'"]+)([\'"])'
            def repl(m):
                orig = m.group(2)
                if orig.startswith(("data:", "mailto:", "javascript:")):
                    return m.group(0)
                absu = to_abs(orig)
                prox = url_for("view") + "?url=" + quote(absu, safe="") + "&cookie=" + quote(raw_cookie, safe="")
                return m.group(1) + prox + m.group(3)
            return re.sub(pattern, repl, html_text, flags=re.IGNORECASE)

        # bỏ <base>, rồi rewrite
        html = re.sub(r"<base[^>]*>", "", html, flags=re.IGNORECASE)
        html = rewrite_attr(html, "href")
        html = rewrite_attr(html, "src")
        html = rewrite_attr(html, "action")

        data = html.encode(resp.encoding or "utf-8")
        content_type = "text/html; charset=utf-8"

    return Response(data, status=resp.status_code, headers={"Content-Type": content_type})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055, debug=True)
