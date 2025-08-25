from django.contrib import admin
from .models import Source, Quote

class QuoteInline(admin.TabularInline):
    model = Quote
    extra = 0
    max_num = 3  # Limit to 3 quotes per source

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_quote_count')
    inlines = [QuoteInline]

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('text', 'source', 'weight', 'views', 'likes', 'dislikes')
    list_filter = ('source', 'weight')
    search_fields = ('text', 'source__name')
    actions = ['add_like', 'add_dislike']
    fieldsets = (
        (None, {
            'fields': ('text', 'source', 'weight', 'views', 'likes', 'dislikes'),
            'description': 'Ensure a source exists before creating a quote.',

        }),
    )

    def add_like(self, request, queryset):
        for quote in queryset:
            quote.likes += 1
            quote.save()
        self.message_user(request, f"Added like to {queryset.count()} quotes.")
    add_like.short_description = "Add like to selected quotes"

    def add_dislike(self, request, queryset):
        for quote in queryset:
            quote.dislikes += 1
            quote.save()
        self.message_user(request, f"Added dislike to {queryset.count()} quotes.")
    add_dislike.short_description = "Add dislike to selected quotes"
