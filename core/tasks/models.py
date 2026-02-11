from django.conf import settings
from django.db import models


class TaskInstance(models.Model):
    """Atomic unit of work. A logical work item may have multiple instances."""

    # ── Categories (workflow lanes) ──
    DEVELOPMENT = "DEVELOPMENT"
    IMPLEMENTATION = "IMPLEMENTATION"
    IMPROVEMENT = "IMPROVEMENT"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    GENERAL = "GENERAL"

    CATEGORY_CHOICES = [
        (DEVELOPMENT, "Development"),
        (IMPLEMENTATION, "Implementation"),
        (IMPROVEMENT, "Improvement"),
        (TESTING, "Testing"),
        (DEPLOYMENT, "Deployment"),
        (GENERAL, "General"),
    ]

    BUILD_CATEGORIES = [DEVELOPMENT, IMPLEMENTATION, IMPROVEMENT]

    # ── Stages (execution state) ──
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    HAVING_ISSUES = "HAVING_ISSUES"
    DONE = "DONE"
    REJECT = "REJECT"

    STAGE_CHOICES = [
        (TODO, "To Do"),
        (IN_PROGRESS, "In Progress"),
        (PENDING, "Pending"),
        (HAVING_ISSUES, "Having Issues"),
        (DONE, "Done"),
        (REJECT, "Reject"),
    ]

    # ── Identity ──
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    project_category = models.ForeignKey(
        "projects.ProjectCategory",
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
        help_text="Project-specific category this task belongs to.",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=DEVELOPMENT)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=TODO)

    # ── People ──
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="assigned_tasks",
        help_text="Users working on this task."
    )

    # ── Metrics ──
    story_points = models.PositiveIntegerField(default=0)
    points_earned = models.BooleanField(
        default=False, help_text="True once points are awarded."
    )
    deadline = models.DateField(null=True, blank=True)

    # ── Lineage ──
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        help_text="The task this was cloned from.",
    )
    original_category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        blank=True,
        help_text="Original category before cloning to testing.",
    )
    is_closed = models.BooleanField(default=False)

    # ── Timestamps ──
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    @property
    def stage_color(self):
        return {
            self.TODO: "bg-slate-500/30 text-slate-300",
            self.IN_PROGRESS: "bg-blue-500/30 text-blue-300",
            self.PENDING: "bg-yellow-500/30 text-yellow-300",
            self.HAVING_ISSUES: "bg-orange-500/30 text-orange-300",
            self.DONE: "bg-emerald-500/30 text-emerald-300",
            self.REJECT: "bg-red-500/30 text-red-300",
        }.get(self.stage, "bg-white/10 text-white/70")

    @property
    def category_color(self):
        return {
            self.DEVELOPMENT: "border-blue-400/40",
            self.IMPLEMENTATION: "border-purple-400/40",
            self.IMPROVEMENT: "border-cyan-400/40",
            self.TESTING: "border-amber-400/40",
            self.DEPLOYMENT: "border-emerald-400/40",
            self.GENERAL: "border-slate-400/40",
        }.get(self.category, "border-white/20")


class TaskNote(models.Model):
    """User notes/comments on task detail page. Editable and deletable."""

    task = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note by {self.author} on {self.task}"
