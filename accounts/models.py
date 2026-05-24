from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    level = models.CharField(default='beginner', max_length=20)
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    last_active = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.level}"

    def update_streak(self):
        """Increment or reset streak based on last activity."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        if self.last_active == yesterday:
            self.streak += 1
        elif self.last_active < yesterday:
            self.streak = 1  # reset if missed a day

        self.save()

    def add_xp(self, amount):
        """Add XP and auto level up."""
        self.xp += amount
        if self.xp >= 500:
            self.level = 'advanced'
        elif self.xp >= 200:
            self.level = 'intermediate'
        else:
            self.level = 'beginner'
        self.save()

        # Auto check achievements after XP update
        self._check_achievements()

    def _check_achievements(self):
        """Auto award achievements when XP threshold is reached."""
        earned_ids = UserAchievement.objects.filter(
            user=self.user
        ).values_list('achievement_id', flat=True)

        eligible = Achievement.objects.filter(
            xp_required__lte=self.xp
        ).exclude(id__in=earned_ids)

        for achievement in eligible:
            UserAchievement.objects.create(
                user=self.user,
                achievement=achievement
            )


class Course(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('java', 'Java'),
        ('c', 'C'),
        ('cpp', 'C++'),
    ]

    title = models.CharField(max_length=100)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    description = models.TextField()
    level = models.CharField(max_length=20, default='beginner')
    order = models.IntegerField(default=0)  # 👈 added — for ordering courses

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.language})"


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='lessons'
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    order = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=10)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name_plural = "User Progress"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"


class Quiz(models.Model):
    ANSWER_CHOICES = [
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
    ]

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name='quizzes'
    )
    question = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(
        max_length=1,
        choices=ANSWER_CHOICES  # 👈 added choices for admin dropdown
    )
    explanation = models.TextField(blank=True, default='') 
    order = models.IntegerField(default=0)  # 👈 added — order questions

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"[{self.lesson.title}] {self.question[:60]}"

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    best_score = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    xp_awarded = models.BooleanField(default=False)  # 👈 key field

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({self.attempts} attempts)"
    


class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # emoji e.g. "🏆"
    xp_required = models.IntegerField(default=0)

    class Meta:
        ordering = ['xp_required']  # 👈 show easiest first in admin

    def __str__(self):
        return f"{self.icon} {self.title} ({self.xp_required} XP)"


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')  # 👈 prevent duplicates

    def __str__(self):
        return f"{self.user.username} earned {self.achievement.title}"