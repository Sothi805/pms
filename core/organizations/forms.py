from django import forms

from .models import Organization
from accounts.models import User

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


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Organization name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": GLASS_INPUT,
                    "placeholder": "Description",
                    "rows": 3,
                }
            ),
        }


class OrganizationMembersForm(forms.ModelForm):
    members_search = forms.CharField(
        label="Members",
        required=False,
        widget=forms.TextInput(attrs={
            "class": GLASS_INPUT + " user-search-field",
            "placeholder": "Search users, separated by commas (e.g., john, jane@email.com)",
            "autocomplete": "off",
            "data-field-type": "user-search-multi",
        }),
    )

    class Meta:
        model = Organization
        fields = []

    # No need to pre-populate since we're adding members incrementally, not replacing

    def clean_members_search(self):
        search_text = self.cleaned_data.get("members_search", "").strip()
        if not search_text:
            self.cleaned_data["members"] = []
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
            
            # Don't add System Administrators to organization members
            if user.is_superuser:
                raise forms.ValidationError(
                    f"User '{search}' is a System Administrator and cannot be added as a member."
                )
            
            users.append(user)
        
        self.cleaned_data["members"] = users
        return search_text

    # Note: save() is not used anymore - we handle member addition in the view
    # This keeps the form simple and allows incremental member additions
