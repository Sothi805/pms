from django.conf import settings
from django.db import models


class ProjectCategory(models.Model):
    """Custom project-specific categories with weight contribution to project progress."""

    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weight = models.PositiveIntegerField(
        default=1,
        help_text="Weight (1-100) used to calculate this category's contribution to project progress.",
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order of this category.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        unique_together = ["project", "name"]
        verbose_name_plural = "Project Categories"

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    @property
    def total_tasks(self):
        """Count of all tasks in this project category."""
        return self.tasks.filter(is_closed=False).count()

    @property
    def done_tasks(self):
        """Count of completed (DONE stage) tasks in this project category."""
        from tasks.models import TaskInstance
        return self.tasks.filter(
            is_closed=False, stage=TaskInstance.DONE
        ).count()

    @property
    def completion_percentage(self):
        """Percentage of completed tasks in this category (0-100)."""
        total = self.total_tasks
        if total == 0:
            return 0
        done = self.done_tasks
        return round((done / total) * 100)


class Project(models.Model):
    """Project belongs to exactly one organization."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="projects",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="member_projects",
        help_text="Full access: can edit tasks, move between stages, create tasks."
    )
    commenters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="commenter_projects",
        help_text="Can view all tasks and add comments/notes to project and tasks.",
    )
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="viewer_projects",
        help_text="Read-only access to view all project information.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["organization", "name"]

    def __str__(self):
        return self.name

    @property
    def progress(self):
        """Weighted project progress based on custom project categories.
        
        Weight represents direct percentage contribution:
        - Weight 5 = 5% of project progress when 100% complete
        - Weight 40 = 40% of project progress when 100% complete
        
        Total project progress = sum of (category_completion% × category_weight) / 100
        """
        categories = self.categories.all()
        
        if not categories.exists():
            return 0
        
        weighted_progress = sum(
            (cat.completion_percentage * cat.weight) for cat in categories
        )
        return min(round(weighted_progress / 100), 100)  # Cap at 100%

    @property
    def task_stats(self):
        from tasks.models import TaskInstance
        from django.db.models import Sum

        tasks = TaskInstance.objects.filter(project=self, is_closed=False)
        done_tasks = tasks.filter(stage=TaskInstance.DONE)
        
        total_sp = tasks.aggregate(Sum('story_points'))['story_points__sum'] or 0
        earned_sp = done_tasks.aggregate(Sum('story_points'))['story_points__sum'] or 0
        
        return {
            "total": tasks.count(),
            "done": done_tasks.count(),
            "in_progress": tasks.filter(stage=TaskInstance.IN_PROGRESS).count(),
            "having_issues": tasks.filter(stage=TaskInstance.HAVING_ISSUES).count(),
            "total_story_points": total_sp,
            "earned_story_points": earned_sp,
            "remaining_story_points": total_sp - earned_sp,
        }

    @property
    def tasks_by_project_category(self):
        """Tasks grouped by project category with completion stats and weights."""
        return list(
            self.categories.prefetch_related("tasks").order_by("order", "-created_at")
        )

    def user_is_member(self, user):
        """Check if user has member access to this project.
        
        System Administrators and project organization Administrators are automatically members.
        """
        if user.is_system_admin():
            return True
        if user.is_org_admin(self.organization):
            return True
        return self.members.filter(pk=user.pk).exists()

    def user_is_commenter(self, user):
        """Check if user has commenter access to this project.
        
        System Administrators are automatically members (which includes commenter access).
        """
        if user.is_system_admin():
            return True
        if user.is_org_admin(self.organization):
            return True
        return self.commenters.filter(pk=user.pk).exists() or self.members.filter(pk=user.pk).exists()

    def user_is_viewer(self, user):
        """Check if user has viewer access to this project.
        
        System Administrators are automatically members (which includes all access levels).
        """
        if user.is_system_admin():
            return True
        if user.is_org_admin(self.organization):
            return True
        return (
            self.viewers.filter(pk=user.pk).exists()
            or self.commenters.filter(pk=user.pk).exists()
            or self.members.filter(pk=user.pk).exists()
        )

    def user_has_any_access(self, user):
        """Check if user has any access to this project (member, commenter, or viewer).
        
        System Administrators have access to all projects.
        """
        if user.is_system_admin():
            return True
        if user.is_org_admin(self.organization):
            return True
        return (
            self.members.filter(pk=user.pk).exists()
            or self.commenters.filter(pk=user.pk).exists()
            or self.viewers.filter(pk=user.pk).exists()
        )


class ProjectNote(models.Model):
    """User notes on project detail page. Editable and deletable."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note by {self.author} on {self.project}"
