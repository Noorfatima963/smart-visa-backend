"""
Smart Visa — University Comparison Engine
==========================================
Compares two university programs side-by-side against a student's real profile.
Returns per-metric winners, probability scores, cost breakdown, and an AI verdict.
"""

from .scoring import (
    build_student_profile,
    build_program_requirements,
    calculate_probability,
)
from .cost_estimator import calculate_cost, cost_to_dict

# Post-study work visa durations per country (display label)
POST_STUDY_WORK = {
    'USA': '1–3 Yrs (OPT/STEM)',
    'UK':  '2 Yrs (Graduate Route)',
    'CA':  'Up to 3 Yrs (PGWP)',
    'AU':  '2–4 Yrs (Subclass 485)',
    'DE':  '18 Months',
    'IE':  '1–2 Yrs (SPSV)',
    'NL':  '1 Yr (Zoekjaar)',
    'SE':  'Limited',
    'FR':  '1–2 Yrs',
    'IT':  '1 Yr',
}

COUNTRY_CODE_MAP = {
    'USA': 'USA', 'UK': 'UK', 'Canada': 'CA', 'Australia': 'AU',
    'Germany': 'DE', 'Ireland': 'IE', 'Netherland': 'NL',
    'Sweden': 'SE', 'France': 'FR', 'Italy': 'IT',
}

COUNTRY_FLAGS = {
    'USA': '🇺🇸', 'UK': '🇬🇧', 'Canada': '🇨🇦', 'Australia': '🇦🇺',
    'Germany': '🇩🇪', 'Ireland': '🇮🇪', 'Netherland': '🇳🇱',
    'Sweden': '🇸🇪', 'France': '🇫🇷', 'Italy': '🇮🇹',
    'New Zealand': '🇳🇿', 'Singapore': '🇸🇬', 'Spain': '🇪🇸',
}


def _country_code(country_str: str) -> str:
    """Map full country name to scoring engine code (USA/UK/DE/CA/AU)."""
    return COUNTRY_CODE_MAP.get(country_str, 'USA')


def _scholarship_label(program) -> str:
    n = program.total_scholarships or 0
    amt = float(program.total_scholarship_amount or 0)
    if n == 0 or amt == 0:
        return 'None listed'
    if amt >= 10000:
        return f'{n} available (up to ${amt:,.0f})'
    return f'{n} available'


def _gre_label(program) -> str:
    v = (program.gre_required or '').strip()
    if not v or v.lower() in ('not applicable', 'n/a', ''):
        return 'Not required'
    if v.lower() == 'waived':
        return 'Waived'
    return f'Required ({v})'


def _build_program_card(program, score_result, cost_result) -> dict:
    """Build the full card for one side of the comparison."""
    uni = program.university
    country = uni.country
    country_code = _country_code(country)

    return {
        # University identity
        'program_id':      program.id,
        'university_name': uni.name,
        'university_type': uni.university_type,
        'country':         country,
        'country_code':    country_code,
        'flag':            COUNTRY_FLAGS.get(country, '🏳️'),
        'city':            uni.city,
        'state':           uni.state_province,
        'website':         uni.website,

        # Rankings
        'qs_world_ranking': uni.qs_world_ranking,
        'us_news_ranking':  uni.us_news_ranking,

        # Program info
        'program_name':   program.program_name,
        'degree_type':    program.degree_type,
        'department':     program.department,
        'is_stem':        program.is_stem,
        'duration_months': program.duration_months,
        'semester':       program.semester,
        'application_deadline': str(program.application_deadline) if program.application_deadline else None,
        'application_link':    program.application_link,

        # Requirements
        'min_gpa':        program.min_gpa,
        'max_backlogs':   program.max_backlogs,
        'ielts_required': program.ielts_required,
        'toefl_required': program.toefl_required,
        'pte_required':   program.pte_required,
        'gre_label':      _gre_label(program),

        # Financials
        'tuition_per_year':   float(program.tuition_fee_per_year or 0),
        'living_cost_per_year': cost_result.annual_living,
        'first_year_total':   cost_result.first_year_cost,
        'total_program_cost': cost_result.total_program_cost,
        'scholarship_label':  _scholarship_label(program),
        'max_scholarship_amt': float(program.total_scholarship_amount or 0),
        'adjusted_total_cost': cost_result.adjusted_total_cost,

        # Visa
        'visa_fee':        cost_result.total_visa_fee,
        'post_study_work': POST_STUDY_WORK.get(country_code, 'Varies'),

        # Admission stats
        'acceptance_rate': program.acceptance_rate,

        # Probability score (against student profile)
        'probability_score':     score_result.probability_score,
        'eligibility':           score_result.eligibility,
        'gpa_score':             score_result.gpa_score,
        'language_score':        score_result.language_score,
        'financial_score':       score_result.financial_score,
        'backlog_score':         score_result.backlog_score,
        'visa_history_score':    score_result.visa_history_score,
        'acceptance_rate_score': score_result.acceptance_rate_score,
        'match_reasons':         score_result.match_reasons,
        'gap_reasons':           score_result.gap_reasons,

        # Full cost breakdown
        'cost_data': cost_to_dict(cost_result),
    }


