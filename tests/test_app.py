import unittest
from flask import current_app
from flask_testing import TestCase
from app import app, db, User
from forms import RegistrationForm

class MyTest(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    TESTING = True

    def create_app(self):
        app.config.from_object(self)
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()
            user = User(username="testuser", email="test@example.com", password="password")
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        with app.test_client() as client:
            response = client.post('/register', data=dict(
                username="newuser",
                email="newuser@example.com",
                password="newpassword",
                confirm_password="newpassword"
            ), follow_redirects=True)
            
            response_data = response.data.decode()
            print(response_data)  # Print the response data for debugging

            self.assertIn('Your account has been created! You are now able to log in', response_data)

    def test_login(self):
        with app.test_client() as client:
            response = client.post('/login', data=dict(
                email="test@example.com",
                password="password"
            ), follow_redirects=True)
            self.assertIn(b'Courses', response.data)

    def test_logout(self):
        with app.test_client() as client:
            client.post('/login', data=dict(
                email="test@example.com",
                password="password"
            ), follow_redirects=True)
            response = client.get('/logout', follow_redirects=True)
            self.assertIn(b'Login', response.data)

if __name__ == '__main__':
    unittest.main()
