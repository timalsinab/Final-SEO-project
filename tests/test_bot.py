import unittest
from bot import get_user_response

class BotTest(unittest.TestCase):
    def test_get_user_response(self):
        user_message = "Explain polymorphism in OOP"
        response = get_user_response(user_message)
        self.assertIn("polymorphism", response.lower())

if __name__ == '__main__':
    unittest.main()
