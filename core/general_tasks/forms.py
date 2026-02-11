from django import forms
from django.contrib.auth import get_user_model

from .models import GeneralTask

User = get_user_model()

GLASS_INPUT = (
    "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 "
    "text-white placeholder-white/40 focus:outline-none focus:ring-2 "
    "focus:ring-blue-500/50 focus:border-blue-500/30 transition-all duration-200"
)

GLASS_SELECT = (
    "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 "
    "text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 "
    "focus:border-blue-500/30 transition-all duration-200 appearance-none"
)

GLASS_TEXTAREA = (
    "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 "
    "text-white placeholder-white/40 focus:outline-none focus:ring-2 "
    "focus:ring-blue-500/50 focus:border-blue-500/30 transition-all duration-200 resize-none"
)


class GeneralTaskForm(forms.ModelForm):
    assigned_to_search = forms.CharField(
        label="Assigned to",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search for a user...",
            "autocomplete": "off",
            "data-field-type": "user-search-single",
        }),
    )
    
    class Meta:
        model = GeneralTask
        fields = ["title", "description", "status", "priority", "due_date"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": GLASS_INPUT,
                "placeholder": "Task title",
            }),
            "description": forms.Textarea(attrs={
                "class": GLASS_TEXTAREA,
                "placeholder": "Task description (optional)",
                "rows": 4,
            }),
            "status": forms.Select(attrs={"class": GLASS_SELECT}),
            "priority": forms.Select(attrs={"class": GLASS_SELECT}),
            "due_date": forms.DateInput(attrs={
                "class": GLASS_INPUT,
                "type": "date",
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial assigned_to_search value if editing
        if self.instance.assigned_to:
            self.fields["assigned_to_search"].initial = f"{self.instance.assigned_to.username} ({self.instance.assigned_to.email})"
    
    def clean_assigned_to_search(self):
        search_text = self.cleaned_data.get("assigned_to_search", "").strip()
        if not search_text:
            self.cleaned_data["assigned_to"] = None
            return search_text
        
        # Try to find user by username or email
        try:
            # First try exact username match
            user = User.objects.get(username=search_text, is_active=True)
        except User.DoesNotExist:
            try:
                # Then try email match
                user = User.objects.get(email=search_text, is_active=True)
            except User.DoesNotExist:
                try:
                    # Try username contains
                    user = User.objects.filter(username__icontains=search_text, is_active=True).first()
                    if not user:
                        raise forms.ValidationError(f"User '{search_text}' not found.")
                except:
                    raise forms.ValidationError(f"User '{search_text}' not found.")
        
        self.cleaned_data["assigned_to"] = user
        return search_text
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.assigned_to = self.cleaned_data.get("assigned_to")
        if commit:
            instance.save()
        return instance
