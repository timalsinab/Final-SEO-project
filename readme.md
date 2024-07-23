# Elearn: Computer Science Interview Preparation Web App

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Routes and Endpoints](#routes-and-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Introduction
Elearn is a web application designed to help computer science students prepare for interviews. It offers various features including interactive courses, mock interviews, and an AI tutor for real-time assistance. This project was developed as part of the Sponsors for Educational Opportunity (SEO) program.

## Features
- **Course Management:** Create, update, and manage courses, modules, and lessons.
- **Mock Interviews:** Participate in live mock interviews with peers.
- **AI Tutor:** Get real-time assistance from an AI tutor.
- **User Authentication:** Secure user registration and login system.

## Technologies Used
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Backend:** Python, Flask
- **Database:** SQLite
- **APIs:** OpenAI, Twilio
- **Others:** Flask-Bcrypt, Flask-Login, Flask-Migrate, Flask-Behind-Proxy

## Setup and Installation

### Prerequisites
- Python 3.x
- Virtual Environment
- Node.js and npm (for frontend dependencies)

### Installation Steps
1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Final-SEO-project.git
    cd Final-SEO-project
    ```

2. **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add the following:
    ```
    SECRET_KEY=your_secret_key
    DATABASE_URL=sqlite:///../instance/site.db
    TWILIO_ACCOUNT_SID=your_twilio_account_sid
    TWILIO_API_KEY_SID=your_twilio_api_key_sid
    TWILIO_API_KEY_SECRET=your_twilio_api_key_secret
    OPENAI_API_KEY=your_openai_api_key
    JDOODLE_CLIENT_ID=your_jdoodle_client_id
    JDOODLE_CLIENT_SECRET=your_jdoodle_client_secret
    ```

5. **Initialize the database:**
    ```bash
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

6. **Run the application:**
    ```bash
    python app.py
    ```

## Usage
- **Home Page:** Overview of the app and navigation links to various features.
- **Courses:** Browse, create, and manage courses, modules, and lessons.
- **Mock Interview:** Join the queue for a live mock interview with a peer.
- **AI Tutor:** Interact with the AI tutor for assistance.

## Routes and Endpoints
- **Home Page:** `/home`
- **Register:** `/register`
- **Login:** `/login`
- **Logout:** `/logout`
- **Courses:** `/courses`
- **Manage Courses:** `/courses/<int:course_id>/modules`
- **Mock Interview:** `/mock_interview`
- **Join Queue:** `/join_queue`
- **Check Match:** `/check_match`
- **Video Call:** `/video_call/<room_name>`
- **AI Tutor Chat:** `/chat`

## Contributing
1. Fork the repository.
2. Create a new feature branch.
    ```bash
    git checkout -b feature/your-feature
    ```
3. Commit your changes.
    ```bash
    git commit -m "Add your feature"
    ```
4. Push to the branch.
    ```bash
    git push origin feature/your-feature
    ```
5. Create a pull request.

