"""
chatbot/context_builder.py
──────────────────────────
Builds the system prompt for the Groq API call by reading
the student's full profile and latest assessment from the DB.

If no assessment exists, auto-runs one silently.
"""

from assessments.scoring import build_student_profile, build_program_requirements, calculate_probability
from assessments.cost_estimator import calculate_cost
from universities.models import UniversityProgram
from student_profile.models import StudentProfile


# Fields required for a useful chatbot response
CRITICAL_FIELDS = {
    'gpa':     'your GPA or academic score',
    'ielts':   'your IELTS / TOEFL score',
    'savings': 'your approximate savings in USD',
    'country': 'your target country (e.g. USA, UK, Canada)',
    'degree':  'your target degree level (e.g. Masters, Bachelors)',
}


def get_missing_fields(profile) -> list:
    """
    Returns a list of missing critical fields.
    Each item: { key, label, question }
    """
    missing = []

    education = profile.education_history.first()
    language  = profile.test_scores.first()
    financial = getattr(profile, 'financial_profile', None)

    if not education or not education.score:
        missing.append({
            'key':      'gpa',
            'label':    'GPA / Academic Score',
            'question': 'What is your GPA or academic percentage?',
        })

    if not language:
        missing.append({
            'key':      'ielts',
            'label':    'Language Test Score',
            'question': 'Do you have an IELTS, TOEFL, or PTE score? If yes, what is your overall score?',
        })

    if not financial or not financial.approx_savings:
        missing.append({
            'key':      'savings',
            'label':    'Savings (USD)',
            'question': 'What are your approximate savings in USD for studying abroad?',
        })

    if not profile.target_country:
        missing.append({
            'key':      'country',
            'label':    'Target Country',
            'question': 'Which country are you targeting for your studies? (e.g. USA, UK, Canada, Australia, Germany)',
        })

    if not profile.target_degree_type:
        missing.append({
            'key':      'degree',
            'label':    'Target Degree',
            'question': 'What degree level are you applying for? (Masters, Bachelors, PhD)',
        })

    return missing


def _run_quick_assessment(profile):
    """
    Silently runs a quick assessment (top 5 matches) for the chatbot context.
    Returns a summary dict or None if it fails.
    """
    try:
        from assessments.scoring import build_student_profile as bsp, build_program_requirements as bpr, calculate_probability as cp

        country     = profile.target_country or 'USA'
        degree_type = profile.target_degree_type or 'Masters'

        programs = UniversityProgram.objects.select_related('university').filter(
            university__country=country,
            degree_type=degree_type,
        )[:50]

        if not programs:
            return None

        student_data = bsp(profile)
        results = []

        for program in programs:
            try:
                req   = bpr(program)
                score = cp(student_data, req)
                results.append({
                    'university': program.university.name,
                    'program':    program.program_name,
                    'score':      score.probability_score,
                    'eligibility': score.eligibility,
                    'tuition':    float(program.tuition_fee_per_year or 0),
                })
            except Exception:
                continue

        if not results:
            return None

        results.sort(key=lambda x: x['score'], reverse=True)
        top = results[:3]

        return {
            'source':           'auto',
            'programs_checked': len(results),
            'top_matches':      top,
            'overall_score':    round(sum(r['score'] for r in top) / len(top), 1) if top else 0,
        }
    except Exception:
        return None


