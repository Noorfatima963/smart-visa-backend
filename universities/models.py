from django.db import models


class University(models.Model):
    """
    Stores university-level information.
    One university can have many programs (UniversityProgram).
    """

    UNIVERSITY_TYPE_CHOICES = [
        ('Public', 'Public'),
        ('Private', 'Private'),
        ('Other', 'Other'),
    ]

    # Identifiers from scraped data
    external_id = models.CharField(max_length=20, unique=True, help_text="universitiesid from scraped data")
    uni_no = models.CharField(max_length=20, blank=True)

    # Core info
    name = models.CharField(max_length=255, db_index=True)
    university_type = models.CharField(max_length=20, choices=UNIVERSITY_TYPE_CHOICES, default='Public')

    # Location
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=10, default='USA', db_index=True)

    # Rankings
    qs_world_ranking = models.PositiveIntegerField(null=True, blank=True)
    us_news_ranking = models.PositiveIntegerField(null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)

    # Financial aid availability
    offers_financial_aid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Universities"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state_province})"


class UniversityProgram(models.Model):
    """
    Stores program-level information for a university.
    This is the core model used by the probability scoring engine.
    Each row = one program at one university.
    """

    DEGREE_TYPE_CHOICES = [
        ('Bachelors', 'Bachelors'),
        ('Masters', 'Masters'),
        ('Phd', 'PhD'),
        ('Diploma', 'Diploma'),
    ]

    SEMESTER_CHOICES = [
        ('Fall', 'Fall'),
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
        ('Rolling', 'Rolling'),
    ]

    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='programs')

    # Program identity
    program_name = models.CharField(max_length=255, db_index=True)
    department = models.CharField(max_length=255, blank=True)
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPE_CHOICES, db_index=True)
    degree_name = models.CharField(max_length=50, blank=True, help_text="e.g. BS, MS, MBA")
    is_stem = models.BooleanField(default=False)

    # ── Language Requirements ──────────────────────────────────────────────────
    ielts_required = models.FloatField(null=True, blank=True, help_text="Minimum IELTS overall band")
    toefl_required = models.FloatField(null=True, blank=True, help_text="Minimum TOEFL iBT score")
    pte_required = models.FloatField(null=True, blank=True, help_text="Minimum PTE score")
    duolingo_required = models.FloatField(null=True, blank=True, help_text="Minimum Duolingo score")

    # ── Academic Requirements ──────────────────────────────────────────────────
    min_gpa = models.FloatField(null=True, blank=True, help_text="Minimum GPA/percentage required")
    max_backlogs = models.PositiveIntegerField(null=True, blank=True, help_text="Max allowed academic backlogs")
    gre_required = models.CharField(max_length=50, blank=True, help_text="e.g. Waived, Required, Not Applicable")
    gmat_required = models.CharField(max_length=50, blank=True)

    # ── Financial ─────────────────────────────────────────────────────────────
    tuition_fee_per_year = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="International student annual tuition in USD"
    )
    estimated_living_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Estimated annual living cost in USD"
    )
    application_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    app_fee_waiver_available = models.BooleanField(default=False)

    # ── Admission Stats ────────────────────────────────────────────────────────
    acceptance_rate = models.FloatField(null=True, blank=True, help_text="Acceptance rate as percentage (0-100)")

    # ── Program Details ────────────────────────────────────────────────────────
    duration_months = models.PositiveIntegerField(null=True, blank=True)
    num_credits = models.PositiveIntegerField(null=True, blank=True)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, blank=True)

    # ── Deadlines ─────────────────────────────────────────────────────────────
    application_deadline = models.DateField(null=True, blank=True)

    # ── Required Documents ─────────────────────────────────────────────────────
    required_documents_raw = models.TextField(
        blank=True,
        help_text="Raw pipe-separated list from scraped data e.g. 'Passport |##| IELTS'"
    )

    # ── Application Links ──────────────────────────────────────────────────────
    application_link = models.URLField(blank=True)
    department_link = models.URLField(blank=True)

    # ── Scholarships ──────────────────────────────────────────────────────────
    total_scholarships = models.PositiveIntegerField(default=0)
    total_scholarship_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['university__name', 'program_name']

    def __str__(self):
        return f"{self.degree_type} in {self.program_name} — {self.university.name}"

    @property
    def total_first_year_cost(self):
        """Total estimated cost for first year: tuition + living."""
        tuition = float(self.tuition_fee_per_year or 0)
        living = float(self.estimated_living_cost or 0)
        return tuition + living

    @property
    def required_documents_list(self):
        """Returns required documents as a clean Python list."""
        if not self.required_documents_raw:
            return []
        return [doc.strip() for doc in self.required_documents_raw.split('|##|') if doc.strip()]