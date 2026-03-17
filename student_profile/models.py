from django.db import models
from django.conf import settings

class StudentProfile(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    MARITAL_STATUS = [('single', 'Single'), ('married', 'Married')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Bio-data
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS, default='single')

    # Target Study Details
    target_country = models.CharField(max_length=100, blank=True, null=True, help_text="Target Country for Study")
    target_degree_type = models.CharField(max_length=100, blank=True, null=True, help_text="Target Degree Type")

    # Nationality & Location
    nationality = models.CharField(max_length=100, help_text="Country of Citizenship")
    residence_country = models.CharField(max_length=100, help_text="Country of Residence")
    city = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)

    # Passport
    passport_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    passport_expiry_date = models.DateField(null=True, blank=True)

    # Professional
    profession_title = models.CharField(max_length=100, blank=True)
    current_employer = models.CharField(max_length=150, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)

    # Flags
    has_travel_history = models.BooleanField(default=False)
    has_additional_residency = models.BooleanField(default=False)
    has_additional_passport = models.BooleanField(default=False)
    has_visa_refusal_history = models.BooleanField(default=False, help_text="Important for risk assessment")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"

    @property
    def readiness_score(self):
        score = 0
        
        # 1. Basic Details (15%)
        if self.first_name and self.date_of_birth and self.nationality:
            score += 15
            
        # 2. Education (20%)
        if self.education_history.exists():
            score += 20
            
        # 3. Test Scores (15%)
        if self.test_scores.exists():
            score += 15
            
        # 4. Financial Info (15%)
        financial = getattr(self, 'financial_profile', None)
        if financial and financial.approx_savings and financial.approx_savings > 0:
            score += 15
        
        # 5. Document Checker Integration (20%)
        # Calculate ratio of uploaded mandatory documents
        from documents.models import DocumentDefinition, UserDocument
        mandatory_docs = DocumentDefinition.objects.filter(is_mandatory=True)
        total_mandatory = mandatory_docs.count()
        
        if total_mandatory > 0:
            uploaded_mandatory = UserDocument.objects.filter(
                user=self.user,
                document_definition__in=mandatory_docs,
                status__in=[UserDocument.StatusChoice.VERIFIED, UserDocument.StatusChoice.PENDING]
            ).count()
            
            doc_ratio = uploaded_mandatory / total_mandatory
            score += int(20 * doc_ratio)
        else:
            # If no mandatory documents are defined in the system yet, grant full 20%
            score += 20
            
        # 6. Passport Details (15%)
        if self.passport_number:
            score += 15
            
        return score

    @property
    def readiness_next_step(self):
        if not (self.first_name and self.date_of_birth and self.nationality):
            return "Complete your Personal Details (Date of Birth, Nationality) to boost your score."
        if not self.education_history.exists():
            return "Add your latest Education History to move forward securely."
        if not self.test_scores.exists():
            return "Add your IELTS, PTE, or English Test Score to increase your admission chances."
            
        financial = getattr(self, 'financial_profile', None)
        if not financial or not financial.approx_savings or financial.approx_savings <= 0:
            return "Add your Financial Details or Bank Statement to reach top readiness."
        
        # Document Checker Integration
        from documents.models import DocumentDefinition, UserDocument
        mandatory_docs = DocumentDefinition.objects.filter(is_mandatory=True)
        
        for doc_def in mandatory_docs:
            has_uploaded = UserDocument.objects.filter(
                user=self.user,
                document_definition=doc_def,
                status__in=[UserDocument.StatusChoice.VERIFIED, UserDocument.StatusChoice.PENDING]
            ).exists()
            
            if not has_uploaded:
                return f"Upload your {doc_def.name} to continue your application."
            
        if not self.passport_number:
            return "Add your Passport Number to complete your full visa profile."
            
        return "You're all set!"

class Education(models.Model):
    LEVEL_CHOICES = [
        ('high_school', 'High School / A-Levels'),
        ('bachelors', 'Bachelors'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
    ]
    
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='education_history')
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    degree_title = models.CharField(max_length=150)
    institute_name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=True)
    score = models.CharField(max_length=20, help_text="CGPA or Percentage")

    def __str__(self):
        return f"{self.degree_title} - {self.institute_name}"

class LanguageTest(models.Model):
    TEST_TYPES = [
        ('ielts', 'IELTS'),
        ('toefl', 'TOEFL'),
        ('pte', 'PTE'),
        ('duolingo', 'Duolingo'),
        ('other', 'Other')
    ]
    
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='test_scores')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    
    overall_score = models.FloatField()
    reading = models.FloatField()
    listening = models.FloatField()
    writing = models.FloatField()
    speaking = models.FloatField()
    
    test_date = models.DateField()
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.get_test_type_display()}: {self.overall_score}"

class StudentTravelHistory(models.Model):
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='travel_history')
    country = models.CharField(max_length=100)
    visa_type = models.CharField(max_length=100)
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    refusal_or_overstay = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.country} ({self.visa_type})"

class StudentFinancialProfile(models.Model):
    profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='financial_profile')
    current_monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    income_currency = models.CharField(max_length=10, default='USD')
    income_source = models.CharField(max_length=100, blank=True, help_text="Job, Business, Freelance, etc.")
    
    approx_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    savings_currency = models.CharField(max_length=10, default='USD')
    
    has_sponsor = models.BooleanField(default=False)
    sponsor_name = models.CharField(max_length=150, blank=True, null=True)
    sponsor_relationship = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Financial Profile - {self.profile}"
