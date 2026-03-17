from rest_framework import serializers
from .models import VisaAssessment, UniversityMatch


class UniversityMatchSerializer(serializers.ModelSerializer):
    """Full match serializer — includes probability breakdown + cost estimate."""

    # University fields
    university_name = serializers.CharField(source='program.university.name', read_only=True)
    university_city = serializers.CharField(source='program.university.city', read_only=True)
    university_state = serializers.CharField(source='program.university.state_province', read_only=True)
    university_type = serializers.CharField(source='program.university.university_type', read_only=True)
    qs_world_ranking = serializers.IntegerField(source='program.university.qs_world_ranking', read_only=True)
    university_website = serializers.CharField(source='program.university.website', read_only=True)

    # Program fields
    program_name = serializers.CharField(source='program.program_name', read_only=True)
    degree_type = serializers.CharField(source='program.degree_type', read_only=True)
    department = serializers.CharField(source='program.department', read_only=True)
    is_stem = serializers.BooleanField(source='program.is_stem', read_only=True)
    duration_months = serializers.IntegerField(source='program.duration_months', read_only=True)
    application_deadline = serializers.DateField(source='program.application_deadline', read_only=True)
    application_link = serializers.CharField(source='program.application_link', read_only=True)
    semester = serializers.CharField(source='program.semester', read_only=True)

    # Raw financial fields (from program — for reference)
    tuition_fee_per_year = serializers.DecimalField(source='program.tuition_fee_per_year',
                                                    max_digits=10, decimal_places=2, read_only=True)
    estimated_living_cost = serializers.DecimalField(source='program.estimated_living_cost',
                                                     max_digits=10, decimal_places=2, read_only=True)
    acceptance_rate = serializers.FloatField(source='program.acceptance_rate', read_only=True)
    total_scholarships = serializers.IntegerField(source='program.total_scholarships', read_only=True)
    total_scholarship_amount = serializers.DecimalField(source='program.total_scholarship_amount',
                                                        max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = UniversityMatch
        fields = [
            'id',
            'rank',

            # Probability
            'probability_score',
            'eligibility',
            'gpa_score',
            'language_score',
            'financial_score',
            'backlog_score',
            'visa_history_score',
            'acceptance_rate_score',
            'match_reasons',
            'gap_reasons',

            # University
            'university_name',
            'university_city',
            'university_state',
            'university_type',
            'university_website',
            'qs_world_ranking',

            # Program
            'program_name',
            'degree_type',
            'department',
            'is_stem',
            'duration_months',
            'semester',
            'application_deadline',
            'application_link',

            # Raw financial (quick reference)
            'tuition_fee_per_year',
            'estimated_living_cost',
            'acceptance_rate',
            'total_scholarships',
            'total_scholarship_amount',

            # Full cost estimate (from cost_estimator)
            'cost_data',
        ]


class VisaAssessmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for assessment history list."""
    target_country_display = serializers.CharField(
        source='get_target_country_display', read_only=True
    )

    class Meta:
        model = VisaAssessment
        fields = [
            'id',
            'target_country',
            'target_country_display',
            'target_degree_type',
            'target_field',
            'overall_score',
            'status',
            'total_programs_evaluated',
            'total_matches_found',
            'created_at',
        ]


class VisaAssessmentDetailSerializer(serializers.ModelSerializer):
    """Full assessment detail including all matches with cost data."""
    matches = UniversityMatchSerializer(many=True, read_only=True)
    target_country_display = serializers.CharField(
        source='get_target_country_display', read_only=True
    )

    class Meta:
        model = VisaAssessment
        fields = [
            'id',
            'target_country',
            'target_country_display',
            'target_degree_type',
            'target_field',
            'overall_score',
            'status',
            'total_programs_evaluated',
            'total_matches_found',
            'score_breakdown',
            'profile_snapshot',
            'missing_factors',
            'created_at',
            'matches',
        ]


class RunAssessmentSerializer(serializers.Serializer):
    """Input validator for POST /api/assessments/run/"""
    target_country = serializers.ChoiceField(
        choices=['USA', 'UK', 'DE', 'CA', 'AU']
    )
    target_degree_type = serializers.ChoiceField(
        choices=['Bachelors', 'Masters', 'Phd', 'Diploma']
    )
    target_field = serializers.CharField(
        required=False, allow_blank=True, default='',
        help_text="Optional field of study e.g. 'Computer Science'"
    )
    max_results = serializers.IntegerField(
        required=False, default=20, min_value=1, max_value=50
    )
