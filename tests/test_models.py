import unittest
from app import app, db, User, Course

class ModelTest(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
        app.config['TESTING'] = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_user_creation(self):
        with app.app_context():
            user = User(username="testuser", email="test@example.com", password="password")
            db.session.add(user)
            db.session.commit()
            self.assertEqual(User.query.count(), 1)

    def test_course_creation(self):
        with app.app_context():
            course = Course(title="Test Course", description="Test Description")
            db.session.add(course)
            db.session.commit()
            self.assertEqual(Course.query.count(), 1)


if __name__ == '__main__':
    unittest.main()
