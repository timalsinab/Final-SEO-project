import unittest
from flask import Flask
from flask_wtf.csrf import generate_csrf
from forms import RegistrationForm, LoginForm

class FormTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'mysecret'
        self.app.config['WTF_CSRF_ENABLED'] = False

    def test_registration_form(self):
        with self.app.test_request_context():
            form = RegistrationForm(username="testuser", email="test@example.com", password="password", confirm_password="password")
            self.assertTrue(form.validate())

    def test_login_form(self):
        with self.app.test_request_context():
            form = LoginForm(email="test@example.com", password="password")
            self.assertTrue(form.validate())

if __name__ == '__main__':
    unittest.main()
