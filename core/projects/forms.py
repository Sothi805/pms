from django import forms
from django.contrib.auth import get_user_model

from .models import Project, ProjectCategory, ProjectNote

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


class ProjectForm(forms.ModelForm):
    members_search = forms.CharField(
        label="Members (Full Access)",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search users, separated by commas (e.g., john, jane@email.com)",
            "autocomplete": "off",
            "data-field-type": "user-search-multi",
        }),
    )
    commenters_search = forms.CharField(
        label="Commenters (View + Comment)",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search users, separated by commas",
            "autocomplete": "off",
            "data-field-type": "user-search-multi",
        }),
    )
    viewers_search = forms.CharField(
        label="Viewers (Read Only)",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search users, separated by commas",
            "autocomplete": "off",
            "data-field-type": "user-search-multi",
        }),
    )

    class Meta:
        model = Project
        fields = ["name", "description", "organization"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Project name"}
            ),
            "description": forms.Textarea(
                attrs={"class": GLASS_INPUT, "placeholder": "Description", "rows": 3}
            ),
            "organization": forms.Select(attrs={"class": GLASS_SELECT}),
        }

    def clean_members_search(self):
        return self._process_user_search("members_search", "members")
    
    def clean_commenters_search(self):
        return self._process_user_search("commenters_search", "commenters")
    
    def clean_viewers_search(self):
        return self._process_user_search("viewers_search", "viewers")
    
    def _process_user_search(self, search_field, model_field):
        """Parse comma-separated user search and convert to user objects."""
        search_text = self.cleaned_data.get(search_field, "").strip()
        if not search_text:
            self.cleaned_data[model_field] = []
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
            users.append(user)
        
        self.cleaned_data[model_field] = users
        return search_text
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Set M2M relationships
            members = self.cleaned_data.get("members", [])
            if members:
                instance.members.set(members)
            else:
                instance.members.clear()
            
            commenters = self.cleaned_data.get("commenters", [])
            if commenters:
                instance.commenters.set(commenters)
            else:
                instance.commenters.clear()
            
            viewers = self.cleaned_data.get("viewers", [])
            if viewers:
                instance.viewers.set(viewers)
            else:
                instance.viewers.clear()
        return instance


class ProjectNoteForm(forms.ModelForm):
    class Meta:
        model = ProjectNote
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": GLASS_INPUT,
                    "placeholder": "Add a note...",
                    "rows": 3,
                }
            ),
        }


class ProjectCategoryForm(forms.ModelForm):
    class Meta:
        model = ProjectCategory
        fields = ["name", "description", "weight"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Category name (e.g., Frontend, Backend)"}
            ),
            "description": forms.Textarea(
                attrs={"class": GLASS_INPUT, "placeholder": "Description (optional)", "rows": 2}
            ),
            "weight": forms.NumberInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Weight (1-100)", "min": "1", "max": "100"}
            ),
        }
