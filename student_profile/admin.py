from django.contrib import admin
from .models import StudentProfile, Education, LanguageTest, StudentTravelHistory, StudentFinancialProfile

class EducationInline(admin.StackedInline):
    model = Education
    extra = 0
    classes = ['collapse']

class LanguageTestInline(admin.TabularInline):
    model = LanguageTest
    extra = 0
    classes = ['collapse']

class StudentTravelHistoryInline(admin.TabularInline):
    model = StudentTravelHistory
    extra = 0
    classes = ['collapse']

class StudentFinancialProfileInline(admin.StackedInline):
    model = StudentFinancialProfile
    can_delete = False
    verbose_name_plural = 'Financial Profile'
    classes = ['collapse']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'nationality', 'created_at')
    search_fields = ('user__email', 'first_name', 'last_name', 'passport_number')
    list_filter = ('gender', 'marital_status', 'nationality')
    inlines = [EducationInline, LanguageTestInline, StudentTravelHistoryInline, StudentFinancialProfileInline]
