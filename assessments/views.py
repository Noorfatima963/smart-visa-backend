from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from universities.models import UniversityProgram
from .models import VisaAssessment, UniversityMatch
from .serializers import (
    RunAssessmentSerializer,
    VisaAssessmentListSerializer,
    VisaAssessmentDetailSerializer,
)
from .scoring import (
    build_student_profile,
    build_program_requirements,
    calculate_probability,
    get_missing_factors,
)
from .cost_estimator import (
    calculate_cost,
    cost_to_dict,
    VISA_FEES,
    INSURANCE_COSTS,
)
from .compare import compare_programs


class RunAssessmentView(APIView):
    """
    POST /api/assessments/run/

    Runs the full pipeline:
      1. Eligibility check (via probability score labels)
      2. Success probability scoring (6-factor weighted model)
      3. Cost estimation (tuition + living + visa + insurance)

    Request body:
    {
        "target_country": "USA",
        "target_degree_type": "Masters",
        "target_field": "Computer Science",
        "max_results": 20
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunAssessmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        target_country = data['target_country']
        target_degree_type = data['target_degree_type']
        target_field = data.get('target_field', '')
        max_results = data.get('max_results', 20)

        try:
            django_profile = request.user.profile
        except Exception:
            return Response(
                {'error': 'Student profile not found. Please complete your profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = build_student_profile(django_profile)
        missing_factors = get_missing_factors(student)

        financial = getattr(django_profile, 'financial_profile', None)
        savings_usd = float(financial.approx_savings or 0) if financial else 0.0
        has_sponsor = financial.has_sponsor if financial else False

        programs_qs = UniversityProgram.objects.select_related('university').filter(
            university__country=target_country,
            degree_type=target_degree_type,
        )
        if target_field:
            programs_qs = programs_qs.filter(
                Q(program_name__icontains=target_field) |
                Q(department__icontains=target_field)
            )

        programs = list(programs_qs)

        if not programs:
            assessment = VisaAssessment.objects.create(
                user=request.user,
                target_country=target_country,
                target_degree_type=target_degree_type,
                target_field=target_field,
                status='no_matches',
                overall_score=0,
                total_programs_evaluated=0,
                total_matches_found=0,
                missing_factors=missing_factors,
                profile_snapshot=_build_profile_snapshot(student),
            )
            return Response({
                'assessment_id': assessment.id,
                'status': 'no_matches',
                'message': f'No {target_degree_type} programs found in {target_country}.',
                'missing_factors': missing_factors,
            }, status=status.HTTP_200_OK)

        # Run scoring + cost for every program
        results = []
        for program in programs:
            req = build_program_requirements(program)
            score = calculate_probability(student, req)
            cost = calculate_cost(program, target_country, savings_usd, has_sponsor)
            results.append((score, cost, program))

        results.sort(key=lambda r: r[0].probability_score, reverse=True)

        top_scores = [r[0].probability_score for r in results[:5]]
        overall_score = round(sum(top_scores) / len(top_scores), 1) if top_scores else 0
        matches_found = sum(1 for r in results if r[0].probability_score >= 50)

        scored = [r[0] for r in results]
        score_breakdown = {
            'gpa': round(sum(r.gpa_score for r in scored) / len(scored), 1),
            'language': round(sum(r.language_score for r in scored) / len(scored), 1),
            'financial': round(sum(r.financial_score for r in scored) / len(scored), 1),
            'backlogs': round(sum(r.backlog_score for r in scored) / len(scored), 1),
            'visa_history': round(sum(r.visa_history_score for r in scored) / len(scored), 1),
            'acceptance_rate': round(sum(r.acceptance_rate_score for r in scored) / len(scored), 1),
        }

        assessment = VisaAssessment.objects.create(
            user=request.user,
            target_country=target_country,
            target_degree_type=target_degree_type,
            target_field=target_field,
            status='completed',
            overall_score=overall_score,
            total_programs_evaluated=len(results),
            total_matches_found=matches_found,
            score_breakdown=score_breakdown,
            profile_snapshot=_build_profile_snapshot(student),
            missing_factors=missing_factors,
        )

        top_results = results[:max_results]
        match_objects = []
        for rank, (score_result, cost_result, program) in enumerate(top_results, start=1):
            match_objects.append(UniversityMatch(
                assessment=assessment,
                program_id=score_result.program_id,
                probability_score=score_result.probability_score,
                eligibility=score_result.eligibility,
                gpa_score=score_result.gpa_score,
                language_score=score_result.language_score,
                financial_score=score_result.financial_score,
                backlog_score=score_result.backlog_score,
                visa_history_score=score_result.visa_history_score,
                acceptance_rate_score=score_result.acceptance_rate_score,
                match_reasons=score_result.match_reasons,
                gap_reasons=score_result.gap_reasons,
                cost_data=cost_to_dict(cost_result),
                rank=rank,
            ))
        UniversityMatch.objects.bulk_create(match_objects)

        response_serializer = VisaAssessmentDetailSerializer(assessment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AssessmentHistoryView(APIView):
    """GET /api/assessments/ — All past assessments for the logged-in student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assessments = VisaAssessment.objects.filter(user=request.user)
        serializer = VisaAssessmentListSerializer(assessments, many=True)
        return Response({'count': assessments.count(), 'results': serializer.data})