def build_system_prompt(profile) -> str:
    """
    Builds the full system prompt injected into every Groq request.
    Reads profile + last assessment (or auto-runs one).
    """
    education = profile.education_history.order_by('-start_date').first()
    language  = profile.test_scores.order_by('-test_date').first()
    financial = getattr(profile, 'financial_profile', None)

    # ── Student identity ──────────────────────────────────────────────────────
    name        = f"{profile.first_name or ''} {profile.last_name or ''}".strip() or 'the student'
    nationality = profile.nationality or 'Pakistani'
    target_c    = profile.target_country or 'Not specified'
    target_d    = profile.target_degree_type or 'Not specified'

    # ── Academic ──────────────────────────────────────────────────────────────
    if education:
        gpa_line     = f"GPA/Score: {education.score} ({education.level} — {education.degree_title} from {education.institute_name})"
        backlogs     = getattr(education, 'backlogs', None) or 0
        backlog_line = f"Backlogs: {backlogs}"
    else:
        gpa_line     = "GPA/Score: Not provided"
        backlog_line = "Backlogs: 0"

    # ── Language ──────────────────────────────────────────────────────────────
    if language:
        lang_line = (
            f"{language.test_type.upper()}: {language.overall_score} overall "
            f"(R:{language.reading} L:{language.listening} W:{language.writing} S:{language.speaking})"
        )
    else:
        lang_line = "Language test: Not provided"

    # ── Financial ─────────────────────────────────────────────────────────────
    if financial and financial.approx_savings:
        savings_val  = float(financial.approx_savings)
        sponsor_line = f"Sponsor: {financial.sponsor_name}" if financial.has_sponsor else "Sponsor: None (self-funded)"
        finance_line = f"Savings: ${savings_val:,.0f} USD. {sponsor_line}"
    else:
        finance_line = "Savings: Not provided"

    # ── Assessment ────────────────────────────────────────────────────────────
    assessment_section = ""
    try:
        from assessments.models import VisaAssessment
        last = VisaAssessment.objects.filter(student=profile).order_by('-created_at').first()

        if last:
            matches = last.matches.order_by('-probability_score')[:3]
            match_lines = "\n".join([
                f"  {i+1}. {m.university.name} — {m.program_name} "
                f"({m.probability_score:.0f}% match, ${float(m.first_year_cost or 0):,.0f}/first year)"
                for i, m in enumerate(matches)
            ])
            assessment_section = f"""
LAST ASSESSMENT (ran {last.created_at.strftime('%b %d, %Y')}):
- Overall admission probability: {last.overall_score:.1f}%
- Programs evaluated: {last.total_programs_evaluated}
- Matches found: {last.total_matches_found}
- Top 3 matches:
{match_lines}
"""
        else:
            quick = _run_quick_assessment(profile)
            if quick:
                match_lines = "\n".join([
                    f"  {i+1}. {m['university']} — {m['program']} "
                    f"({m['score']:.0f}% match, ${m['tuition']:,.0f} tuition/yr)"
                    for i, m in enumerate(quick['top_matches'])
                ])
                assessment_section = f"""
QUICK ASSESSMENT (auto-generated for this session):
- Programs checked: {quick['programs_checked']}
- Average match score: {quick['overall_score']}%
- Top matches:
{match_lines}
"""
            else:
                assessment_section = "\nASSESSMENT DATA: Not available yet. Advise the student to run an assessment from the dashboard.\n"
    except Exception:
        assessment_section = "\nASSESSMENT DATA: Could not load.\n"

    # ── Build final prompt ────────────────────────────────────────────────────
    return f"""You are SmartVisa AI, a friendly and knowledgeable visa and university admissions advisor specializing in helping Pakistani students study abroad.

STUDENT PROFILE:
- Name: {name}
- Nationality: {nationality}
- Target: {target_d} → {target_c}
- {gpa_line}
- {backlog_line}
- Language: {lang_line}
- Financial: {finance_line}
{assessment_section}
INSTRUCTIONS:
- Always personalize answers using the student's actual data above.
- Be concise, practical, and encouraging.
- If you recommend a university, reference their actual profile gaps or strengths.
- If asked about costs, use their savings data to assess affordability.
- If critical data is missing (marked "Not provided"), ask the student to share it before giving a detailed answer.
- Never make up visa rules — if unsure, say so and suggest they verify with the official embassy website.
- Keep responses under 200 words unless the question requires more detail.
- Use bullet points for lists of requirements or steps.
"""


def build_context(user) -> dict:
    """
    Main entry point called by the view.
    Returns { system_prompt, missing_fields, has_profile }
    """
    try:
        profile = user.profile
    except Exception:
        return {
            'system_prompt':  None,
            'missing_fields': list(CRITICAL_FIELDS.values()),
            'has_profile':    False,
        }

    missing = get_missing_fields(profile)
    prompt  = build_system_prompt(profile)

    return {
        'system_prompt':  prompt,
        'missing_fields': missing,
        'has_profile':    True,
    }
