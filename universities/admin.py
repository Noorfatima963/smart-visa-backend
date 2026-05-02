from django.contrib import admin
from .models import University, UniversityProgram


class UniversityProgramInline(admin.TabularInline):
    model = UniversityProgram
    extra = 0
    fields = [
        'program_name', 'degree_type', 'is_stem',
        'ielts_required', 'min_gpa', 'tuition_fee_per_year',
        'acceptance_rate', 'application_deadline'
    ]
    show_change_link = True


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'university_type', 'city', 'state_province',
        'qs_world_ranking', 'us_news_ranking', 'offers_financial_aid', 'program_count'
    ]
    list_filter = ['university_type', 'country', 'offers_financial_aid']
    search_fields = ['name', 'city', 'state_province', 'country']
    inlines = [UniversityProgramInline]
    readonly_fields = ['created_at', 'updated_at']

    def program_count(self, obj):
        return obj.programs.count()
    program_count.short_description = 'Programs'


@admin.register(UniversityProgram)
class UniversityProgramAdmin(admin.ModelAdmin):
    list_display = [
        'program_name', 'degree_type', 'university',
        'ielts_required', 'min_gpa', 'max_backlogs',
        'tuition_fee_per_year', 'acceptance_rate', 'is_stem'
    ]
    list_filter = ['degree_type', 'is_stem', 'semester', 'university__university_type']
    search_fields = ['program_name', 'department', 'university__name']
    autocomplete_fields = ['university']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Program Identity', {
            'fields': ('university', 'program_name', 'department', 'degree_type', 'degree_name', 'is_stem')
        }),
        ('Language Requirements', {
            'fields': ('ielts_required', 'toefl_required', 'pte_required', 'duolingo_required')
        }),
        ('Academic Requirements', {
            'fields': ('min_gpa', 'max_backlogs', 'gre_required', 'gmat_required')
        }),
        ('Financial', {
            'fields': ('tuition_fee_per_year', 'estimated_living_cost', 'application_fee', 'app_fee_waiver_available')
        }),
        ('Admission Stats', {
            'fields': ('acceptance_rate', 'duration_months', 'num_credits', 'semester', 'application_deadline')
        }),
        ('Scholarships', {
            'fields': ('total_scholarships', 'total_scholarship_amount')
        }),
        ('Links & Documents', {
            'fields': ('application_link', 'department_link', 'required_documents_raw'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )