from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


class Habit(models.Model):
    PERIODICITY_CHOICES = [
        (1, 'Ежедневно'),
        (2, 'Раз в 2 дня'),
        (3, 'Раз в 3 дня'),
        (4, 'Раз в 4 дня'),
        (5, 'Раз в 5 дней'),
        (6, 'Раз в 6 дней'),
        (7, 'Еженедельно'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='habits'
    )
    place = models.CharField(max_length=255, verbose_name='Место выполнения')
    time = models.TimeField(verbose_name='Время выполнения')
    action = models.CharField(max_length=255, verbose_name='Действие')
    is_pleasant = models.BooleanField(default=False, verbose_name='Признак приятной привычки')
    related_habit = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Связанная привычка',
        related_name='related_habits'
    )
    periodicity = models.PositiveSmallIntegerField(
        choices=PERIODICITY_CHOICES,
        default=1,
        verbose_name='Периодичность (в днях)'
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Вознаграждение'
    )
    time_to_complete = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        verbose_name='Время на выполнение (в секундах)'
    )
    is_public = models.BooleanField(default=False, verbose_name='Признак публичности')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.action} в {self.time}"

    def clean(self):
        errors = {}

        if self.related_habit and self.reward:
            errors['reward'] = 'Нельзя одновременно указывать связанную привычку и вознаграждение.'

        if self.related_habit and not self.related_habit.is_pleasant:
            errors['related_habit'] = 'Связанная привычка должна быть приятной.'

        if self.is_pleasant:
            if self.reward:
                errors['reward'] = 'У приятной привычки не может быть вознаграждения.'
            if self.related_habit:
                errors['related_habit'] = 'У приятной привычки не может быть связанной привычки.'

        if self.periodicity > 7:
            errors['periodicity'] = 'Нельзя выполнять привычку реже, чем 1 раз в 7 дней.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class HabitTracking(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='trackings')
    date = models.DateField(default=timezone.now, verbose_name='Дата выполнения')
    is_completed = models.BooleanField(default=False, verbose_name='Выполнено')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Время выполнения')

    class Meta:
        verbose_name = 'Отслеживание привычки'
        verbose_name_plural = 'Отслеживание привычек'
        unique_together = ['habit', 'date']

    def __str__(self):
        status = "Выполнено" if self.is_completed else "Не выполнено"
        return f"{self.habit} - {self.date} ({status})"

    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)