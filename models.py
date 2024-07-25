from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Define your models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True # All users are active

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=False)
    description = db.Column(db.String(250), nullable=False, unique=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modules = db.relationship('Module', backref='course', lazy=True, cascade="all, delete-orphan")
    enrolled = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)  # Tracking course completion 
    completed_at = db.Column(db.DateTime, nullable=True)  # For tracking date of course completion 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quizzes = db.relationship('Quiz', backref='course', lazy=True)
    
    def __repr__(self):
        return f"Course('{self.title}', '{self.description}')"

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(250), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lessons = db.relationship('Lesson', backref='module', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Module('{self.title}', '{self.description}')"

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=False)
    content = db.Column(db.Text, nullable=False)
    quiz = db.Column(db.Text, nullable=True)  # Assuming quiz is stored as JSON or similar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)

    # Additional fields for completion status
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"Lesson('{self.title}')"

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # Store questions and answers in JSON format

    def __repr__(self):
        return f"Quiz('{self.course_id}')"