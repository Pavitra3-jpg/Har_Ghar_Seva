import os
import logging
from flask import Flask
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure file upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Import models after app creation
from models import User, users_db

@login_manager.user_loader
def load_user(user_id):
    return users_db.get(int(user_id))

# Register blueprints
from auth import auth_bp
from worker import worker_bp
from jobs import jobs_bp
from admin import admin_bp
from messages import messages_bp
from ratings import ratings_bp
from notifications import notifications_bp
from analytics import analytics_bp
from search import search_bp
from unique_features import unique_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(worker_bp, url_prefix='/worker')
app.register_blueprint(jobs_bp, url_prefix='/jobs')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(messages_bp, url_prefix='/messages')
app.register_blueprint(ratings_bp, url_prefix='/ratings')
app.register_blueprint(notifications_bp, url_prefix='/notifications')
app.register_blueprint(analytics_bp, url_prefix='/analytics')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(unique_bp, url_prefix='/unique')

# Main route
from flask import render_template
from models import get_unread_count

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about-developer')
def about_developer():
    """Developer information page - Pavitra Gupta"""
    return render_template('about_developer.html')

# Template context processor to make functions available in templates
@app.context_processor
def utility_processor():
    return dict(get_unread_count=get_unread_count)

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
