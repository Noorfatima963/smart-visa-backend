from django.contrib import admin
from .models import VisaAssessment, UniversityMatch


class UniversityMatchInline(admin.TabularInline):
    model = UniversityMatch
    extra = 0
    readonly_fields = [
        'rank', 'program', 'probability_score', 'eligibility',
        'gpa_score', 'language_score', 'financial_score',
        'backlog_score', 'visa_history_score', 'acceptance_rate_score',
    ]
    fields = [
        'rank', 'program', 'probability_score', 'eligibility',
        'gpa_score', 'language_score', 'financial_score',
        'backlog_score', 'visa_history_score',
    ]
    show_change_link = True
    can_delete = False
    max_num = 0


@admin.register(VisaAssessment)
class VisaAssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'target_country', 'target_degree_type', 'target_field',
        'overall_score', 'total_matches_found', 'total_programs_evaluated',
        'status', 'created_at'
    ]
    list_filter = ['target_country', 'target_degree_type', 'status', 'created_at']
    search_fields = ['user__email', 'target_field']
    readonly_fields = [
        'user', 'overall_score', 'total_programs_evaluated', 'total_matches_found',
        'score_breakdown', 'profile_snapshot', 'missing_factors', 'created_at'
    ]
    inlines = [UniversityMatchInline]
    fieldsets = (
        ('Request', {
            'fields': ('user', 'target_country', 'target_degree_type', 'target_field')
        }),
        ('Results', {
            'fields': ('status', 'overall_score', 'total_programs_evaluated', 'total_matches_found')
        }),
        ('Score Breakdown', {
            'fields': ('score_breakdown',),
            'classes': ('collapse',)
        }),
        ('Profile Snapshot', {
            'fields': ('profile_snapshot', 'missing_factors'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UniversityMatch)
class UniversityMatchAdmin(admin.ModelAdmin):
    list_display = [
        'rank', 'assessment', 'program', 'probability_score', 'eligibility'
    ]
    list_filter = ['eligibility', 'assessment__target_country']
    search_fields = ['program__university__name', 'program__program_name']
    readonly_fields = ['assessment', 'program', 'rank', 'probability_score', 'eligibility']
