from rest_framework import serializers
from .models import University, UniversityProgram


class UniversityProgramSerializer(serializers.ModelSerializer):
    total_first_year_cost = serializers.ReadOnlyField()
    required_documents_list = serializers.ReadOnlyField()

    class Meta:
        model = UniversityProgram
        fields = [
            'id',
            'program_name',
            'department',
            'degree_type',
            'degree_name',
            'is_stem',
            # Language requirements
            'ielts_required',
            'toefl_required',
            'pte_required',
            'duolingo_required',
            # Academic requirements
            'min_gpa',
            'max_backlogs',
            'gre_required',
            'gmat_required',
            # Financial
            'tuition_fee_per_year',
            'estimated_living_cost',
            'total_first_year_cost',
            'application_fee',
            'app_fee_waiver_available',
            # Admission stats
            'acceptance_rate',
            # Program details
            'duration_months',
            'num_credits',
            'semester',
            'application_deadline',
            # Docs & links
            'required_documents_list',
            'application_link',
            'department_link',
            # Scholarships
            'total_scholarships',
            'total_scholarship_amount',
        ]


class UniversityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no nested programs."""
    program_count = serializers.SerializerMethodField()

    class Meta:
        model = University
        fields = [
            'id',
            'name',
            'university_type',
            'city',
            'state_province',
            'country',
            'qs_world_ranking',
            'us_news_ranking',
            'offers_financial_aid',
            'program_count',
        ]

    def get_program_count(self, obj):
        return obj.programs.count()


class UniversityDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view — includes nested programs."""
    programs = UniversityProgramSerializer(many=True, read_only=True)
    program_count = serializers.SerializerMethodField()

    class Meta:
        model = University
        fields = [
            'id',
            'external_id',
            'uni_no',
            'name',
            'university_type',
            'city',
            'state_province',
            'country',
            'qs_world_ranking',
            'us_news_ranking',
            'phone',
            'website',
            'offers_financial_aid',
            'program_count',
            'programs',
            'created_at',
            'updated_at',
        ]

    def get_program_count(self, obj):
        return obj.programs.count()