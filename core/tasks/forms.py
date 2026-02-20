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


class DateInput(forms.DateInput):
    """Custom date input widget with dd/mm/yyyy format."""
    input_type = 'text'
    
    def __init__(self, attrs=None, format=None):
        default_attrs = {
            'placeholder': 'dd/mm/yyyy',
            'pattern': r'\d{2}/\d{2}/\d{4}',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format='%d/%m/%Y')
    
    def format_value(self, value):
        """Format date value as dd/mm/yyyy for display."""
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        return value.strftime('%d/%m/%Y') if hasattr(value, 'strftime') else value


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
    coordinator_search = forms.CharField(
        label="Coordinator",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search coordinator by username or email",
            "autocomplete": "off",
            "data-field-type": "user-search-single",
        }),
    )
    
    deadline = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%Y'],
        widget=DateInput(attrs={"class": GLASS_INPUT})
    )
    
    start_date = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%Y'],
        widget=DateInput(attrs={"class": GLASS_INPUT})
    )
    
    end_date = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%Y'],
        widget=DateInput(attrs={"class": GLASS_INPUT})
    )

    class Meta:
        model = TaskInstance
        fields = [
            "title",
            "description",
            "category",
            "project_category",
            "story_points",
            "deadline",
            "start_date",
            "end_date",
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
            "story_points": forms.NumberInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Story points", "min": 0}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if self.instance.pk:
            if self.instance.assignees.exists():
                assignee_names = ", ".join(self.instance.assignees.values_list("username", flat=True))
                self.fields["assignees_search"].initial = assignee_names
            if self.instance.coordinator:
                self.fields["coordinator_search"].initial = self.instance.coordinator.username

    def clean_coordinator_search(self):
        search_text = self.cleaned_data.get("coordinator_search", "").strip()
        if not search_text:
            self.cleaned_data["coordinator"] = None
            return search_text

        try:
            user = User.objects.get(username=search_text, is_active=True)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=search_text, is_active=True)
            except User.DoesNotExist:
                user = User.objects.filter(username__icontains=search_text, is_active=True).first()
                if not user:
                    raise forms.ValidationError(f"User '{search_text}' not found.")

        if self.project:
            is_in_project = (
                self.project.members.filter(pk=user.pk).exists() or
                user.is_superuser
            )
            if not is_in_project:
                raise forms.ValidationError(
                    f"User '{search_text}' is not a member of this project."
                )

        self.cleaned_data["coordinator"] = user
        return search_text

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
            instance.coordinator = self.cleaned_data.get("coordinator")
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
