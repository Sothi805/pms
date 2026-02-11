from django import forms
from django.contrib.auth import get_user_model

from .models import TaskInstance, TaskNote

User = get_user_model()

GLASS_INPUT = (
    "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 "
    "text-white placeholder-white/40 focus:outline-none focus:ring-2 "
    "focus:ring-blue-500/50 focus:border-blue-500/30 transition-all duration-200"
)

GLASS_SELECT = (
    "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 "
    "text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 "
    "focus:border-blue-500/30 transition-all duration-200"
)


class TaskInstanceForm(forms.ModelForm):
    assignees_search = forms.CharField(
        label="Assignees",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search users, separated by commas (e.g., john, jane@email.com)",
            "autocomplete": "off",
            "data-field-type": "user-search-multi",
        }),
    )

    class Meta:
        model = TaskInstance
        fields = [
            "title",
            "description",
            "category",
            "project_category",
            "stage",
            "story_points",
            "deadline",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Task title"}
            ),
            "description": forms.Textarea(
                attrs={"class": GLASS_INPUT, "placeholder": "Description", "rows": 3}
            ),
            "category": forms.Select(attrs={"class": GLASS_SELECT}),
            "project_category": forms.Select(attrs={"class": GLASS_SELECT}),
            "stage": forms.Select(attrs={"class": GLASS_SELECT}),
            "story_points": forms.NumberInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Story points", "min": 0}
            ),
            "deadline": forms.DateInput(
                attrs={"class": GLASS_INPUT, "type": "date"}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if self.instance.pk and self.instance.assignees.exists():
            # Pre-populate search field with current assignees
            assignee_names = ", ".join(self.instance.assignees.values_list("username", flat=True))
            self.fields["assignees_search"].initial = assignee_names

    def clean_assignees_search(self):
        search_text = self.cleaned_data.get("assignees_search", "").strip()
        if not search_text:
            self.cleaned_data["assignees"] = []
            return search_text
        
        # Split by comma to support multiple entries
        user_searches = [s.strip() for s in search_text.split(",") if s.strip()]
        users = []
        
        for search in user_searches:
            try:
                # Try exact username match
                user = User.objects.get(username=search, is_active=True)
            except User.DoesNotExist:
                try:
                    # Try email match
                    user = User.objects.get(email=search, is_active=True)
                except User.DoesNotExist:
                    # Try username contains
                    user = User.objects.filter(username__icontains=search, is_active=True).first()
                    if not user:
                        raise forms.ValidationError(f"User '{search}' not found.")
            
            # If project filtering is needed, validate user is in project
            if self.project:
                is_in_project = (
                    self.project.members.filter(pk=user.pk).exists() or
                    user.is_superuser
                )
                if not is_in_project:
                    raise forms.ValidationError(
                        f"User '{search}' is not a member of this project."
                    )
            
            users.append(user)
        
        self.cleaned_data["assignees"] = users
        return search_text

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            assignees = self.cleaned_data.get("assignees", [])
            if assignees:
                instance.assignees.set(assignees)
            else:
                instance.assignees.clear()
        return instance


class TaskNoteForm(forms.ModelForm):
    class Meta:
        model = TaskNote
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": GLASS_INPUT,
                    "placeholder": "Add a comment or note...",
                    "rows": 3,
                }
            ),
        }
