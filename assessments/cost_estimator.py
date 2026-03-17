"""
Smart Visa — Cost Estimator
============================
Calculates the complete financial cost of studying abroad for a given
university program and student profile.

Four cost components:
    1. Tuition Fee          — from university program data × duration
    2. Living Expenses      — from university data OR fallback lookup table
    3. Visa Application Fee — fixed per country (government charges)
    4. Health Insurance     — fixed per country per year × duration

Living Cost Priority (3-tier lookup):
    Tier 1 — Use estimated_living_cost from university program (if > 0)
    Tier 2 — Use city-level override (expensive cities: NYC, SF, LA etc.)
    Tier 3 — Use state/province-level average
    Tier 4 — Use country-level default
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Static Lookup Tables ───────────────────────────────────────────────────────

# Government visa application fees in USD (one-time charge)
VISA_FEES = {
    'USA': {
        'visa_type': 'F-1 Student Visa',
        'application_fee': 185.0,
        'additional_fee': 350.0,
        'additional_fee_label': 'SEVIS I-901 Fee',
        'total': 535.0,
    },
    'UK': {
        'visa_type': 'Student Visa',
        'application_fee': 490.0,
        'additional_fee': 0.0,
        'additional_fee_label': None,
        'total': 490.0,
    },
    'DE': {
        'visa_type': 'Student Visa (National D)',
        'application_fee': 80.0,
        'additional_fee': 0.0,
        'additional_fee_label': None,
        'total': 80.0,
    },
    'CA': {
        'visa_type': 'Study Permit',
        'application_fee': 150.0,
        'additional_fee': 0.0,
        'additional_fee_label': None,
        'total': 150.0,
    },
    'AU': {
        'visa_type': 'Student Visa (Subclass 500)',
        'application_fee': 710.0,
        'additional_fee': 0.0,
        'additional_fee_label': None,
        'total': 710.0,
    },
}

# Annual health insurance costs in USD
INSURANCE_COSTS = {
    'USA': {
        'annual_cost': 1500.0,
        'program_name': 'University Health Insurance Plan',
        'notes': 'Average across US universities — varies by institution',
    },
    'UK': {
        'annual_cost': 470.0,
        'program_name': 'Immigration Health Surcharge (IHS)',
        'notes': 'Paid upfront for full visa duration at time of application',
    },
    'DE': {
        'annual_cost': 1440.0,
        'program_name': 'Statutory Health Insurance (GKV)',
        'notes': 'Approx. €110-120/month — mandatory for students under 30',
    },
    'CA': {
        'annual_cost': 750.0,
        'program_name': 'Provincial Health Insurance',
        'notes': 'Average across provinces — some provinces have waiting periods',
    },
    'AU': {
        'annual_cost': 600.0,
        'program_name': 'Overseas Student Health Cover (OSHC)',
        'notes': 'Mandatory for all international student visa holders',
    },
}

# ── Living Cost Fallback Tables ────────────────────────────────────────────────
#
# Annual living cost in USD. Covers rent, food, transport, utilities, misc.
# Calibrated against real scraped data where available, supplemented by
# international student cost-of-living reports (EduCanada, NCES, IDP etc.)
#
# Priority: Tier1 (university data) > Tier2 (city) > Tier3 (state) > Tier4 (country)

# Tier 2 — City-level overrides (cities that differ significantly from state avg)
CITY_LIVING_COSTS = {
    # USA cities
    'new york':        28000,
    'new york city':   28000,
    'manhattan':       28000,
    'brooklyn':        24000,
    'san francisco':   30000,
    'los angeles':     27000,
    'boston':          26000,
    'cambridge':       26000,
    'seattle':         24000,
    'washington':      22000,
    'washington dc':   22000,
    'chicago':         20000,
    'miami':           20000,
    'san jose':        27000,
    'san diego':       24000,
    'denver':          18000,
    'austin':          16000,
    'dallas':          14000,
    'houston':         13000,
    'buffalo':         16500,
    'hoboken':         22000,
    'newark':          20000,
    'baltimore':       17000,
    'philadelphia':    18000,
    'pittsburgh':      15000,
    'cleveland':       14000,
    'st. louis':       14000,
    'st louis':        14000,
    'binghamton':      13000,
    'flagstaff':       16000,
    'tucson':          14000,
    'west haven':      17000,
    'providence':      18000,
    'fort worth':      14000,
    'san antonio':     13500,
    'warrensburg':     11000,
    'auburn':          10000,
    # Canada cities
    'toronto':         18000,
    'vancouver':       20000,
    'montreal':        14000,
    'calgary':         15000,
    'ottawa':          14000,
    'edmonton':        13000,
    'kingston':        13000,
    'london':          12000,   # London, Ontario
    'kitchener':       12000,
    'etobicoke':       16000,
    # UK cities
    'london':          20000,   # will be overridden by country context
    'bath':            16000,
    'peterborough':    13000,
    'edinburgh':       15000,
    'manchester':      13000,
    'birmingham':      13000,
    # Australia cities
    'sydney':          18000,
    'melbourne':       17000,
    'brisbane':        15000,
    'adelaide':        14000,
    'perth':           15000,
    # Germany cities
    'berlin':          12000,
    'munich':          14000,
    'hamburg':         13000,
    'frankfurt':       13000,
    # Singapore / other
    'singapore':       18000,
}

# Tier 3 — US State averages (annual, USD)
# Calibrated from scraped data + NCES international student reports
US_STATE_LIVING_COSTS = {
    'Alabama':              10000,
    'Alaska':               16000,
    'Arizona':              16000,
    'Arkansas':             10000,
    'California':           25000,
    'Colorado':             18000,
    'Connecticut':          20000,
    'Delaware':             16000,
    'Florida':              16000,
    'Georgia':              14000,
    'Hawaii':               22000,
    'Idaho':                13000,
    'Illinois':             18000,
    'Indiana':              13000,
    'Iowa':                 12000,
    'Kansas':               12000,
    'Kentucky':             12000,
    'Louisiana':            13000,
    'Maine':                15000,
    'Maryland':             20000,
    'Massachusetts':        24000,
    'Michigan':             14000,
    'Minnesota':            15000,
    'Mississippi':          10000,
    'Missouri':             13000,
    'Montana':              13000,
    'Nebraska':             12000,
    'Nevada':               16000,
    'New Hampshire':        17000,
    'New Jersey':           22000,
    'New Mexico':           13000,
    'New York':             22000,
    'North Carolina':       14000,
    'North Dakota':         11000,
    'Ohio':                 14000,
    'Oklahoma':             11000,
    'Oregon':               18000,
    'Pennsylvania':         17000,
    'Rhode Island':         18000,
    'South Carolina':       13000,
    'South Dakota':         11000,
    'Tennessee':            13000,
    'Texas':                13000,
    'Utah':                 14000,
    'Vermont':              17000,
    'Virginia':             18000,
    'Washington':           20000,
    'West Virginia':        11000,
    'Wisconsin':            13000,
    'Wyoming':              12000,
    'District of Columbia': 24000,
}

# Canadian province averages (annual, USD)
CA_PROVINCE_LIVING_COSTS = {
    'Alberta':                13000,
    'British Columbia':       18000,
    'Manitoba':               12000,
    'New Brunswick':          11000,
    'Newfoundland':           11000,
    'Nova Scotia':            12000,
    'Ontario':                15000,
    'Prince Edward Island':   11000,
    'Quebec':                 13000,
    'Saskatchewan':           11000,
    'YUKON':                  14000,
}

# Australian state averages (annual, USD)
AU_STATE_LIVING_COSTS = {
    'New South Wales':        18000,
    'Victoria':               17000,
    'Queensland':             15000,
    'South Australia':        14000,
    'Western Australia':      15000,
    'Tasmania':               13000,
    'Australian Capital Territory': 16000,
    'Northern Territory':     14000,
}

# UK region averages (annual, USD)
UK_REGION_LIVING_COSTS = {
    'England':   15000,
    'Scotland':  14000,
    'Wales':     13000,
    'London':    20000,   # treated as region
}

# Germany state averages (annual, USD)
DE_STATE_LIVING_COSTS = {
    'Bavaria':              13000,
    'Berlin':               12000,
    'Hamburg':              13000,
    'Baden-Württemberg':    12000,
    'North Rhine-Westphalia': 11000,
}

# Tier 4 — Country-level defaults (fallback of last resort)
COUNTRY_LIVING_DEFAULTS = {
    'USA': 16000,
    'UK':  15000,
    'DE':  11000,
    'CA':  14000,
    'AU':  16000,
}

# Affordability thresholds
AFFORDABILITY_BANDS = [
    (1.0,  'Fully Funded',     'Student can fully self-fund the program.'),
    (0.75, 'Mostly Funded',    'Minor loan or sponsorship may be needed.'),
    (0.50, 'Partially Funded', 'Significant funding gap — explore scholarships and education loans.'),
    (0.0,  'Underfunded',      'High financial rejection risk. Consider deferring or seeking full sponsorship.'),
]


# ── Living Cost Resolver ───────────────────────────────────────────────────────

def resolve_living_cost(
    university_value: float,
    city: str,
    state_province: str,
    country_code: str,
) -> tuple[float, str]:
    """
    Resolve annual living cost using 4-tier priority lookup.

    Returns:
        (annual_living_cost_usd, source_label)
        source_label tells frontend where the figure came from.
    """
    # Tier 1 — university's own data
    if university_value and university_value > 0:
        return university_value, 'university_data'

    # Tier 2 — city override
    if city:
        city_key = city.strip().lower()
        if city_key in CITY_LIVING_COSTS:
            return float(CITY_LIVING_COSTS[city_key]), f'city_average:{city}'

    # Tier 3 — state/province lookup
    if state_province:
        state_key = state_province.strip()

        if country_code == 'USA' and state_key in US_STATE_LIVING_COSTS:
            return float(US_STATE_LIVING_COSTS[state_key]), f'state_average:{state_key}'

        if country_code == 'CA' and state_key in CA_PROVINCE_LIVING_COSTS:
            return float(CA_PROVINCE_LIVING_COSTS[state_key]), f'province_average:{state_key}'

        if country_code == 'AU' and state_key in AU_STATE_LIVING_COSTS:
            return float(AU_STATE_LIVING_COSTS[state_key]), f'state_average:{state_key}'

        if country_code == 'UK' and state_key in UK_REGION_LIVING_COSTS:
            return float(UK_REGION_LIVING_COSTS[state_key]), f'region_average:{state_key}'

        if country_code == 'DE' and state_key in DE_STATE_LIVING_COSTS:
            return float(DE_STATE_LIVING_COSTS[state_key]), f'state_average:{state_key}'

    # Tier 4 — country default
    default = COUNTRY_LIVING_DEFAULTS.get(country_code, 15000)
    return float(default), f'country_average:{country_code}'


# ── Result Dataclass ───────────────────────────────────────────────────────────

@dataclass
class CostBreakdown:
    """Full cost estimate result for one program."""

    program_id:     int   = 0
    university_name: str  = ''
    program_name:   str   = ''
    degree_type:    str   = ''
    country:        str   = ''
    duration_months: int  = 24
    duration_years:  float = 2.0

    # Component 1 — Tuition
    annual_tuition: float = 0.0
    total_tuition:  float = 0.0

    # Component 2 — Living
    annual_living:       float = 0.0
    total_living:        float = 0.0
    living_cost_source:  str   = 'university_data'   # which tier was used

    # Component 3 — Visa
    visa_type:                str   = ''
    visa_application_fee:     float = 0.0
    visa_additional_fee:      float = 0.0
    visa_additional_fee_label: str  = ''
    total_visa_fee:           float = 0.0

    # Component 4 — Insurance
    insurance_program_name: str   = ''
    insurance_notes:        str   = ''
    annual_insurance:       float = 0.0
    total_insurance:        float = 0.0

    # Totals
    first_year_cost:    float = 0.0
    total_program_cost: float = 0.0

    # Scholarship
    available_scholarships:  int   = 0
    max_scholarship_amount:  float = 0.0
    adjusted_total_cost:     float = 0.0

    # Affordability
    student_savings:      float = 0.0
    has_sponsor:          bool  = False
    effective_funds:      float = 0.0
    funding_gap:          float = 0.0
    coverage_percent:     float = 0.0
    affordability_status: str   = ''
    affordability_note:   str   = ''


# ── Main Estimator ─────────────────────────────────────────────────────────────

def calculate_cost(
    django_program,
    target_country: str,
    student_savings: float = 0.0,
    has_sponsor: bool = False,
) -> CostBreakdown:
    """
    Calculate full cost breakdown for one university program.

    Uses 3-tier living cost fallback when university data is missing.
    """
    result = CostBreakdown(
        program_id=django_program.id,
        university_name=django_program.university.name,
        program_name=django_program.program_name,
        degree_type=django_program.degree_type,
        country=target_country,
    )

    # ── Duration ───────────────────────────────────────────────────────────────
    duration_months = django_program.duration_months or 24
    duration_years  = round(duration_months / 12, 2)
    result.duration_months = duration_months
    result.duration_years  = duration_years

    # ── Component 1: Tuition ───────────────────────────────────────────────────
    annual_tuition   = float(django_program.tuition_fee_per_year or 0)
    result.annual_tuition = annual_tuition
    result.total_tuition  = round(annual_tuition * duration_years, 2)

    # ── Component 2: Living Expenses (3-tier fallback) ─────────────────────────
    raw_living   = float(django_program.estimated_living_cost or 0)
    city         = getattr(django_program.university, 'city', '') or ''
    state        = getattr(django_program.university, 'state_province', '') or ''

    annual_living, living_source = resolve_living_cost(
        raw_living, city, state, target_country
    )
    result.annual_living      = annual_living
    result.total_living       = round(annual_living * duration_years, 2)
    result.living_cost_source = living_source

    # ── Component 3: Visa Fee ──────────────────────────────────────────────────
    visa_info = VISA_FEES.get(target_country, {
        'visa_type': 'Student Visa', 'application_fee': 0.0,
        'additional_fee': 0.0, 'additional_fee_label': None, 'total': 0.0,
    })
    result.visa_type                = visa_info['visa_type']
    result.visa_application_fee     = visa_info['application_fee']
    result.visa_additional_fee      = visa_info['additional_fee']
    result.visa_additional_fee_label = visa_info['additional_fee_label'] or ''
    result.total_visa_fee           = visa_info['total']

    # ── Component 4: Health Insurance ──────────────────────────────────────────
    ins_info            = INSURANCE_COSTS.get(target_country, {
        'annual_cost': 0.0, 'program_name': 'Health Insurance', 'notes': '',
    })
    annual_insurance             = ins_info['annual_cost']
    result.insurance_program_name = ins_info['program_name']
    result.insurance_notes        = ins_info['notes']
    result.annual_insurance       = annual_insurance
    result.total_insurance        = round(annual_insurance * duration_years, 2)

    # ── Totals ─────────────────────────────────────────────────────────────────
    result.first_year_cost = round(
        annual_tuition + annual_living + result.total_visa_fee + annual_insurance, 2
    )
    result.total_program_cost = round(
        result.total_tuition + result.total_living +
        result.total_visa_fee + result.total_insurance, 2
    )

    # ── Scholarship Deduction ──────────────────────────────────────────────────
    result.available_scholarships  = django_program.total_scholarships or 0
    result.max_scholarship_amount  = float(django_program.total_scholarship_amount or 0)
    result.adjusted_total_cost     = round(
        max(result.total_program_cost - result.max_scholarship_amount, 0), 2
    )

    # ── Affordability Check ────────────────────────────────────────────────────
    result.student_savings = student_savings
    result.has_sponsor     = has_sponsor
    effective_funds        = student_savings * 1.20 if has_sponsor else student_savings
    result.effective_funds = round(effective_funds, 2)

    total = result.total_program_cost
    if total > 0:
        result.coverage_percent = round((effective_funds / total) * 100, 1)
        result.funding_gap      = round(max(total - effective_funds, 0), 2)
    else:
        result.coverage_percent = 100.0
        result.funding_gap      = 0.0

    coverage_ratio = effective_funds / total if total > 0 else 1.0
    for threshold, status, note in AFFORDABILITY_BANDS:
        if coverage_ratio >= threshold:
            result.affordability_status = status
            result.affordability_note   = note
            break

    return result


def cost_to_dict(cost: CostBreakdown) -> dict:
    """Convert CostBreakdown to JSON-serialisable dict for API response."""
    return {
        'program_id':     cost.program_id,
        'university_name': cost.university_name,
        'program_name':   cost.program_name,
        'degree_type':    cost.degree_type,
        'country':        cost.country,
        'duration': {
            'months': cost.duration_months,
            'years':  cost.duration_years,
        },
        'cost_breakdown': {
            'tuition': {
                'annual': cost.annual_tuition,
                'total':  cost.total_tuition,
            },
            'living_expenses': {
                'annual': cost.annual_living,
                'total':  cost.total_living,
                'source': cost.living_cost_source,   # transparency — shows which tier was used
            },
            'visa': {
                'visa_type':            cost.visa_type,
                'application_fee':      cost.visa_application_fee,
                'additional_fee':       cost.visa_additional_fee,
                'additional_fee_label': cost.visa_additional_fee_label,
                'total_visa_fee':       cost.total_visa_fee,
                'note': 'One-time charge — paid once regardless of duration',
            },
            'health_insurance': {
                'program_name': cost.insurance_program_name,
                'annual':       cost.annual_insurance,
                'total':        cost.total_insurance,
                'notes':        cost.insurance_notes,
            },
        },
        'totals': {
            'first_year_cost':    cost.first_year_cost,
            'total_program_cost': cost.total_program_cost,
        },
        'scholarships': {
            'available_count':    cost.available_scholarships,
            'max_amount':         cost.max_scholarship_amount,
            'adjusted_total_cost': cost.adjusted_total_cost,
        },
        'affordability': {
            'student_savings':  cost.student_savings,
            'has_sponsor':      cost.has_sponsor,
            'effective_funds':  cost.effective_funds,
            'funding_gap':      cost.funding_gap,
            'coverage_percent': cost.coverage_percent,
            'status':           cost.affordability_status,
            'note':             cost.affordability_note,
        },
    }