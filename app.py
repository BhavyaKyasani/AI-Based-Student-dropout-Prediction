from flask import Flask, session
from config import Config
from models import db, User, Department, Student, Alert
import os
import pymysql
from urllib.parse import urlparse

# Import Blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.student import student_bp
from routes.prediction import prediction_bp
from routes.counseling import counseling_bp
from routes.alert import alert_bp

def verify_and_prepare_db(app):
    """
    Verifies connection to MySQL database server. If it fails, falls back to SQLite.
    If it succeeds, ensures the database itself exists.
    """
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    if uri.startswith('mysql'):
        try:
            # Parse connection details: mysql+pymysql://username:password@host:port/database
            # Remove protocol prefix
            clean_uri = uri.replace('mysql+pymysql://', '')
            
            # Split auth and host info
            auth_info, host_info = clean_uri.split('@')
            
            # Parse username/password
            if ':' in auth_info:
                username, password = auth_info.split(':')
            else:
                username, password = auth_info, ''
                
            # Parse host/port/database
            if '/' in host_info:
                host_port, database = host_info.split('/')
            else:
                host_port, database = host_info, 'student_dropout_db'
                
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host, port = host_port, 3306
                
            # Connect to MySQL server to ensure DB exists
            conn = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                connect_timeout=3
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
            conn.commit()
            conn.close()
            print(f"Successfully connected to MySQL database: {database}")
        except Exception as e:
            print(f"Warning: Primary database connection failed ({e}). Falling back to SQLite.")
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'student_dropout.db')}"
            
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Check and prepare DB
    verify_and_prepare_db(app)
    
    # Initialize DB
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(counseling_bp)
    app.register_blueprint(alert_bp)
    
    # Custom Error Pages Handlers
    from flask import render_template
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Context processor to expose pending notifications count to all templates
    @app.context_processor
    def inject_notifications():
        if 'user_id' in session:
            try:
                # Count pending risk alerts
                pending_count = Alert.query.filter_by(status='Pending').count()
                return dict(pending_alerts_count=pending_count)
            except:
                return dict(pending_alerts_count=0)
        return dict(pending_alerts_count=0)
        
    # Custom template filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"Rs. {float(val):,.2f}"
        except:
            return f"Rs. {val}"
            
    # Create tables automatically inside application context
    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    # Run server on localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=True)