class AssessmentDetailView(APIView):
    """GET /api/assessments/<id>/ — Full detail with all matches and cost data."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        assessment = get_object_or_404(VisaAssessment, pk=pk, user=request.user)
        serializer = VisaAssessmentDetailSerializer(assessment)
        return Response(serializer.data)


class AssessmentDeleteView(APIView):
    """DELETE /api/assessments/<id>/delete/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        assessment = get_object_or_404(VisaAssessment, pk=pk, user=request.user)
        assessment.delete()
        return Response({'message': 'Assessment deleted.'}, status=status.HTTP_204_NO_CONTENT)


class ProgramCostEstimateView(APIView):
    """
    GET /api/assessments/cost/<program_id>/?country=USA

    Standalone cost estimate for a single program.
    Does not create an assessment — just returns cost breakdown.

    Query params:
        country — USA / UK / DE / CA / AU
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, program_id):
        program = get_object_or_404(
            UniversityProgram.objects.select_related('university'),
            pk=program_id
        )

        country = request.query_params.get('country', 'USA').upper()
        if country not in VISA_FEES:
            return Response(
                {'error': f'Unsupported country: {country}. Choose from: {list(VISA_FEES.keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            financial = request.user.profile.financial_profile
            savings_usd = float(financial.approx_savings or 0)
            has_sponsor = financial.has_sponsor
        except Exception:
            savings_usd = 0.0
            has_sponsor = False

        cost = calculate_cost(program, country, savings_usd, has_sponsor)
        return Response(cost_to_dict(cost))


class CountryCostInfoView(APIView):
    """
    GET /api/assessments/cost-info/<country>/

    Returns fixed visa fee and insurance details for a country.
    Example: GET /api/assessments/cost-info/USA/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, country):
        country = country.upper()
        if country not in VISA_FEES:
            return Response(
                {'error': f'Country not supported. Available: {list(VISA_FEES.keys())}'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'country': country,
            'visa': VISA_FEES[country],
            'health_insurance': INSURANCE_COSTS[country],
        })


# ── Helper ─────────────────────────────────────────────────────────────────────

def _build_profile_snapshot(student) -> dict:
    return {
        'gpa': student.gpa,
        'backlogs': student.backlogs,
        'ielts': student.ielts,
        'toefl': student.toefl,
        'pte': student.pte,
        'duolingo': student.duolingo,
        'savings_usd': student.savings_usd,
        'has_sponsor': student.has_sponsor,
        'has_visa_refusal': student.has_visa_refusal,
    }


class UniversityCompareView(APIView):
    """
    POST /api/assessments/compare/

    Compare two university programs head-to-head against the student's profile.

    Request body:
    {
        "program_a_id": 101,
        "program_b_id": 204
    }

    Returns per-metric winners, probability scores, cost breakdown, and an AI verdict.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        program_a_id = request.data.get('program_a_id')
        program_b_id = request.data.get('program_b_id')

        if not program_a_id or not program_b_id:
            return Response(
                {'error': 'Both program_a_id and program_b_id are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if program_a_id == program_b_id:
            return Response(
                {'error': 'program_a_id and program_b_id must be different programs.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            program_a = UniversityProgram.objects.select_related('university').get(pk=program_a_id)
        except UniversityProgram.DoesNotExist:
            return Response({'error': f'Program {program_a_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            program_b = UniversityProgram.objects.select_related('university').get(pk=program_b_id)
        except UniversityProgram.DoesNotExist:
            return Response({'error': f'Program {program_b_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            django_profile = request.user.profile
        except Exception:
            return Response(
                {'error': 'Student profile not found. Please complete your profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = compare_programs(program_a, program_b, django_profile)
        return Response(result, status=status.HTTP_200_OK)


class ProgramSearchView(APIView):
    """
    GET /api/assessments/programs/search/

    Search programs to find IDs for the compare endpoint.

    Query params (all optional):
        q           — keyword search on program name / university name
        country     — e.g. USA, UK, Canada, Australia, Germany
        degree_type — Masters | Bachelors | Phd | Diploma
        field       — e.g. Computer Science
        university  — partial university name
        page        — page number (default 1)
        page_size   — results per page (default 20, max 50)

    Example:
        GET /api/assessments/programs/search/?country=USA&degree_type=Masters&field=Computer Science
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = UniversityProgram.objects.select_related('university').all()

        q = request.query_params.get('q', '').strip()
        country = request.query_params.get('country', '').strip()
        degree_type = request.query_params.get('degree_type', '').strip()
        field = request.query_params.get('field', '').strip()
        university = request.query_params.get('university', '').strip()

        if q:
            qs = qs.filter(
                Q(program_name__icontains=q) |
                Q(university__name__icontains=q)
            )
        if country:
            qs = qs.filter(university__country__iexact=country)
        if degree_type:
            qs = qs.filter(degree_type=degree_type)
        if field:
            qs = qs.filter(
                Q(program_name__icontains=field) |
                Q(department__icontains=field)
            )
        if university:
            qs = qs.filter(university__name__icontains=university)

        # Pagination
        try:
            page = max(int(request.query_params.get('page', 1)), 1)
            page_size = min(int(request.query_params.get('page_size', 20)), 50)
        except ValueError:
            page, page_size = 1, 20

        total = qs.count()
        offset = (page - 1) * page_size
        items = qs[offset: offset + page_size]

        results = [
            {
                'program_id': p.id,
                'university_name': p.university.name,
                'program_name': p.program_name,
                'degree_type': p.degree_type,
                'country': p.university.country,
                'city': p.university.city,
                'qs_ranking': p.university.qs_world_ranking,
                'tuition_per_year': float(p.tuition_fee_per_year or 0),
                'ielts_required': p.ielts_required,
                'acceptance_rate': p.acceptance_rate,
            }
            for p in items
        ]

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size,
            'results': results,
        })
