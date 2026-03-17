"""
Smart Visa — Probability Scoring Engine
========================================
This module computes a student's admission probability score for each
university program based on their profile data.

Scoring Weights (must sum to 100):
    GPA Match           → 25%
    Language Score      → 25%
    Financial           → 20%
    Backlogs            → 15%
    Visa Refusal History→ 10%
    Acceptance Rate     →  5%
    ─────────────────────────
    Total               → 100%

Each factor returns a score between 0 and 100.
The weighted average gives the final probability percentage.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Weights ────────────────────────────────────────────────────────────────────

WEIGHTS = {
    'gpa':             0.25,
    'language':        0.25,
    'financial':       0.20,
    'backlogs':        0.15,
    'visa_history':    0.10,
    'acceptance_rate': 0.05,
}


# ── Student Input Dataclass ────────────────────────────────────────────────────

@dataclass
class StudentProfile:
    """
    Flattened representation of all student data needed for scoring.
    Built from Django models before calling the engine.
    """
    # GPA / Academic
    gpa: Optional[float] = None             # percentage e.g. 75.0
    backlogs: int = 0                       # number of academic backlogs

    # Language scores
    ielts: Optional[float] = None
    toefl: Optional[float] = None
    pte: Optional[float] = None
    duolingo: Optional[float] = None

    # Financial (in USD)
    savings_usd: float = 0.0
    has_sponsor: bool = False

    # Visa history
    has_visa_refusal: bool = False

    # Profile completeness flags (used for missing_factors)
    has_education: bool = False
    has_language_test: bool = False
    has_financial_info: bool = False


@dataclass
class ProgramRequirements:
    """
    Flattened representation of a university program's requirements.
    Built from UniversityProgram model.
    """
    program_id: int = 0
    university_name: str = ''
    program_name: str = ''
    degree_type: str = ''

    # Requirements
    min_gpa: Optional[float] = None
    max_backlogs: Optional[int] = None
    ielts_required: Optional[float] = None
    toefl_required: Optional[float] = None
    pte_required: Optional[float] = None
    duolingo_required: Optional[float] = None

    # Financial
    tuition_per_year: float = 0.0
    living_cost: float = 0.0

    # Stats
    acceptance_rate: Optional[float] = None


@dataclass
class ScoreResult:
    """
    Full scoring result for one student × one program combination.
    """
    program_id: int = 0
    university_name: str = ''
    program_name: str = ''
    degree_type: str = ''

    # Final score
    probability_score: float = 0.0
    eligibility: str = 'unlikely'

    # Per-factor scores (each 0–100)
    gpa_score: float = 0.0
    language_score: float = 0.0
    financial_score: float = 0.0
    backlog_score: float = 0.0
    visa_history_score: float = 0.0
    acceptance_rate_score: float = 0.0

    # Human-readable reasons
    match_reasons: list = field(default_factory=list)
    gap_reasons: list = field(default_factory=list)


# ── Individual Factor Scorers ──────────────────────────────────────────────────

def score_gpa(student_gpa: Optional[float], required_gpa: Optional[float]) -> tuple[float, list, list]:
    """
    Score GPA factor.

    Returns (score_0_to_100, match_reasons, gap_reasons)

    Logic:
    - If no requirement → full score (program accepts all GPAs)
    - If student has no GPA → 0 score
    - If student GPA >= required → score based on how far above they are
    - If student GPA < required → proportional penalty
    """
    matches = []
    gaps = []

    if required_gpa is None or required_gpa == 0:
        return 100.0, ['No minimum GPA requirement'], []

    if student_gpa is None:
        return 0.0, [], ['No GPA/academic score found in your profile']

    if student_gpa >= required_gpa:
        # Score above requirement — bonus up to 100
        # e.g. student 85, required 75 → 10 points above → scale to 100
        surplus = student_gpa - required_gpa
        # Cap bonus at 20 points above requirement = full 100
        bonus = min(surplus / 20.0, 1.0) * 20
        score = min(80.0 + bonus, 100.0)
        matches.append(f'GPA {student_gpa:.1f}% meets requirement of {required_gpa:.1f}%')
        return round(score, 1), matches, gaps
    else:
        # Below requirement — proportional score
        ratio = student_gpa / required_gpa
        score = max(ratio * 70, 0)  # scale penalty, floor at 0
        gap = required_gpa - student_gpa
        gaps.append(f'GPA {student_gpa:.1f}% is {gap:.1f}% below requirement of {required_gpa:.1f}%')
        return round(score, 1), matches, gaps


def score_language(
    student: StudentProfile,
    program: ProgramRequirements
) -> tuple[float, list, list]:
    """
    Score language test factor.

    Priority: IELTS → TOEFL → PTE → Duolingo
    Uses whichever test the student has taken, matched against the program requirement.

    Returns (score_0_to_100, match_reasons, gap_reasons)
    """
    matches = []
    gaps = []

    # Check if program has any language requirement
    has_any_req = any([
        program.ielts_required,
        program.toefl_required,
        program.pte_required,
        program.duolingo_required,
    ])

    if not has_any_req:
        return 100.0, ['No language test requirement'], []

    # Try to match student's test against program requirements
    # Each pair: (student_score, required_score, test_name)
    test_pairs = []
    if student.ielts and program.ielts_required:
        test_pairs.append((student.ielts, program.ielts_required, 'IELTS'))
    if student.toefl and program.toefl_required:
        test_pairs.append((student.toefl, program.toefl_required, 'TOEFL'))
    if student.pte and program.pte_required:
        test_pairs.append((student.pte, program.pte_required, 'PTE'))
    if student.duolingo and program.duolingo_required:
        test_pairs.append((student.duolingo, program.duolingo_required, 'Duolingo'))

    if not test_pairs:
        # Student has a test but program requires a different one
        # Partial credit — student at least has some language test
        if any([student.ielts, student.toefl, student.pte, student.duolingo]):
            gaps.append('Your language test may not match what this program requires — verify on their website')
            return 40.0, [], gaps
        gaps.append('No language test score found in your profile')
        return 0.0, [], gaps

    # Use best matching pair
    best_score = 0.0
    for student_score, required_score, test_name in test_pairs:
        if student_score >= required_score:
            surplus = student_score - required_score
            # Normalise surplus as a fraction of the required score (capped at 20%)
            bonus = min(surplus / required_score, 0.20) * 20
            factor_score = min(80.0 + bonus, 100.0)
            matches.append(f'{test_name} {student_score} meets requirement of {required_score}')
        else:
            ratio = student_score / required_score
            factor_score = max(ratio * 70, 0)
            gap = required_score - student_score
            gaps.append(f'{test_name} {student_score} is {gap:.1f} below requirement of {required_score}')

        if factor_score > best_score:
            best_score = factor_score

    return round(best_score, 1), matches, gaps


def score_financial(
    savings_usd: float,
    has_sponsor: bool,
    tuition_per_year: float,
    living_cost: float
) -> tuple[float, list, list]:
    """
    Score financial readiness.

    Logic:
    - Total required = tuition + living cost (first year minimum)
    - If student savings + sponsor >= required → high score
    - Partial credit for partial funding
    - Sponsor gives a 20% bonus

    Returns (score_0_to_100, match_reasons, gap_reasons)
    """
    matches = []
    gaps = []

    total_required = tuition_per_year + living_cost

    if total_required == 0:
        return 100.0, ['No financial requirement data available'], []

    effective_funds = savings_usd
    if has_sponsor:
        # Sponsor doesn't guarantee a specific amount, but it's a strong positive signal
        effective_funds *= 1.20
        matches.append('Sponsor support noted — boosts financial score')

    ratio = effective_funds / total_required

    if ratio >= 1.0:
        score = min(80.0 + (ratio - 1.0) * 20, 100.0)
        matches.append(
            f'Savings ${savings_usd:,.0f} covers estimated first year cost of ${total_required:,.0f}'
        )
    elif ratio >= 0.75:
        score = 60.0 + (ratio - 0.75) * 80
        shortfall = total_required - savings_usd
        gaps.append(f'Savings may be ~${shortfall:,.0f} short of first year costs (${total_required:,.0f})')
    elif ratio >= 0.50:
        score = 35.0 + (ratio - 0.50) * 100
        shortfall = total_required - savings_usd
        gaps.append(f'Savings ${savings_usd:,.0f} covers ~{ratio*100:.0f}% of required ${total_required:,.0f}')
    else:
        score = max(ratio * 70, 0)
        gaps.append(f'Insufficient funds — need ${total_required:,.0f}, have ${savings_usd:,.0f}')

    return round(score, 1), matches, gaps


def score_backlogs(student_backlogs: int, max_allowed: Optional[int]) -> tuple[float, list, list]:
    """
    Score based on academic backlogs.

    Returns (score_0_to_100, match_reasons, gap_reasons)
    """
    matches = []
    gaps = []

    if max_allowed is None:
        # No backlog policy stated — neutral, give benefit of doubt
        if student_backlogs == 0:
            return 100.0, ['No backlogs — strong academic record'], []
        elif student_backlogs <= 3:
            return 80.0, [], [f'{student_backlogs} backlog(s) — verify with university directly']
        else:
            return 50.0, [], [f'{student_backlogs} backlog(s) — may need explanation in SOP']

    if student_backlogs == 0:
        return 100.0, ['No backlogs — exceeds requirement'], []

    if student_backlogs <= max_allowed:
        # Within limit but has some backlogs
        ratio = 1 - (student_backlogs / (max_allowed + 1))
        score = 60.0 + ratio * 40
        matches.append(f'{student_backlogs} backlog(s) within allowed limit of {max_allowed}')
        return round(score, 1), matches, gaps
    else:
        # Exceeds limit
        score = max(0, 30 - (student_backlogs - max_allowed) * 10)
        gaps.append(
            f'{student_backlogs} backlog(s) exceeds maximum allowed ({max_allowed}) — high risk of rejection'
        )
        return round(score, 1), matches, gaps


def score_visa_history(has_refusal: bool) -> tuple[float, list, list]:
    """
    Score based on visa refusal history.
    A prior refusal is a significant negative signal.

    Returns (score_0_to_100, match_reasons, gap_reasons)
    """
    if has_refusal:
        return (
            40.0,
            [],
            ['Previous visa refusal detected — include strong explanation letter with application']
        )
    return 100.0, ['No prior visa refusals — positive signal'], []


def score_acceptance_rate(acceptance_rate: Optional[float]) -> tuple[float, list, list]:
    """
    Score based on university acceptance rate.
    Higher acceptance rate = more likely to get in.
    This factor helps rank easier-to-enter programs higher.

    Returns (score_0_to_100, match_reasons, gap_reasons)
    """
    if acceptance_rate is None:
        return 70.0, [], []  # Neutral if unknown

    if acceptance_rate >= 70:
        return 100.0, [f'High acceptance rate ({acceptance_rate:.0f}%) — favorable odds'], []
    elif acceptance_rate >= 40:
        score = 60 + (acceptance_rate - 40) / 30 * 40
        return round(score, 1), [f'Moderate acceptance rate ({acceptance_rate:.0f}%)'], []
    elif acceptance_rate >= 20:
        score = 30 + (acceptance_rate - 20) / 20 * 30
        return round(score, 1), [], [f'Competitive acceptance rate ({acceptance_rate:.0f}%)']
    else:
        return 20.0, [], [f'Very competitive — acceptance rate is {acceptance_rate:.0f}%']


# ── Eligibility Label ──────────────────────────────────────────────────────────

def get_eligibility_label(score: float) -> str:
    if score >= 75:
        return 'likely'
    elif score >= 50:
        return 'possible'
    elif score >= 30:
        return 'reach'
    return 'unlikely'


# ── Main Scoring Function ──────────────────────────────────────────────────────

def calculate_probability(
    student: StudentProfile,
    program: ProgramRequirements
) -> ScoreResult:
    """
    Calculate the probability score for one student × one program.

    Returns a ScoreResult with full breakdown.
    """
    result = ScoreResult(
        program_id=program.program_id,
        university_name=program.university_name,
        program_name=program.program_name,
        degree_type=program.degree_type,
    )

    # ── Score each factor ──────────────────────────────────────────────────────
    gpa_s, gpa_m, gpa_g = score_gpa(student.gpa, program.min_gpa)
    lang_s, lang_m, lang_g = score_language(student, program)
    fin_s, fin_m, fin_g = score_financial(
        student.savings_usd,
        student.has_sponsor,
        program.tuition_per_year,
        program.living_cost
    )
    back_s, back_m, back_g = score_backlogs(student.backlogs, program.max_backlogs)
    visa_s, visa_m, visa_g = score_visa_history(student.has_visa_refusal)
    acc_s, acc_m, acc_g = score_acceptance_rate(program.acceptance_rate)

    # ── Weighted final score ───────────────────────────────────────────────────
    final = (
        gpa_s  * WEIGHTS['gpa'] +
        lang_s * WEIGHTS['language'] +
        fin_s  * WEIGHTS['financial'] +
        back_s * WEIGHTS['backlogs'] +
        visa_s * WEIGHTS['visa_history'] +
        acc_s  * WEIGHTS['acceptance_rate']
    )

    # ── Populate result ────────────────────────────────────────────────────────
    result.gpa_score = gpa_s
    result.language_score = lang_s
    result.financial_score = fin_s
    result.backlog_score = back_s
    result.visa_history_score = visa_s
    result.acceptance_rate_score = acc_s

    result.probability_score = round(final, 1)
    result.eligibility = get_eligibility_label(final)

    result.match_reasons = gpa_m + lang_m + fin_m + back_m + visa_m + acc_m
    result.gap_reasons = gpa_g + lang_g + fin_g + back_g + visa_g + acc_g

    return result


# ── Profile Builder (Django model → dataclass) ─────────────────────────────────

def build_student_profile(django_profile) -> StudentProfile:
    """
    Convert a Django StudentProfile model instance into a StudentProfile dataclass
    for use in the scoring engine.
    """
    # Get best GPA from education history
    gpa = None
    backlogs = 0
    if django_profile.education_history.exists():
        for edu in django_profile.education_history.all():
            try:
                score_val = float(str(edu.score).replace('%', '').strip())
                if gpa is None or score_val > gpa:
                    gpa = score_val
                backlogs += getattr(edu, 'backlogs', 0)
            except (ValueError, TypeError):
                pass

    # Get language scores
    ielts = toefl = pte = duolingo = None
    for test in django_profile.test_scores.all():
        t = test.test_type.lower()
        if t == 'ielts':
            ielts = max(ielts or 0, float(test.overall_score))
        elif t == 'toefl':
            toefl = max(toefl or 0, float(test.overall_score))
        elif t == 'pte':
            pte = max(pte or 0, float(test.overall_score))
        elif t == 'duolingo':
            duolingo = max(duolingo or 0, float(test.overall_score))

    # Get financial data
    savings_usd = 0.0
    has_sponsor = False
    financial = getattr(django_profile, 'financial_profile', None)
    if financial:
        savings_usd = float(financial.approx_savings or 0)
        has_sponsor = financial.has_sponsor

    return StudentProfile(
        gpa=gpa,
        backlogs=backlogs,
        ielts=ielts,
        toefl=toefl,
        pte=pte,
        duolingo=duolingo,
        savings_usd=savings_usd,
        has_sponsor=has_sponsor,
        has_visa_refusal=django_profile.has_visa_refusal_history,
        has_education=django_profile.education_history.exists(),
        has_language_test=django_profile.test_scores.exists(),
        has_financial_info=financial is not None,
    )


def build_program_requirements(django_program) -> ProgramRequirements:
    """
    Convert a Django UniversityProgram model instance into a ProgramRequirements dataclass.
    """
    return ProgramRequirements(
        program_id=django_program.id,
        university_name=django_program.university.name,
        program_name=django_program.program_name,
        degree_type=django_program.degree_type,
        min_gpa=django_program.min_gpa,
        max_backlogs=django_program.max_backlogs,
        ielts_required=django_program.ielts_required,
        toefl_required=django_program.toefl_required,
        pte_required=django_program.pte_required,
        duolingo_required=django_program.duolingo_required,
        tuition_per_year=float(django_program.tuition_fee_per_year or 0),
        living_cost=float(django_program.estimated_living_cost or 0),
        acceptance_rate=django_program.acceptance_rate,
    )


def get_missing_factors(student: StudentProfile) -> list:
    """
    Return a list of profile gaps that could be affecting the overall score.
    Used to guide the student on what to complete.
    """
    missing = []
    if not student.has_education:
        missing.append('Add your education history to enable GPA scoring')
    elif student.gpa is None:
        missing.append('Add your CGPA or percentage to your education record')

    if not student.has_language_test:
        missing.append('Add IELTS, TOEFL, or PTE score to enable language scoring')

    if not student.has_financial_info:
        missing.append('Add financial profile (savings/sponsorship) to enable financial scoring')
    elif student.savings_usd == 0 and not student.has_sponsor:
        missing.append('Add your approximate savings or sponsorship details')

    return missing
