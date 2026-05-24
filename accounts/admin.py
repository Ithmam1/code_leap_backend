from django.contrib import admin
from .models import (
    UserProfile,
    Course,
    Lesson,
    UserProgress,
    Quiz,
    Achievement,
    UserAchievement,
    QuizAttempt,
)


# ─────────────────────────────────────────
# INLINE — Quiz inside Lesson
# ─────────────────────────────────────────
class QuizInline(admin.StackedInline):
    model = Quiz
    extra = 1  # shows 1 empty form by default
    fields = [
        'question',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
        'correct_answer',
        'order',
    ]


# ─────────────────────────────────────────
# INLINE — Lesson inside Course
# ─────────────────────────────────────────
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ['title', 'content', 'order', 'xp_reward']
    show_change_link = True  # 👈 click to open full lesson page with quiz


# ─────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'xp', 'streak', 'last_active']
    list_filter = ['level']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['last_active']
    ordering = ['-xp']


# ─────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'level', 'order', 'lesson_count']
    list_filter = ['language', 'level']
    search_fields = ['title']
    ordering = ['order']
    inlines = [LessonInline]  # 👈 add lessons directly inside course

    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'


# ─────────────────────────────────────────
# LESSON
# ─────────────────────────────────────────
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'xp_reward', 'quiz_count']
    list_filter = ['course', 'course__language']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']
    inlines = [QuizInline]  # 👈 add quiz directly inside lesson

    def quiz_count(self, obj):
        return obj.quizzes.count()
    quiz_count.short_description = 'Questions'


# ─────────────────────────────────────────
# QUIZ
# ─────────────────────────────────────────
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'question_preview',
        'lesson',
        'course_name',
        'correct_answer',
        'order',
    ]
    list_filter = ['lesson__course', 'correct_answer']
    search_fields = ['question', 'lesson__title']
    ordering = ['lesson', 'order']
    fields = [
        'lesson',
        'question',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
        'correct_answer',
        'order',
    ]

    def question_preview(self, obj):
        return obj.question[:60] + '...' if len(obj.question) > 60 else obj.question
    question_preview.short_description = 'Question'

    def course_name(self, obj):
        return obj.lesson.course.title
    course_name.short_description = 'Course'

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'attempts', 'best_score', 'xp_awarded']
    list_filter = ['xp_awarded']
    search_fields = ['user__username']
# ─────────────────────────────────────────
# USER PROGRESS
# ─────────────────────────────────────────
@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'course_name', 'completed', 'completed_at']
    list_filter = ['completed', 'lesson__course']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['completed_at']
    ordering = ['-completed_at']

    def course_name(self, obj):
        return obj.lesson.course.title
    course_name.short_description = 'Course'


# ─────────────────────────────────────────
# ACHIEVEMENT
# ─────────────────────────────────────────
@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['icon', 'title', 'xp_required', 'description_preview']
    search_fields = ['title']
    ordering = ['xp_required']

    def description_preview(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_preview.short_description = 'Description'


# ─────────────────────────────────────────
# USER ACHIEVEMENT
# ─────────────────────────────────────────
@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['achievement']
    search_fields = ['user__username', 'achievement__title']
    readonly_fields = ['earned_at']
    ordering = ['-earned_at']