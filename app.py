import os
from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Login manager setup
login_manager = LoginManager()
login_manager.login_view = "google.login"
login_manager.init_app(app)

# OAuth2 Google blueprint
google_bp = make_google_blueprint(
    client_id=os.getenv("API_KEY"),
    client_secret=os.getenv("API_SECRET"),
    scope=["profile", "email"],
    redirect_url="/login/google/authorized"  # Default, can be omitted
)
app.register_blueprint(google_bp, url_prefix="/login")

# Models
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    todos = db.relationship("Todo", backref="owner", cascade="all, delete", lazy=True)

class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("google.login"))
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", todos=todos)

@app.route("/login/google/authorized")
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info.", 400
    info = resp.json()

    user = User.query.filter_by(google_id=info["id"]).first()
    if not user:
        user = User(
            google_id=info["id"],
            name=info.get("name"),
            email=info.get("email")
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("home"))

@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title")
    description = request.form.get("description")
    if title:
        todo = Todo(title=title, description=description, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/done/<int:todo_id>")
@login_required
def mark_done(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    todo.is_done = not todo.is_done
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# Create tables and run app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
