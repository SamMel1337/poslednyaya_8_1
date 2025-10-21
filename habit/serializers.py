from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Habit, HabitTracking
from .validators import validate_habit_creation
from users.models import  TelegramUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Habit
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, data):
        habit = Habit(**data)
        validate_habit_creation(habit)
        return data

    def validate_time_to_complete(self, value):
        if value > 120:
            raise serializers.ValidationError("Время выполнения не должно превышать 120 секунд")
        return value


class PublicHabitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Habit
        fields = ('id', 'user', 'place', 'time', 'action', 'periodicity',
                  'time_to_complete', 'created_at')
        read_only_fields = fields


class HabitTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitTracking
        fields = '__all__'


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = '__all__'
        read_only_fields = ('user', 'created_at')