def _winner(val_a, val_b, higher_is_better=True):
    """Return 'a', 'b', or 'tie' for a single metric."""
    if val_a is None and val_b is None:
        return 'tie'
    if val_a is None:
        return 'b'
    if val_b is None:
        return 'a'
    if val_a == val_b:
        return 'tie'
    if higher_is_better:
        return 'a' if val_a > val_b else 'b'
    return 'a' if val_a < val_b else 'b'


def _build_comparison(card_a: dict, card_b: dict) -> dict:
    """Return per-metric winner flags (a / b / tie)."""
    return {
        'probability_score':  _winner(card_a['probability_score'],  card_b['probability_score']),
        'qs_ranking':         _winner(card_a['qs_world_ranking'],    card_b['qs_world_ranking'],    higher_is_better=False),
        'tuition_per_year':   _winner(card_a['tuition_per_year'],    card_b['tuition_per_year'],    higher_is_better=False),
        'living_cost':        _winner(card_a['living_cost_per_year'],card_b['living_cost_per_year'],higher_is_better=False),
        'first_year_total':   _winner(card_a['first_year_total'],    card_b['first_year_total'],    higher_is_better=False),
        'acceptance_rate':    _winner(card_a['acceptance_rate'],     card_b['acceptance_rate']),
        'ielts_required':     _winner(card_a['ielts_required'],      card_b['ielts_required'],      higher_is_better=False),
        'scholarship':        _winner(card_a['max_scholarship_amt'], card_b['max_scholarship_amt']),
        'duration':           _winner(card_a['duration_months'],     card_b['duration_months'],     higher_is_better=False),
    }


