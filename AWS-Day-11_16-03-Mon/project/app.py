from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# --- AWS RDS MySQL Configuration ---
MYSQL_USER     = os.environ.get("MYSQL_USER", "admin")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "demo@957684")
MYSQL_HOST     = os.environ.get("MYSQL_HOST", "database-1.cglioew4ktr8.us-east-1.rds.amazonaws.com")
MYSQL_PORT     = os.environ.get("MYSQL_PORT", "3306")
MYSQL_DB       = os.environ.get("MYSQL_DB", "test")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_timeout": 30,
    "pool_size": 10,
    "max_overflow": 5,
}

db = SQLAlchemy(app)


# --- Model ---
class User(db.Model):
    __tablename__ = "users"
    id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name  = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


# ----------------------------
#   HTML DASHBOARD (Frontend)
# ----------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Flask User Manager</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f4f6f9; color: #1a1a2e; }
  header { background: #1a1a2e; color: white; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 20px; font-weight: 600; }
  .tag { font-size: 12px; padding: 4px 10px; border-radius: 20px; background: #27ae60; color: white; }
  .tag.red { background: #e74c3c; }
  .container { max-width: 1100px; margin: 32px auto; padding: 0 24px; }
  .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px; }
  .metric { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .metric-label { font-size: 13px; color: #888; margin-bottom: 6px; }
  .metric-value { font-size: 28px; font-weight: 600; color: #1a1a2e; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .card { background: white; border-radius: 10px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .card h2 { font-size: 15px; font-weight: 600; margin-bottom: 16px; color: #1a1a2e; }
  .form-group { margin-bottom: 12px; }
  .form-group label { font-size: 13px; color: #555; display: block; margin-bottom: 4px; }
  input[type=text], input[type=email], input[type=number] {
    width: 100%; padding: 9px 12px; border: 1px solid #dde1e7; border-radius: 7px;
    font-size: 14px; outline: none; transition: border 0.2s;
  }
  input:focus { border-color: #3498db; }
  .btn { padding: 9px 18px; border: none; border-radius: 7px; font-size: 13px; font-weight: 500; cursor: pointer; transition: opacity 0.2s; }
  .btn:hover { opacity: 0.85; }
  .btn-blue  { background: #3498db; color: white; }
  .btn-green { background: #27ae60; color: white; }
  .btn-red   { background: #e74c3c; color: white; }
  .btn-gray  { background: #ecf0f1; color: #555; }
  .btn-row   { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }
  .response  { margin-top: 12px; background: #f8f9fa; border-radius: 7px; padding: 12px; font-size: 12px; font-family: monospace; min-height: 56px; max-height: 150px; overflow-y: auto; color: #333; white-space: pre-wrap; word-break: break-all; border-left: 3px solid #3498db; }
  .response.success { border-left-color: #27ae60; color: #1e8449; }
  .response.error   { border-left-color: #e74c3c; color: #c0392b; }
  .full { grid-column: 1 / -1; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; padding: 10px 12px; font-weight: 500; color: #888; font-size: 12px; border-bottom: 1px solid #f0f0f0; text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 11px 12px; border-bottom: 1px solid #f7f7f7; color: #1a1a2e; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #fafbfc; }
  .action-btn { font-size: 12px; padding: 4px 10px; border-radius: 5px; cursor: pointer; border: 1px solid; margin-right: 4px; background: transparent; font-weight: 500; }
  .edit-btn { color: #2980b9; border-color: #aed6f1; }
  .del-btn  { color: #e74c3c; border-color: #f1948a; }
  .edit-btn:hover { background: #eaf4fb; }
  .del-btn:hover  { background: #fdf0ef; }
  .empty { text-align: center; color: #aaa; padding: 32px; font-size: 14px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .dot-green { background: #27ae60; }
  .dot-red   { background: #e74c3c; }
</style>
</head>
<body>

<header>
  <h1>Flask User Manager</h1>
  <span class="tag red" id="conn-tag">● checking...</span>
</header>

<div class="container">

  <div class="metrics">
    <div class="metric">
      <div class="metric-label">Total users</div>
      <div class="metric-value" id="total">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">Database</div>
      <div class="metric-value" style="font-size:15px; padding-top:6px;" id="db-status">
        <span class="dot dot-red"></span>unknown
      </div>
    </div>
    <div class="metric">
      <div class="metric-label">Last action</div>
      <div class="metric-value" style="font-size:15px; padding-top:6px;" id="last-action">—</div>
    </div>
  </div>

  <div class="grid">

    <div class="card">
      <h2>➕ Create user</h2>
      <div class="form-group">
        <label>Name</label>
        <input type="text" id="c-name" placeholder="John Smith" />
      </div>
      <div class="form-group">
        <label>Email</label>
        <input type="email" id="c-email" placeholder="john@example.com" />
      </div>
      <button class="btn btn-green" onclick="createUser()">Create user</button>
      <div class="response" id="c-res">Response will appear here...</div>
    </div>

    <div class="card">
      <h2>🔍 Get / delete user</h2>
      <div class="form-group">
        <label>User ID</label>
        <input type="number" id="gd-id" placeholder="1" min="1" />
      </div>
      <div class="btn-row">
        <button class="btn btn-blue" onclick="getUser()">Get user</button>
        <button class="btn btn-red"  onclick="deleteUser()">Delete user</button>
      </div>
      <div class="response" id="gd-res">Response will appear here...</div>
    </div>

    <div class="card">
      <h2>✏️ Update user</h2>
      <div class="form-group">
        <label>User ID</label>
        <input type="number" id="u-id" placeholder="1" min="1" />
      </div>
      <div class="form-group">
        <label>New name (optional)</label>
        <input type="text" id="u-name" placeholder="Updated name" />
      </div>
      <div class="form-group">
        <label>New email (optional)</label>
        <input type="email" id="u-email" placeholder="updated@example.com" />
      </div>
      <button class="btn btn-blue" onclick="updateUser()">Update user</button>
      <div class="response" id="u-res">Response will appear here...</div>
    </div>

    <div class="card">
      <h2>❤️ Health check</h2>
      <p style="font-size:13px; color:#888; margin-bottom:16px;">Check if the API and RDS database are reachable.</p>
      <button class="btn btn-gray" onclick="checkHealth()">Run health check</button>
      <div class="response" id="h-res">Response will appear here...</div>
    </div>

    <div class="card full">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
        <h2 style="margin:0;">👥 All users</h2>
        <button class="btn btn-gray" onclick="getAllUsers()">🔄 Refresh</button>
      </div>
      <div id="users-container"><div class="empty">Click refresh to load users</div></div>
    </div>

  </div>
</div>

<script>
function fmt(data) { return JSON.stringify(data, null, 2); }

function setRes(id, ok, data) {
  const el = document.getElementById(id);
  el.textContent = fmt(data);
  el.className = 'response ' + (ok ? 'success' : 'error');
}

function setLastAction(msg) { document.getElementById('last-action').textContent = msg; }

async function apiFetch(path, options={}) {
  try {
    const res = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json' } });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch(e) {
    return { ok: false, status: 0, data: { error: e.message } };
  }
}

async function checkHealth() {
  const r = await apiFetch('/health');
  setRes('h-res', r.ok, r.data);
  const tag = document.getElementById('conn-tag');
  const dbStatus = document.getElementById('db-status');
  if (r.ok) {
    tag.textContent = '● connected';
    tag.className = 'tag';
    dbStatus.innerHTML = '<span class="dot dot-green"></span>connected';
  } else {
    tag.textContent = '● unreachable';
    tag.className = 'tag red';
    dbStatus.innerHTML = '<span class="dot dot-red"></span>error';
  }
  setLastAction('health check');
  getAllUsers();
}

async function getAllUsers() {
  const r = await apiFetch('/users');
  const container = document.getElementById('users-container');
  document.getElementById('total').textContent = Array.isArray(r.data) ? r.data.length : '—';
  if (!r.ok || !Array.isArray(r.data) || r.data.length === 0) {
    container.innerHTML = '<div class="empty">No users found</div>';
    return;
  }
  container.innerHTML = `<table>
    <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Actions</th></tr></thead>
    <tbody>${r.data.map(u => `
      <tr>
        <td>${u.id}</td>
        <td>${u.name}</td>
        <td>${u.email}</td>
        <td>
          <button class="action-btn edit-btn" onclick="prefillUpdate(${u.id},'${u.name}','${u.email}')">Edit</button>
          <button class="action-btn del-btn" onclick="quickDelete(${u.id})">Delete</button>
        </td>
      </tr>`).join('')}
    </tbody>
  </table>`;
}

async function createUser() {
  const name  = document.getElementById('c-name').value.trim();
  const email = document.getElementById('c-email').value.trim();
  if (!name || !email) { setRes('c-res', false, { error: 'Name and email are required' }); return; }
  const r = await apiFetch('/users', { method: 'POST', body: JSON.stringify({ name, email }) });
  setRes('c-res', r.ok, r.data);
  if (r.ok) { document.getElementById('c-name').value = ''; document.getElementById('c-email').value = ''; getAllUsers(); }
  setLastAction('created user');
}

async function getUser() {
  const id = document.getElementById('gd-id').value;
  if (!id) { setRes('gd-res', false, { error: 'Enter a user ID' }); return; }
  const r = await apiFetch(`/users/${id}`);
  setRes('gd-res', r.ok, r.data);
  setLastAction(`fetched user ${id}`);
}

async function deleteUser() {
  const id = document.getElementById('gd-id').value;
  if (!id) { setRes('gd-res', false, { error: 'Enter a user ID' }); return; }
  if (!confirm(`Delete user ${id}?`)) return;
  const r = await apiFetch(`/users/${id}`, { method: 'DELETE' });
  setRes('gd-res', r.ok, r.data);
  if (r.ok) getAllUsers();
  setLastAction(`deleted user ${id}`);
}

async function quickDelete(id) {
  if (!confirm(`Delete user ${id}?`)) return;
  const r = await apiFetch(`/users/${id}`, { method: 'DELETE' });
  if (r.ok) getAllUsers();
  setLastAction(`deleted user ${id}`);
}

async function updateUser() {
  const id    = document.getElementById('u-id').value;
  const name  = document.getElementById('u-name').value.trim();
  const email = document.getElementById('u-email').value.trim();
  if (!id) { setRes('u-res', false, { error: 'Enter a user ID' }); return; }
  const body = {};
  if (name)  body.name  = name;
  if (email) body.email = email;
  const r = await apiFetch(`/users/${id}`, { method: 'PUT', body: JSON.stringify(body) });
  setRes('u-res', r.ok, r.data);
  if (r.ok) getAllUsers();
  setLastAction(`updated user ${id}`);
}

function prefillUpdate(id, name, email) {
  document.getElementById('u-id').value    = id;
  document.getElementById('u-name').value  = name;
  document.getElementById('u-email').value = email;
  document.querySelector('.card:nth-child(3)').scrollIntoView({ behavior: 'smooth' });
}

window.onload = checkHealth;
</script>
</body>
</html>
"""


# ----------------------------
#         ROUTES
# ----------------------------

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "database": str(e)}), 500


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 409
    user = User(name=data["name"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.route("/users", methods=["GET"])
def get_users():
    return jsonify([u.to_dict() for u in User.query.all()]), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json()
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            return jsonify({"error": "Email already in use"}), 409
        user.email = data["email"]
    db.session.commit()
    return jsonify(user.to_dict()), 200


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} deleted successfully"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
