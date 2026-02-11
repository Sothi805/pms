from django import forms
from django.contrib.auth import get_user_model
from django.utils.html import format_html

User = get_user_model()


class SearchableUserSelectWidget(forms.Widget):
    """Searchable single user selection widget."""
    
    template_name = 'widgets/searchable_user_select.html'
    
    class Media:
        js = ('js/searchable_user_select.js',)
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        
        attrs['class'] = attrs.get('class', '') + ' searchable-user-select'
        attrs['data-name'] = name
        
        selected_user = None
        if value:
            try:
                selected_user = User.objects.get(pk=value)
            except (User.DoesNotExist, ValueError, TypeError):
                pass
        
        # Get all active users for the dropdown
        users = User.objects.filter(is_active=True).values('id', 'username', 'email').order_by('username')
        users_json = list(users)
        
        html = f'''
        <div class="searchable-user-select-wrapper">
            <input type="hidden" name="{name}" class="selected-user-id" value="{value or ''}">
            <input type="text" 
                   placeholder="Search users..." 
                   class="searchable-user-input {attrs.get('class', '')}"
                   data-field-name="{name}"
                   data-users='{forms.utils.json.dumps(users_json)}'
                   autocomplete="off">
            <div class="search-results-dropdown hidden"></div>
            <div class="selected-user-display" data-user-id="{value or ''}">
                {f'<span class="selected-badge">{selected_user.username} ({selected_user.email})</span>' if selected_user else ''}
            </div>
        </div>
        '''
        return format_html(html)


class SearchableUserMultiSelectWidget(forms.Widget):
    """Searchable multiple user selection widget."""
    
    template_name = 'widgets/searchable_user_multiselect.html'
    
    class Media:
        js = ('js/searchable_user_multiselect.js',)
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        
        attrs['class'] = attrs.get('class', '') + ' searchable-user-multiselect'
        attrs['data-name'] = name
        
        # Parse selected users
        selected_users = []
        if value:
            if isinstance(value, (list, tuple)):
                user_ids = value
            else:
                user_ids = [value]
            
            selected_users = list(User.objects.filter(pk__in=user_ids, is_active=True).values('id', 'username', 'email'))
        
        # Get all active users for filtering
        users = User.objects.filter(is_active=True).values('id', 'username', 'email').order_by('username')
        users_json = list(users)
        
        # Build selected users display
        selected_display = ''.join([
            f'<span class="selected-user-badge" data-user-id="{u['id']}">{u["username"]} ({u["email"]}) <button type="button" class="remove-user" onClick="this.parentElement.remove();">×</button></span>'
            for u in selected_users
        ])
        
        # Build hidden inputs for selected users
        hidden_inputs = ''.join([
            f'<input type="hidden" name="{name}" value="{u['id']}">'
            for u in selected_users
        ])
        
        html = f'''
        <div class="searchable-user-multiselect-wrapper">
            {hidden_inputs}
            <input type="text" 
                   placeholder="Search and select users..." 
                   class="searchable-user-input {attrs.get('class', '')}"
                   data-field-name="{name}"
                   data-users='{forms.utils.json.dumps(users_json)}'
                   autocomplete="off">
            <div class="search-results-dropdown hidden"></div>
            <div class="selected-users-display">
                {selected_display}
            </div>
        </div>
        '''
        return format_html(html)
