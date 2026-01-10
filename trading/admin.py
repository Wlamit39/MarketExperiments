from django.contrib import admin
from .models import SquareOffRule, TradeLog

# Admin configuration for the SquareOffRule model.
@admin.register(SquareOffRule)
class SquareOffRuleAdmin(admin.ModelAdmin):
    # Fields to display in the list view of the admin.
    list_display = ('symbol', 'lower_limit_price', 'upper_limit_price', 'active', 'triggered_today', 'dry_run', 'kill_switch', 'updated_at')
    # Fields to use for filtering in the admin sidebar.
    list_filter = ('active', 'triggered_today', 'dry_run', 'kill_switch')
    # Fields to use for search functionality in the admin.
    search_fields = ('symbol',)
    # Custom actions available for SquareOffRule objects.
    actions = ['reset_triggered_today']

    def reset_triggered_today(self, request, queryset):
        """Admin action to reset the 'triggered_today' flag for selected rules."""
        queryset.update(triggered_today=False)
        self.message_user(request, "Selected rules' 'triggered_today' flag has been reset.")
    reset_triggered_today.short_description = "Reset 'triggered today' flag for selected rules"

# Admin configuration for the TradeLog model.
@admin.register(TradeLog)
class TradeLogAdmin(admin.ModelAdmin):
    # Fields to display in the list view of the admin.
    list_display = ('timestamp', 'event_type', 'rule', 'message')
    # Fields to use for filtering in the admin sidebar.
    list_filter = ('event_type', 'rule')
    # Fields to use for search functionality in the admin.
    search_fields = ('message', 'rule__symbol')
    # Fields that should not be editable in the admin form.
    readonly_fields = ('timestamp', 'event_type', 'rule', 'message', 'data')
