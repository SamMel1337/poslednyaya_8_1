from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_habit_creation(habit):
    errors = []

    # Исключить одновременный выбор связанной привычки и указания вознаграждения
    if habit.related_habit and habit.reward:
        errors.append("Нельзя одновременно указывать связанную привычку и вознаграждение.")

    # В связанные привычки могут попадать только привычки с признаком приятной привычки
    if habit.related_habit and not habit.related_habit.is_pleasant:
        errors.append("Связанная привычка должна быть приятной.")

    # У приятной привычки не может быть вознаграждения или связанной привычки
    if habit.is_pleasant:
        if habit.reward:
            errors.append("У приятной привычки не может быть вознаграждения.")
        if habit.related_habit:
            errors.append("У приятной привычки не может быть связанной привычки.")

    # Нельзя выполнять привычку реже, чем 1 раз в 7 дней
    if habit.periodicity > 7:
        errors.append("Нельзя выполнять привычку реже, чем 1 раз в 7 дней.")

    if errors:
        raise ValidationError(errors)


class HabitValidator:
    def __call__(self, value):
        validate_habit_creation(value)