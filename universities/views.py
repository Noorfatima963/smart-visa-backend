from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import University, UniversityProgram
from .serializers import (
    UniversityListSerializer,
    UniversityDetailSerializer,
    UniversityProgramSerializer,
)


class UniversityListView(APIView):
    """
    GET /api/universities/
    Returns a list of universities with optional filters.

    Query Parameters:
        search      — filter by university name (case-insensitive)
        state       — filter by state/province
        type        — filter by university_type (Public / Private)
        degree_type — filter by available degree type (Bachelors/Masters/Phd/Diploma)
        stem_only   — pass 'true' to return only STEM programs' universities
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = University.objects.all()

        search = request.query_params.get('search', '').strip()
        state = request.query_params.get('state', '').strip()
        uni_type = request.query_params.get('type', '').strip()
        degree_type = request.query_params.get('degree_type', '').strip()
        stem_only = request.query_params.get('stem_only', '').lower() == 'true'

        if search:
            qs = qs.filter(name__icontains=search)
        if state:
            qs = qs.filter(state_province__icontains=state)
        if uni_type:
            qs = qs.filter(university_type=uni_type)
        if degree_type:
            qs = qs.filter(programs__degree_type=degree_type).distinct()
        if stem_only:
            qs = qs.filter(programs__is_stem=True).distinct()

        serializer = UniversityListSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data
        })


class UniversityDetailView(APIView):
    """
    GET /api/universities/<id>/
    Returns full university detail including all nested programs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        serializer = UniversityDetailSerializer(university)
        return Response(serializer.data)


class UniversityProgramListView(APIView):
    """
    GET /api/universities/<id>/programs/
    Returns all programs for a specific university with optional filters.

    Query Parameters:
        degree_type — filter by Bachelors / Masters / Phd / Diploma
        stem_only   — pass 'true' to return only STEM programs
        max_tuition — filter programs by max annual tuition (USD)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        programs = university.programs.all()

        degree_type = request.query_params.get('degree_type', '').strip()
        stem_only = request.query_params.get('stem_only', '').lower() == 'true'
        max_tuition = request.query_params.get('max_tuition', '').strip()

        if degree_type:
            programs = programs.filter(degree_type=degree_type)
        if stem_only:
            programs = programs.filter(is_stem=True)
        if max_tuition:
            try:
                programs = programs.filter(tuition_fee_per_year__lte=float(max_tuition))
            except ValueError:
                pass

        serializer = UniversityProgramSerializer(programs, many=True)
        return Response({
            'university': university.name,
            'count': programs.count(),
            'programs': serializer.data
        })


class ProgramSearchView(APIView):
    """
    GET /api/universities/programs/search/
    Search programs across all universities.

    Query Parameters:
        q           — search in program_name or department
        degree_type — Bachelors / Masters / Phd / Diploma
        max_tuition — max annual tuition (USD)
        max_ielts   — student's IELTS score — returns programs they qualify for
        min_gpa     — student's GPA — returns programs at or below this requirement
        stem_only   — 'true' for STEM only
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        programs = UniversityProgram.objects.select_related('university').all()

        q = request.query_params.get('q', '').strip()
        degree_type = request.query_params.get('degree_type', '').strip()
        max_tuition = request.query_params.get('max_tuition', '').strip()
        student_ielts = request.query_params.get('max_ielts', '').strip()
        student_gpa = request.query_params.get('min_gpa', '').strip()
        stem_only = request.query_params.get('stem_only', '').lower() == 'true'

        if q:
            programs = programs.filter(
                Q(program_name__icontains=q) | Q(department__icontains=q)
            )
        if degree_type:
            programs = programs.filter(degree_type=degree_type)
        if max_tuition:
            try:
                programs = programs.filter(tuition_fee_per_year__lte=float(max_tuition))
            except ValueError:
                pass
        if student_ielts:
            try:
                # Return programs where student's score meets or exceeds requirement
                programs = programs.filter(
                    Q(ielts_required__lte=float(student_ielts)) | Q(ielts_required__isnull=True)
                )
            except ValueError:
                pass
        if student_gpa:
            try:
                programs = programs.filter(
                    Q(min_gpa__lte=float(student_gpa)) | Q(min_gpa__isnull=True)
                )
            except ValueError:
                pass
        if stem_only:
            programs = programs.filter(is_stem=True)

        serializer = UniversityProgramSerializer(programs[:50], many=True)
        return Response({
            'count': programs.count(),
            'results': serializer.data
        })