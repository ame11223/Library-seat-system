from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
# Use SQLite database, no need to install MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- HTML Templates (Written directly in code for beginner convenience) ---
BASE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Library Seat Reservation System</title></head>
<body>
    <nav>
        <a href=" ">Home</a > | 
        {% if current_user.is_authenticated %}
            <span>Welcome, {{ current_user.username }}</span> | <a href="/logout">Logout</a >
        {% else %}
            <a href="/login">Login</a > | <a href="/register">Register</a >
        {% endif %}
    </nav>
    <hr>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul style="color: red;">
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</body>
</html>
"""

INDEX_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<h2>Available Seats</h2>
<ul>
    {% for seat in seats %}
        <li>{{ seat.location }} - Seat ID: <b>{{ seat.name }}</b></li>
    {% endfor %}
</ul>
""")

LOGIN_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<h2>Login</h2>
<form method="POST">
    Username: <input type="text" name="username" required><br><br>
    Password: <input type="password" name="password" required><br><br>
    <button type="submit">Login</button>
</form>
""")

REGISTER_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<h2>Register</h2>
<form method="POST">
    Username: <input type="text" name="username" required><br><br>
    Password: <input type="password" name="password" required><br><br>
    <button type="submit">Register</button>
</form>
""")

# --- Routes ---
@app.route('/')
def index():
    seats = Seat.query.all()
    return render_template_string(INDEX_HTML, seats=seats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful, please login')
            return redirect(url_for('login'))
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Initialize Database and Run ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables
        if not Seat.query.first(): # Add some dummy data if no seats exist
            db.session.add(Seat(name='A-01', location='2nd Floor, East Wing'))
            db.session.add(Seat(name='A-02', location='2nd Floor, East Wing'))
            db.session.add(Seat(name='B-01', location='3rd Floor, West Wing'))
            db.session.commit()
    app.run(debug=True)