def _build_verdict(card_a: dict, card_b: dict, comparison: dict) -> dict:
    """
    Rule-based verdict: who is the better fit for this specific student?

    Scoring: probability score carries the most weight, then affordability, then ranking.
    """
    score_a = card_a['probability_score']
    score_b = card_b['probability_score']
    cost_a  = card_a['first_year_total']
    cost_b  = card_b['first_year_total']
    rank_a  = card_a['qs_world_ranking']
    rank_b  = card_b['qs_world_ranking']

    # Tally points (weighted)
    points_a = 0
    points_b = 0

    # 1. Probability score — 3 points
    if score_a > score_b + 5:
        points_a += 3
    elif score_b > score_a + 5:
        points_b += 3
    else:
        points_a += 1
        points_b += 1   # near-tie

    # 2. First-year cost — 2 points
    if cost_a < cost_b * 0.9:
        points_a += 2
    elif cost_b < cost_a * 0.9:
        points_b += 2

    # 3. Acceptance rate — 1 point
    acc_a = card_a['acceptance_rate'] or 50
    acc_b = card_b['acceptance_rate'] or 50
    if acc_a > acc_b:
        points_a += 1
    elif acc_b > acc_a:
        points_b += 1

    # 4. QS ranking — 1 point
    if rank_a and rank_b:
        if rank_a < rank_b:
            points_a += 1
        else:
            points_b += 1
    elif rank_a:
        points_a += 1
    elif rank_b:
        points_b += 1

    # Determine winner
    if points_a > points_b:
        winner = 'a'
    elif points_b > points_a:
        winner = 'b'
    else:
        winner = 'tie'

    # Build human-readable reason
    reasons = []
    name_a = card_a['university_name'].title()
    name_b = card_b['university_name'].title()

    if abs(score_a - score_b) > 3:
        higher = name_a if score_a > score_b else name_b
        lower  = name_b if score_a > score_b else name_a
        reasons.append(
            f'{higher} gives you a higher admission probability '
            f'({max(score_a, score_b):.1f}% vs {min(score_a, score_b):.1f}%)'
        )

    if abs(cost_a - cost_b) > 2000:
        cheaper = name_a if cost_a < cost_b else name_b
        diff = abs(cost_a - cost_b)
        reasons.append(f'{cheaper} saves ~${diff:,.0f} in first-year costs')

    if card_a['acceptance_rate'] and card_b['acceptance_rate']:
        diff_acc = abs(acc_a - acc_b)
        if diff_acc >= 5:
            easier = name_a if acc_a > acc_b else name_b
            reasons.append(
                f'{easier} has a higher acceptance rate '
                f'({max(acc_a, acc_b):.0f}% vs {min(acc_a, acc_b):.0f}%)'
            )

    if not reasons:
        if winner == 'a':
            reasons.append(f'{name_a} edges ahead on overall fit for your profile')
        elif winner == 'b':
            reasons.append(f'{name_b} edges ahead on overall fit for your profile')
        else:
            reasons.append('Both universities are a comparable fit for your profile')

    winner_name = name_a if winner == 'a' else (name_b if winner == 'b' else 'Tie')

    return {
        'winner':       winner,          # 'a' | 'b' | 'tie'
        'winner_name':  winner_name,
        'score_a':      score_a,
        'score_b':      score_b,
        'points_a':     points_a,
        'points_b':     points_b,
        'reasons':      reasons,
        'summary':      ' — '.join(reasons) if reasons else 'Both are strong options.',
    }


def compare_programs(program_a, program_b, django_profile) -> dict:
    """
    Main entry point. Runs scoring + cost for both programs and returns
    the full comparison payload ready to serialize.
    """
    student = build_student_profile(django_profile)

    financial = getattr(django_profile, 'financial_profile', None)
    savings    = float(financial.approx_savings or 0) if financial else 0.0
    sponsor    = financial.has_sponsor if financial else False

    # Score both
    req_a   = build_program_requirements(program_a)
    req_b   = build_program_requirements(program_b)
    score_a = calculate_probability(student, req_a)
    score_b = calculate_probability(student, req_b)

    # Country code for cost estimator (needs 2-letter code for USA/UK/DE/CA/AU fallback)
    cc_a = _country_code(program_a.university.country)
    cc_b = _country_code(program_b.university.country)
    # Cost estimator only supports 5 countries; fall back to nearest if unsupported
    supported = {'USA', 'UK', 'DE', 'CA', 'AU'}
    cc_a = cc_a if cc_a in supported else 'USA'
    cc_b = cc_b if cc_b in supported else 'USA'

    cost_a = calculate_cost(program_a, cc_a, savings, sponsor)
    cost_b = calculate_cost(program_b, cc_b, savings, sponsor)

    card_a     = _build_program_card(program_a, score_a, cost_a)
    card_b     = _build_program_card(program_b, score_b, cost_b)
    comparison = _build_comparison(card_a, card_b)
    verdict    = _build_verdict(card_a, card_b, comparison)

    return {
        'university_a': card_a,
        'university_b': card_b,
        'comparison':   comparison,
        'verdict':      verdict,
    }