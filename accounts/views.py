import random
import string
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.dispatch import receiver
from django.core.mail import send_mail
from django_rest_passwordreset.signals import reset_password_token_created
from .models import (
    Course, Lesson, UserProgress,
    UserProfile, Quiz, Achievement, UserAchievement, QuizAttempt
)
from .serializers import UserProfileSerializer, CourseSerializer, QuizSerializer


# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────
@api_view(['POST'])
def register(request):
    """Handles JWT user registration."""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if not username or not password or not email:
        return Response({'error': 'All fields are required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username taken'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already in use'}, status=400)

    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        UserProfile.objects.create(user=user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': username,
        }, status=201)

    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ─────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Returns full profile data for Flutter HomePage."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    serializer = UserProfileSerializer(profile)
    return Response(serializer.data)


# ─────────────────────────────────────────
# FULL STATS
# ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """Full stats for profile page."""
    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        completed_lessons = UserProgress.objects.filter(
            user=request.user,
            completed=True
        ).count()

        total_courses = Course.objects.count()
        completed_courses = 0

        for course in Course.objects.all():
            total = course.lessons.count()
            done = UserProgress.objects.filter(
                user=request.user,
                lesson__course=course,
                completed=True
            ).count()
            if total > 0 and done == total:
                completed_courses += 1

        # Get earned achievements
        achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement')

        achievement_data = []
        for ua in achievements:
            achievement_data.append({
                'title': ua.achievement.title,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'earned_at': ua.earned_at,
            })

        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'level': profile.level,
            'xp': profile.xp,
            'streak': profile.streak,
            'completed_lessons': completed_lessons,
            'completed_courses': completed_courses,
            'total_courses': total_courses,
            'achievements': achievement_data,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ─────────────────────────────────────────
# STREAK UPDATE
# ─────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_streak(request):
    """Call this every time user opens the app."""
    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.update_streak()
        return Response({
            'streak': profile.streak,
            'message': 'Streak updated!',
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ─────────────────────────────────────────
# COURSES
# ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_courses(request):
    """Lists all courses with user-specific progress counts."""
    courses = Course.objects.all()
    data = []
    for course in courses:
        total_lessons = course.lessons.count()
        completed_lessons = UserProgress.objects.filter(
            user=request.user,
            lesson__course=course,
            completed=True
        ).count()
        data.append({
            'id': course.id,
            'title': course.title,
            'language': course.language,
            'description': course.description,
            'level': course.level,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_detail(request, id):
    """Fetches lessons for a specific course with completion status."""
    try:
        course = Course.objects.get(id=id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=404)

    lessons = course.lessons.order_by('order')
    data = []
    for lesson in lessons:
        completed = UserProgress.objects.filter(
            user=request.user,
            lesson=lesson,
            completed=True
        ).exists()

        # Check if lesson has quiz
        has_quiz = lesson.quizzes.exists()

        data.append({
            'id': lesson.id,
            'title': lesson.title,
            'content': lesson.content,
            'order': lesson.order,
            'xp_reward': lesson.xp_reward,
            'completed': completed,
            'has_quiz': has_quiz,   # 👈 tells Flutter whether to show quiz button
        })

    return Response({
        'id': course.id,
        'title': course.title,
        'language': course.language,
        'description': course.description,
        'level': course.level,
        'lessons': data,
    })


# ─────────────────────────────────────────
# LESSONS
# ─────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_lesson(request, id):
    """Marks lesson as done and awards XP."""
    try:
        lesson = Lesson.objects.get(id=id)
    except Lesson.DoesNotExist:
        return Response({'error': 'Lesson not found'}, status=404)

    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
    )

    # ✅ Only award XP if first time completing
    if not progress.completed:
        progress.completed = True
        progress.save()

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.add_xp(lesson.xp_reward)  # handles leveling + achievements

        profile.update_streak()  # ✅ called only ONCE

        return Response({
            'message': 'Lesson completed!',
            'xp_earned': lesson.xp_reward,
            'total_xp': profile.xp,
            'level': profile.level,
            'streak': profile.streak,
            'already_completed': False,
        })

    # ✅ Already completed — no XP awarded
    profile = UserProfile.objects.get(user=request.user)
    return Response({
        'message': 'Already completed',
        'xp_earned': 0,
        'total_xp': profile.xp,
        'level': profile.level,
        'streak': profile.streak,
        'already_completed': True,  # 👈 tells Flutter no XP was given
    })
# ─────────────────────────────────────────
# QUIZ
# ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_quiz(request, lesson_id):
    """Get all quiz questions for a lesson — never sends correct_answer."""
    try:
        quizzes = Quiz.objects.filter(
            lesson_id=lesson_id
        ).order_by('order')

        if not quizzes.exists():
            return Response(
                {'error': 'No quiz found for this lesson'},
                status=404
            )

        data = []
        for quiz in quizzes:
            data.append({
                'id': quiz.id,
                'question': quiz.question,
                'option_a': quiz.option_a,
                'option_b': quiz.option_b,
                'option_c': quiz.option_c,
                'option_d': quiz.option_d,
                'correct_answer': quiz.correct_answer, # 👈 needed for instant feedback
                
                
                'explanation': quiz.explanation,

                # ⚠️ correct_answer NOT included for security
            })

        return Response({
            'lesson_id': lesson_id,
            'total_questions': len(data),
            'questions': data,
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request, lesson_id):
    try:
        answers = request.data.get('answers', {})
        quizzes = Quiz.objects.filter(
            lesson_id=lesson_id
        ).order_by('order')

        if not quizzes.exists():
            return Response({'error': 'No quiz found'}, status=404)

        total = quizzes.count()
        correct = 0
        results = []

        for quiz in quizzes:
            user_answer = answers.get(str(quiz.id), '').lower()
            is_correct = user_answer == quiz.correct_answer.lower()
            if is_correct:
                correct += 1
            results.append({
                'question_id': quiz.id,
                'question': quiz.question,
                'your_answer': user_answer,
                'correct_answer': quiz.correct_answer,
                'is_correct': is_correct,
            })

        score_percent = int((correct / total) * 100) if total > 0 else 0

        # ✅ Get or create attempt record
        attempt, created = QuizAttempt.objects.get_or_create(
            user=request.user,
            lesson_id=lesson_id,
        )

        attempt.attempts += 1
        if score_percent > attempt.best_score:
            attempt.best_score = score_percent
        attempt.save()

        xp_earned = 0
        is_retry = not created and attempt.xp_awarded

        # ✅ Only award XP on very first attempt ever
        if not attempt.xp_awarded:
            if score_percent == 100:
                xp_earned = 30
            elif score_percent >= 80:
                xp_earned = 20
            elif score_percent >= 60:
                xp_earned = 10
            elif score_percent >= 40:
                xp_earned = 5

            if xp_earned > 0:
                profile, _ = UserProfile.objects.get_or_create(
                    user=request.user
                )
                profile.add_xp(xp_earned)
                # ✅ Mark as awarded — never awards again
                attempt.xp_awarded = True
                attempt.save()

        profile = UserProfile.objects.get(user=request.user)

        return Response({
            'total': total,
            'correct': correct,
            'score_percent': score_percent,
            'xp_earned': xp_earned,       # 0 on retry
            'total_xp': profile.xp,
            'level': profile.level,
            'passed': score_percent >= 60,
            'best_score': attempt.best_score,
            'attempt_number': attempt.attempts,
            'is_retry': is_retry,          # ✅ tells Flutter no XP
            'results': results,
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)
# ─────────────────────────────────────────
# ACHIEVEMENTS
# ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_achievements(request):
    """Returns all achievements with earned status for current user."""
    try:
        all_achievements = Achievement.objects.all().order_by('xp_required')
        earned_ids = UserAchievement.objects.filter(
            user=request.user
        ).values_list('achievement_id', flat=True)

        data = []
        for achievement in all_achievements:
            data.append({
                'id': achievement.id,
                'title': achievement.title,
                'description': achievement.description,
                'icon': achievement.icon,
                'xp_required': achievement.xp_required,
                'earned': achievement.id in earned_ids,  # 👈 tells Flutter if earned
            })

        return Response(data)

    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ─────────────────────────────────────────
# FORGOT PASSWORD EMAIL
# ─────────────────────────────────────────
@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    # Get the token key (already generated by the library)
    token = reset_password_token.key

    send_mail(
        subject="CodeLeap — Password Reset Code",
        message=f"""
Hi {reset_password_token.user.username},

Your password reset code is:

━━━━━━━━━━━━━━━
    {token}
━━━━━━━━━━━━━━━

Enter this code in the CodeLeap app to reset your password.
This code expires in 24 hours.

If you did not request this, ignore this email.

— CodeLeap Team
        """,
        from_email='buyerrequest111@gmail.com',
        recipient_list=[reset_password_token.user.email],
        fail_silently=False,
    )