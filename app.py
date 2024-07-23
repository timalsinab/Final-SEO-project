from flask import Flask, render_template, redirect, url_for, flash, request,jsonify

from flask_bcrypt import Bcrypt
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_migrate import Migrate
from forms import LoginForm, RegistrationForm
import os
from bot import get_user_response
from models import db , User, Course, Module, Lesson
from openai import OpenAI
from datetime import datetime


api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = '9c7f5ed4fee35fed7a039ddba384397f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/site.db'
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


@app.route('/courses', methods=['GET'])
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
    modules_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": level_specific_prompt}],
        max_tokens=1500  # Set max tokens to avoid exceeding the context length
    )
    modules_content = modules_response.choices[0].message.content.split('\n')

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
            self_check_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": self_check_prompt}],
                max_tokens=500  # Set max tokens to avoid exceeding the context length
            )
            lesson["content"] = self_check_response.choices[0].message.content

    return modules
    # Verify the content using OpenAI
    """self_check_results = []
    for module in modules:
        for lesson in module["lessons"]:
            self_check_prompt = f"Verify if the following lesson is appropriate for a {level} level course on {course_title}: {lesson['content']}"
            self_check_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": self_check_prompt}],
                max_tokens=500  # Set max tokens to avoid exceeding the context length
            )
            lesson["self_check_result"] = self_check_response.choices[0].message.content
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


def generate_quiz(course_title, course_description):
    prompt = f"Generate a 5-question quiz based on the following course: {course_title}. Description: {course_description}. Provide questions and multiple choice answers, with one correct answer for each question. Format: Q: <question>, A: <option1>, B: <option2>, C: <option3>, D: <option4>, Answer: <correct option letter>"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500
    )
    quiz_content = response.choices[0].message.content.split('\n')
    
    quiz = []
    current_question = {}
    for line in quiz_content:
        if line.startswith("Q:"):
            if current_question:
                quiz.append(current_question)
            current_question = {"question": line[3:], "options": {}}
        elif line.startswith("A:") or line.startswith("B:") or line.startswith("C:") or line.startswith("D:"):
            current_question["options"][line[0]] = line[3:]
        elif line.startswith("Answer:"):
            current_question["answer"] = line.split(': ')[1]
    if current_question:
        quiz.append(current_question)
    
    return quiz
@app.route('/courses/<int:course_id>/submit_quiz', methods=['POST'])
@login_required
def submit_quiz(course_id):
    course = Course.query.get(course_id)
    if not course or course.user_id != current_user.id:
        flash('Course not found or you do not have permission to take this quiz.', 'danger')
        return redirect(url_for('manage_courses'))

    quiz = generate_quiz(course.title, course.description)

    score = 0
    total_questions = len(quiz)
    for index, question in enumerate(quiz):
        user_answer = request.form.get(f"question{index + 1}")
        if user_answer == question['answer']:
            score += 1

    return render_template('quiz_result.html', course=course, score=score, total_questions=total_questions)


if __name__ == '__main__':
    app.run(debug=True)
