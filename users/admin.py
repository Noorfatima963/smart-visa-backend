from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from .models import CustomUser
from student_profile.models import StudentProfile


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number')


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    # Fieldsets for the change (edit) view
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fieldsets for the add (create) view
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'get_groups')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

    inlines = (StudentProfileInline,)

    def get_inlines(self, request, obj=None):
        # Only show StudentProfile inline when editing an existing non-staff user
        if obj is None or obj.is_staff or obj.is_superuser:
            return []
        return self.inlines

    def save_model(self, request, obj, form, change):
        # Prevent signal from auto-creating a StudentProfile for admin-panel users
        obj._skip_student_profile = True
        super().save_model(request, obj, form, change)

    @admin.display(description='Groups')
    def get_groups(self, obj):
        return ', '.join(obj.groups.values_list('name', flat=True)) or '—'


# Re-register Group with a cleaner admin that shows member count
admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    list_display = ('name', 'member_count')
    search_fields = ('name',)

    @admin.display(description='Members')
    def member_count(self, obj):
        return obj.user_set.count()

