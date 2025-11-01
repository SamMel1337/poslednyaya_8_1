import unittest
from unittest.mock import Mock


class TestChatBot(unittest.TestCase):
    """Тесты для чат-бота"""

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Имитация основных компонентов бота
        self.bot = Mock()
        self.bot.name = "TestBot"
        self.bot.responses = {
            "greeting": ["Привет!", "Здравствуйте!", "Добрый день!"],
            "farewell": ["Пока!", "До свидания!", "Удачи!"],
            "unknown": ["Не понимаю вас", "Попробуйте сказать по-другому"],
        }

    def test_bot_initialization(self):
        """Тест инициализации бота"""
        self.assertEqual(self.bot.name, "TestBot")
        self.assertIn("greeting", self.bot.responses)
        self.assertIn("farewell", self.bot.responses)
        self.assertIn("unknown", self.bot.responses)

    def test_generate_greeting_response(self):
        """Тест генерации приветственного ответа"""
        response = self._mock_generate_response("привет")
        self.assertIn(response, self.bot.responses["greeting"])
