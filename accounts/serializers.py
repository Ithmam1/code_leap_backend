from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Course, Lesson, Quiz, Achievement


# ─────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'level', 'xp', 'streak', 'last_active']


# ─────────────────────────────────────────
# LESSON
# ─────────────────────────────────────────
class LessonSerializer(serializers.ModelSerializer):
    completed = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'order', 'xp_reward', 'completed']


# ─────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────
class CourseSerializer(serializers.ModelSerializer):
    total_lessons = serializers.IntegerField(read_only=True)
    completed_lessons = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'language', 'description',
            'level', 'total_lessons', 'completed_lessons'
        ]


# ─────────────────────────────────────────
# QUIZ — ⚠️ never expose correct_answer to client
# ─────────────────────────────────────────
class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            'id', 'lesson', 'question',
            'option_a', 'option_b', 'option_c', 'option_d',
            # correct_answer intentionally excluded for security
        ]


# ─────────────────────────────────────────
# ACHIEVEMENT
# ─────────────────────────────────────────
class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'icon', 'xp_required']