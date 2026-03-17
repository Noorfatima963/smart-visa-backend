from django.db import models
from django.conf import settings
from universities.models import UniversityProgram


class VisaAssessment(models.Model):
    """
    One complete assessment run for a student.
    Stores probability scores, cost estimates, and profile snapshot.
    """

    COUNTRY_CHOICES = [
        ('USA', 'United States'),
        ('UK',  'United Kingdom'),
        ('DE',  'Germany'),
        ('CA',  'Canada'),
        ('AU',  'Australia'),
    ]
    DEGREE_TYPE_CHOICES = [
        ('Bachelors', 'Bachelors'),
        ('Masters',   'Masters'),
        ('Phd',       'PhD'),
        ('Diploma',   'Diploma'),
    ]
    STATUS_CHOICES = [
        ('completed',         'Completed'),
        ('incomplete_profile','Incomplete Profile'),
        ('no_matches',        'No Matches Found'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments'
    )

    # Target criteria
    target_country     = models.CharField(max_length=5,  choices=COUNTRY_CHOICES)
    target_degree_type = models.CharField(max_length=20, choices=DEGREE_TYPE_CHOICES)
    target_field       = models.CharField(max_length=255, blank=True,
                             help_text="Optional field of study e.g. Computer Science")

    # Result summary
    status                   = models.CharField(max_length=30, choices=STATUS_CHOICES, default='completed')
    overall_score            = models.FloatField(default=0, help_text="Probability score 0-100")
    total_programs_evaluated = models.PositiveIntegerField(default=0)
    total_matches_found      = models.PositiveIntegerField(default=0,
                                   help_text="Programs where student scored >= 50%")

    # JSON blobs
    score_breakdown  = models.JSONField(default=dict,
                           help_text="Per-factor average scores across all evaluated programs")
    profile_snapshot = models.JSONField(default=dict,
                           help_text="Student profile data at time of assessment")
    missing_factors  = models.JSONField(default=list,
                           help_text="Profile gaps that affected scoring")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.target_degree_type} in {self.target_country} ({self.overall_score:.1f}%)"


class UniversityMatch(models.Model):
    """
    One ranked program match within a VisaAssessment.
    Stores both the probability score breakdown AND the full cost estimate.
    """

    ELIGIBILITY_CHOICES = [
        ('likely',   'Likely'),    # >= 75
        ('possible', 'Possible'),  # >= 50
        ('reach',    'Reach'),     # >= 30
        ('unlikely', 'Unlikely'),  # < 30
    ]

    assessment = models.ForeignKey(
        VisaAssessment,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    program = models.ForeignKey(
        UniversityProgram,
        on_delete=models.CASCADE,
        related_name='assessment_matches'
    )

    # Probability score
    probability_score     = models.FloatField()
    gpa_score             = models.FloatField(default=0)
    language_score        = models.FloatField(default=0)
    financial_score       = models.FloatField(default=0)
    backlog_score         = models.FloatField(default=0)
    visa_history_score    = models.FloatField(default=0)
    acceptance_rate_score = models.FloatField(default=0)

    eligibility   = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES)
    match_reasons = models.JSONField(default=list)
    gap_reasons   = models.JSONField(default=list)

    # Full cost estimate stored as JSON
    # Structure: { duration, cost_breakdown, totals, scholarships, affordability }
    cost_data = models.JSONField(
        default=dict,
        help_text="Complete cost estimate: tuition + living + visa + insurance + affordability"
    )

    rank = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['rank']

    def __str__(self):
        return f"#{self.rank} {self.program.university.name} — {self.probability_score:.1f}%"
