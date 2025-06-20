from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'amount', 'status', 'created_at', 'paid_at', 'released_at', 'refunded_at')
    list_filter = ('status', 'created_at', 'paid_at', 'released_at', 'refunded_at')
    search_fields = ('project__title', 'transaction_id_provider')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('project',)
    
    fieldsets = (
        (None, {
            'fields': ('id', 'project', 'amount', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at', 'released_at', 'refunded_at')
        }),
        ('Payment Provider Details', {
            'fields': ('payment_provider', 'transaction_id_provider'),
        })
    )
