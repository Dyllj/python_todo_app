from flask import Flask, redirect, url_for, session, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class ToDo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text)
    is_done = db.Column(db.Boolean, default=False)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("API_KEY"),
    client_secret=os.getenv("API_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login')
def login():
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    redirect_uri = url_for('auth_callback', _external=True)  # ✅ Dynamically generate full redirect URI
    return google.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/auth/callback')
def auth_callback():
    try:
        token = google.authorize_access_token()
        userinfo = google.parse_id_token(token, nonce=session.get('nonce'))

        user = User.query.filter_by(email=userinfo['email']).first()
        if not user:
            user = User(
                google_id=userinfo['sub'],
                name=userinfo['name'],
                email=userinfo['email']
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('dashboard'))

    except Exception as e:
        return f"OAuth callback error: {str(e)}", 500

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        title = request.form.get('task')
        description = request.form.get('description')
        if title:
            new_task = ToDo(title=title, description=description, user_id=current_user.id)
            db.session.add(new_task)
            db.session.commit()
        return redirect(url_for('dashboard'))
    tasks = ToDo.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = ToDo.query.get_or_404(id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/complete/<int:id>', methods=['POST'])
@login_required
def complete(id):
    task = ToDo.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.is_done = not task.is_done
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    ToDo.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
