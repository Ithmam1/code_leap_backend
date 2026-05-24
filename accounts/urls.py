from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [

    # ─────────────────────────────────────────
    # AUTH
    # ─────────────────────────────────────────
    path('register/', views.register),
    path('login/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),

    # ─────────────────────────────────────────
    # USER
    # ─────────────────────────────────────────
    path('profile/', views.profile),
    path('stats/', views.get_user_stats),
    path('streak/', views.update_streak),

    # ─────────────────────────────────────────
    # PASSWORD RESET
    # ─────────────────────────────────────────
    path('password-reset/', include(
        'django_rest_passwordreset.urls',
        namespace='password_reset'
    )),

    # ─────────────────────────────────────────
    # COURSES
    # ─────────────────────────────────────────
    path('courses/', views.get_courses),
    path('courses/<int:id>/', views.get_course_detail),

    # ─────────────────────────────────────────
    # LESSONS
    # ─────────────────────────────────────────
    path('lesson/<int:id>/complete/', views.complete_lesson),

    # ─────────────────────────────────────────
    # QUIZ
    # ─────────────────────────────────────────
    path('lesson/<int:lesson_id>/quiz/', views.get_lesson_quiz),
    path('lesson/<int:lesson_id>/submit/', views.submit_quiz),

    # ─────────────────────────────────────────
    # ACHIEVEMENTS
    # ─────────────────────────────────────────
    path('achievements/', views.get_achievements),
]