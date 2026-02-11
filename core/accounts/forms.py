from django import forms
from django.contrib.auth import get_user_model

from .models import Role

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

GLASS_CHECKBOX = "rounded border-white/20 bg-white/5 text-blue-500 focus:ring-blue-500/50"


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Enter username or email",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Enter password",
                "autocomplete": "current-password",
            }
        ),
    )


class UserCreateForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": GLASS_SELECT}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role"]
        widgets = {
            "username": forms.TextInput(attrs={"class": GLASS_INPUT, "placeholder": "Username"}),
            "email": forms.EmailInput(attrs={"class": GLASS_INPUT, "placeholder": "Email"}),
            "first_name": forms.TextInput(
                attrs={"class": GLASS_INPUT, "placeholder": "First name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": GLASS_INPUT, "placeholder": "Last name"}
            ),
        }


class UserEditForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": GLASS_SELECT}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": GLASS_INPUT}),
            "email": forms.EmailInput(attrs={"class": GLASS_INPUT}),
            "first_name": forms.TextInput(attrs={"class": GLASS_INPUT}),
            "last_name": forms.TextInput(attrs={"class": GLASS_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": GLASS_CHECKBOX}),
        }


class PermissionOverrideForm(forms.ModelForm):
    """Override individual permissions for a user."""

    class Meta:
        model = User
        fields = [
            "perm_create_users",
            "perm_manage_projects",
            "perm_manage_tasks",
            "perm_move_task_stages",
            "perm_move_task_categories",
            "perm_reject_testing",
            "perm_add_project_notes",
            "perm_view_assigned_only",
            "perm_manage_organizations",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget = forms.NullBooleanSelect(
                attrs={"class": GLASS_SELECT}
            )
            field.label = field_name.replace("perm_", "").replace("_", " ").title()

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Enter current password",
                "autocomplete": "current-password",
            }
        ),
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Enter new password",
                "autocomplete": "new-password",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Confirm new password",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class SetPasswordForm(forms.Form):
    """Superuser manually sets a password for any user (no verification)."""
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Enter new password",
                "autocomplete": "new-password",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": GLASS_INPUT,
                "placeholder": "Confirm new password",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")

        return cleaned_data