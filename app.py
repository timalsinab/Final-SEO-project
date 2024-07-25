import random
import string
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_migrate import Migrate
from dotenv import load_dotenv
from forms import LoginForm, RegistrationForm
from models import db, User, Course, Module, Lesson
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
import requests
import os
from bot import get_user_response
from models import db , User, Course, Module, Lesson
from openai import OpenAI

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '9c7f5ed4fee35fed7a039ddba384397f')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///../instance/site.db')

# Initialize Flask extensions
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
proxied = FlaskBehindProxy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    #return db.session.get(User, int(user_id))

def generate_token(identity, room_name):
    token = AccessToken(
        os.getenv('TWILIO_ACCOUNT_SID'),
        os.getenv('TWILIO_API_KEY_SID'),
        os.getenv('TWILIO_API_KEY_SECRET'),
        identity=identity
    )
    video_grant = VideoGrant(room=room_name)
    token.add_grant(video_grant)
    return token.to_jwt()

@app.route("/")
def landing():
    return render_template('landing.html')

@app.route("/home")
@login_required
def home():
    return render_template('home.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/video_call/<room_name>")
@login_required
def video_call(room_name):
    token = generate_token(current_user.username, room_name)
    return render_template('video_call.html', token=token, room_name=room_name)

# Global matchmaking queue and temporary storage for room assignments
matchmaking_queue = []
room_assignments = {}

lock = threading.Lock()  # Lock to handle concurrent access to matchmaking_queue and room_assignments

@app.route("/join_queue")
@login_required
def join_queue():
    print("Join queue route accessed")

    # Clear room_name from session if present
    if 'room_name' in session:
        print(f"Clearing room_name from session for user {current_user.username}")
        session.pop('room_name', None)

    # Check if the user is already in the matchmaking queue
    with lock:
        if current_user.username in matchmaking_queue:
            print(f"User {current_user.username} is already in the queue")
            return jsonify({'matched': False, 'message': 'You are already in the queue'})

        # Add the user to the queue
        matchmaking_queue.append(current_user.username)
        print(f"User {current_user.username} added to queue. Current queue: {matchmaking_queue}")

        # Check if there are exactly two users in the queue
        if len(matchmaking_queue) >= 2:
            user1 = matchmaking_queue.pop(0)
            user2 = matchmaking_queue.pop(0)
            room_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            room_assignments[user1] = room_name
            room_assignments[user2] = room_name

            print(f"Room {room_name} created with users: {user1} and {user2}")
            print(f"Matchmaking queue: {matchmaking_queue}")

            # Return response with room details for the current user
            session['room_name'] = room_name
            return jsonify({'matched': True, 'room_name': room_name})

    # If not enough users, return waiting message
    print(f"User {current_user.username} waiting for a partner")
    return jsonify({'matched': False, 'message': 'You have been added to the queue and are waiting for a partner'})

@app.route("/check_match")
@login_required
def check_match():
    username = current_user.username
    if username in room_assignments:
        room_name = room_assignments[username]
        session['room_name'] = room_name
        return jsonify({'matched': True, 'room_name': room_name})
    return jsonify({'matched': False})

@app.route("/token")
@login_required
def token():
    room_name = session.get('room_name')
    if not room_name:
        return jsonify({'error': 'No room name found'}), 404
    token = generate_token(current_user.username, room_name)
    return jsonify({'token': token})

# JDoodle API endpoint
@app.route("/compile", methods=['POST'])
def compile_code():
    data = request.json
    payload = {
        'script': data['script'],
        'language': data['language'],
        'stdin': data['stdin'],
        'versionIndex': '0',
        'clientId': os.environ.get('JDOODLE_CLIENT_ID'),
        'clientSecret': os.environ.get('JDOODLE_CLIENT_SECRET')
    }
    response = requests.post('https://api.jdoodle.com/v1/execute', json=payload)
    return jsonify(response.json())

@app.route("/end_call", methods=['POST'])
@login_required
def end_call():
    # Perform any necessary cleanup here, such as updating the database or matchmaking queue
    session.pop('room_name', None)  # Clear the room name from the session
    return jsonify({'message': 'Call ended successfully'}), 200

# Mock Interview route
@app.route("/mock_interview")
@login_required
def mock_interview():
    return render_template('mock_interview.html')



@app.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    """if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_course = Course(title=title, description=description)
        db.session.add(new_course)
        db.session.commit()
        flash('Course added successfully!', 'success')
        return redirect(url_for('manage_courses'))"""
    id = current_user.id
    courses = Course.query.filter_by(user_id=id).all()
    return render_template('courses.html', courses=courses)

@app.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get(course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully!', 'success')
    return redirect(url_for('manage_courses'))

@app.route('/courses/<int:course_id>/modules', methods=['GET', 'POST'])
def manage_modules(course_id):
    course = Course.query.get(course_id)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_module = Module(title=title, description=description, course_id=course_id)
        db.session.add(new_module)
        db.session.commit()
        flash('Module added successfully!', 'success')
        return redirect(url_for('manage_modules', course_id=course_id))
    
    modules = Module.query.filter_by(course_id=course_id).all()
    return render_template('modules.html', course=course, modules=modules)

@app.route('/modules/<int:module_id>/delete', methods=['POST'])
def delete_module(module_id):
    module = Module.query.get(module_id)
    if module:
        db.session.delete(module)
        db.session.commit()
        flash('Module deleted successfully!', 'success')
    return redirect(url_for('manage_modules', course_id=module.course_id))

@app.route('/modules/<int:module_id>/lessons', methods=['GET', 'POST'])
def manage_lessons(module_id):
    module = Module.query.get(module_id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_lesson = Lesson(title=title, content=content, module_id=module_id)
        db.session.add(new_lesson)
        db.session.commit()
        flash('Lesson added successfully!', 'success')
        return redirect(url_for('manage_lessons', module_id=module_id))
    
    lessons = Lesson.query.filter_by(module_id=module_id).all()
    return render_template('lessons.html', module=module, lessons=lessons)

@app.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
def delete_lesson(lesson_id):
    lesson = Lesson.query.get(lesson_id)
    if lesson:
        db.session.delete(lesson)
        db.session.commit()
        flash('Lesson deleted successfully!', 'success')
    return redirect(url_for('manage_lessons', module_id=lesson.module_id))

@app.route("/chat")
@login_required
def chat():
    return render_template('chatbot.html')

@app.route("/chat", methods=['POST'])
@login_required
def chatting():
    if request.is_json:
        user_msg = request.json.get('message', '')
        bot_msg = get_user_response(user_msg)
        response = {'message': bot_msg}
        return jsonify(response), 200


def generate_modules_and_lessons(course_title, course_description, level):
    # Modify the prompt to include the user's level and request a more structured output
    if level.lower() == 'beginner':
        level_specific_prompt = (f"Generate 5 foundational modules for a course on {course_title} with the following description: {course_description}. "
                                 f"The user is a beginner, so focus on introductory and basic concepts. Format each module as follows:\n"
                                 f"Module Title: <title>\n"
                                 f"Module Description: <description>\n"
                                 f"Lessons:\n"
                                 f"1. <Lesson Title>: <Lesson Description>\n"
                                 f"2. <Lesson Title>: <Lesson Description>\n"
                                 f"3. ...")
    elif level.lower() == 'intermediate':
        level_specific_prompt = (f"Generate 5 advanced modules for a course on {course_title} with the following description: {course_description}. "
                                 f"The user is at an intermediate level, so avoid basic topics and focus on advanced concepts. Format each module as follows:\n"
                                 f"Module Title: <title>\n"
                                 f"Module Description: <description>\n"
                                 f"Lessons:\n"
                                 f"1. <Lesson Title>: <Lesson Description>\n"
                                 f"2. <Lesson Title>: <Lesson Description>\n"
                                 f"3. ...")
    else:
        level_specific_prompt = (f"Generate 5 expert-level modules for a course on {course_title} with the following description: {course_description}. "
                                 f"The user is advanced, so focus on highly specialized and complex concepts. Format each module as follows:\n"
                                 f"Module Title: <title>\n"
                                 f"Module Description: <description>\n"
                                 f"Lessons:\n"
                                 f"1. <Lesson Title>: <Lesson Description>\n"
                                 f"2. <Lesson Title>: <Lesson Description>\n"
                                 f"3. ...")

    # Generate modules using OpenAI
    modules_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": level_specific_prompt}],
        max_tokens=1500  # Set max tokens to avoid exceeding the context length
    )
    modules_content = modules_response.choices[0].message['content'].split('\n')

    modules = []
    module = None

    for line in modules_content:
        line = line.strip()
        if line.startswith("Module Title:"):
            if module:
                modules.append(module)
            module = {
                "title": line.replace("Module Title:", "").strip(),
                "description": "",
                "lessons": []
            }
        elif line.startswith("Module Description:"):
            module["description"] = line.replace("Module Description:", "").strip()
        elif line.startswith("Lessons:") or line == "":
            continue
        elif line[0].isdigit() and line[1] == '.':
            lesson_title, lesson_desc = line.split(":", 1)
            lesson = {
                "title": lesson_title.strip()[2:],  # remove the number and space
                "content": lesson_desc.strip()
            }
            module["lessons"].append(lesson)

    if module:
        modules.append(module)

    for module in modules:
        for lesson in module["lessons"]:
            self_check_prompt = f"Review and enhance the following lesson for a {level} level course on {course_title}: {lesson['content']}"
            self_check_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": self_check_prompt}],
                max_tokens=500  # Set max tokens to avoid exceeding the context length
            )
            lesson["content"] = self_check_response.choices[0].message['content']

    return modules
    # Verify the content using OpenAI
    """self_check_results = []
    for module in modules:
        for lesson in module["lessons"]:
            self_check_prompt = f"Verify if the following lesson is appropriate for a {level} level course on {course_title}: {lesson['content']}"
            self_check_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": self_check_prompt}],
                max_tokens=500  # Set max tokens to avoid exceeding the context length
            )
            lesson["self_check_result"] = self_check_response.choices[0].message['content']
            self_check_results.append(lesson["self_check_result"])

    return modules, self_check_results"""

@app.route('/generate_course', methods=['GET', 'POST'])
@login_required
def generate_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        level = request.form['level']
        user_id = current_user.id

        existing_course = Course.query.filter_by(description=description).first()
        if existing_course:
            flash('Course with this description already exists.', 'danger')
            return redirect(url_for('generate_course'))

        modules = generate_modules_and_lessons(title, description, level)
        print(modules)
        new_course = Course(title=title, description=description, user_id=user_id)
        db.session.add(new_course)
        db.session.commit()

        for module_data in modules:
            new_module = Module(title=module_data['title'], description=module_data['description'], course_id=new_course.id)
            db.session.add(new_module)
            db.session.commit()

            for lesson_data in module_data['lessons']:
                new_lesson = Lesson(title=lesson_data['title'], content=lesson_data['content'], module_id=new_module.id)
                db.session.add(new_lesson)
                db.session.commit()

        flash('Course generated and saved successfully!', 'success')
        return redirect(url_for('manage_courses'))

    return render_template('generate_course.html')

@app.route('/courses/<int:course_id>', methods=['GET'])
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('view_course.html', course=course)


@app.route("/interview", methods=['GET', 'POST'])
@login_required 
def interview():
    """Route to handle the interview prep page. """
    """Not set up yet"""
    return render_template('interview.html')

@app.route('/courses/<int:course_id>/complete', methods=['POST'])
@login_required
def complete_course(course_id):
    course = Course.query.get_or_404(course_id)
    course.completed = True
    db.session.commit()
    flash('Course marked as completed!', 'success')
    return redirect(url_for('manage_courses'))

@app.route('/completed_courses')
@login_required
def completed_courses():
    completed_courses = Course.query.filter_by(completed=True, user_id=current_user.id).all()
    return render_template('completed_courses.html', completed_courses=completed_courses)

@app.route('/courses/<int:course_id>/complete', methods=['POST'])
@login_required
def mark_course_completed(course_id):
    course = Course.query.get_or_404(course_id)
    course.completed_at = datetime.utcnow()
    db.session.commit()
    flash('Course marked as completed!', 'success')
    return redirect(url_for('manage_courses'))

if __name__ == '__main__':
    app.run(debug=True)
