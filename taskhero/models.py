from django.db import models
from django.conf import settings
from django.utils import timezone


class TaskQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(owner=user)

    def overdue(self):
        today = timezone.localdate()
        return self.filter(due_date__lt=today).exclude(status=Task.STATUS_COMPLETED)

    def by_status(self, status):
        return self.filter(status=status)


class Task(models.Model):
    """Core Task model for TaskHero.

    - owner: links to Django user (keeps tasks private to their creator)
    - title/description: basic text fields
    - due_date: optional date when the task should be finished
    - status: grouped columns on dashboard (TODO / IN_PROGRESS / COMPLETED)
    - priority: Low / Medium / High
    """

    STATUS_TODO = 'TODO'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='tasks',
        on_delete=models.CASCADE,
        help_text='The user who created this task',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        # index owner + status for fast filtering on dashboard
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['due_date']),
        ]
        ordering = ['due_date', '-priority', 'created_at']

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"

    @property
    def is_overdue(self):
        """Return True if the task has passed its due_date and isn't completed."""
        if not self.due_date:
            return False
        if self.status == self.STATUS_COMPLETED:
            return False
        return timezone.localdate() > self.due_date

    def mark_completed(self):
        """Convenience method to mark a task completed and save."""
        self.status = self.STATUS_COMPLETED
        self.save(update_fields=['status', 'updated_at'])

    def get_priority_color(self):
        """Return a presentation-friendly color name for UI mapping.
        (View/template can map these to exact hex/classes.)
        """
        return {
            self.PRIORITY_HIGH: 'red',
            self.PRIORITY_MEDIUM: 'yellow',
            self.PRIORITY_LOW: 'blue',
        }[self.priority]


# Optionally, you can add a short log model or activity feed later:
class TaskActivity(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)  # e.g. 'created', 'marked completed'
    created_at = models.DateTimeField(auto_now_add=True)


