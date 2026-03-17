"""
Management command to import university data from scraped JSON files.

Usage:
    python manage.py import_universities --folder /path/to/json/folder/
    python manage.py import_universities --file path/to/file.json
    python manage.py import_universities --folder /path/to/folder/ --clear
"""

import json
import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from universities.models import University, UniversityProgram


def _safe_float(value, fallback=None):
    if value is None or value == '':
        return fallback
    try:
        f = float(value)
        return f if f > 0 else fallback
    except (ValueError, TypeError):
        return fallback


def _safe_int(value, fallback=None):
    if value is None or value == '':
        return fallback
    try:
        i = int(float(value))
        return i if i > 0 else fallback
    except (ValueError, TypeError):
        return fallback


def _safe_date(value, fallback=None):
    if not value:
        return fallback
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return fallback


def _normalise_gre(value):
    if not value or value in ('', '0', 0):
        return ''
    return str(value).strip()


def _normalise_degree_type(value):
    mapping = {
        'bachelors': 'Bachelors',
        'masters': 'Masters',
        'phd': 'Phd',
        'diploma': 'Diploma',
    }
    return mapping.get(str(value).strip().lower(), 'Bachelors')


def _normalise_semester(value):
    if not value:
        return ''
    val = str(value).strip().title()
    return val if val in {'Fall', 'Spring', 'Summer', 'Rolling'} else ''


def _extract_records(raw):
    """
    Handles all 3 JSON structures produced by the scraper/notebook:

    Structure A — Original scraped files:
        {
            "total_universities": 500,
            "scraped_at": 123456,
            "universities": [ {...}, {...}, ... ]   ← list of program dicts
        }

    Structure B — Notebook processed sample (pd.to_json orient='records'):
        [
            { "total_universities": 500, "scraped_at": 123, "universities": {...} },
            ...
        ]
        Each item's "universities" value is a single program dict.

    Structure C — Flat list (just in case):
        [ {...}, {...}, ... ]   ← each item is a program dict directly
    """
    records = []

    if isinstance(raw, dict):
        # Structure A: {"universities": [...]}
        unis = raw.get('universities', [])
        if isinstance(unis, list):
            records = unis
        elif isinstance(unis, dict):
            records = [unis]

    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            unis = item.get('universities')
            if unis is None:
                # Structure C: item itself is a program dict
                records.append(item)
            elif isinstance(unis, dict):
                # Structure B: universities is a single program dict
                records.append(unis)
            elif isinstance(unis, list):
                # Nested list inside list
                records.extend(unis)

    return records


class Command(BaseCommand):
    help = 'Import university data from one JSON file or an entire folder of JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Path to a single JSON file.',
        )
        parser.add_argument(
            '--folder',
            type=str,
            default=None,
            help='Path to a folder — all .json files inside will be imported in one run.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing university data before importing.',
        )

    def handle(self, *args, **options):
        # ── Collect files ──────────────────────────────────────────────────────
        files_to_process = []

        if options.get('folder'):
            folder = options['folder']
            if not os.path.isdir(folder):
                raise CommandError(f"Folder not found: {folder}")
            json_files = sorted([
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.endswith('.json')
            ])
            if not json_files:
                raise CommandError(f"No .json files found in: {folder}")
            files_to_process = json_files

        elif options.get('file'):
            f = options['file']
            if not os.path.exists(f):
                raise CommandError(f"File not found: {f}")
            files_to_process = [f]

        else:
            default = os.path.join(settings.BASE_DIR, 'universities_sample_100_records.json')
            if not os.path.exists(default):
                raise CommandError("No file specified. Use --file <path> or --folder <path>")
            files_to_process = [default]

        self.stdout.write(f'\nFound {len(files_to_process)} file(s) to import:')
        for f in files_to_process:
            self.stdout.write(f'  • {os.path.basename(f)}')

        # ── Optionally clear ───────────────────────────────────────────────────
        if options['clear']:
            self.stdout.write(self.style.WARNING('\nClearing existing data...'))
            UniversityProgram.objects.all().delete()
            University.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared.\n'))

        # ── Process each file ──────────────────────────────────────────────────
        total_uc = total_uu = total_pc = total_pu = total_sk = 0

        for file_path in files_to_process:
            fname = os.path.basename(file_path)
            self.stdout.write(f'\nProcessing: {fname}')

            with open(file_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)

            records = _extract_records(raw)
            self.stdout.write(f'  {len(records)} records found')

            if not records:
                self.stdout.write(self.style.WARNING('  No records extracted, skipping.'))
                continue

            uc = uu = pc = pu = sk = 0

            for u in records:
                if not isinstance(u, dict):
                    sk += 1
                    continue

                external_id = str(u.get('universitiesid', '')).strip()
                uni_name = str(u.get('university', '')).strip()

                if not external_id or not uni_name:
                    sk += 1
                    continue

                fin_aid_raw = str(u.get('uni_fin_aid', '')).strip().lower()
                uni_obj, created = University.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        'uni_no': str(u.get('uni_no', '')).strip(),
                        'name': uni_name,
                        'university_type': str(u.get('university_type', 'Public')).strip() or 'Public',
                        'city': str(u.get('city', '')).strip(),
                        'state_province': str(u.get('state_province', '')).strip(),
                        'country': str(u.get('country', 'USA')).strip(),
                        'qs_world_ranking': _safe_int(u.get('qs_world_univ_rankings')),
                        'us_news_ranking': _safe_int(u.get('us_news_rankings')),
                        'phone': str(u.get('phone', '')).strip(),
                        'website': str(u.get('uni_website', '')).strip(),
                        'offers_financial_aid': fin_aid_raw in ('yes', '1', 'true'),
                    }
                )
                uc += created
                uu += (not created)

                program_name = str(u.get('program', '')).strip()
                degree_type = _normalise_degree_type(u.get('degree_type', 'Bachelors'))

                if not program_name:
                    sk += 1
                    continue

                app_link = str(u.get('application_link', '') or u.get('depart_contact_info', '')).strip()
                dept_link = str(u.get('depart_link', '') or '').strip()

                _, p_created = UniversityProgram.objects.update_or_create(
                    university=uni_obj,
                    program_name=program_name,
                    degree_type=degree_type,
                    defaults={
                        'department': str(u.get('department', '')).strip(),
                        'degree_name': str(u.get('degree_name', '')).strip(),
                        'is_stem': str(u.get('uni_stem', '0')).strip() in ('1', 'true', 'yes'),
                        'ielts_required': _safe_float(u.get('ielts')),
                        'toefl_required': _safe_float(u.get('toefl')),
                        'pte_required': _safe_float(u.get('pte')),
                        'duolingo_required': _safe_float(u.get('duolingo')),
                        'min_gpa': _safe_float(u.get('academic_requirements_gpa')),
                        'max_backlogs': _safe_int(u.get('num_backlogs')),
                        'gre_required': _normalise_gre(u.get('gre_total')),
                        'gmat_required': _normalise_gre(u.get('gmat_total')),
                        'tuition_fee_per_year': _safe_float(u.get('international_tuition_fee_yr')),
                        'estimated_living_cost': _safe_float(u.get('estimated_living_cost')),
                        'application_fee': _safe_float(u.get('international_app_fee')),
                        'app_fee_waiver_available': str(u.get('app_fee_waiver', '0')).strip() in ('1', 'true', 'yes'),
                        'acceptance_rate': _safe_float(u.get('acceptance_rate')),
                        'duration_months': _safe_int(u.get('duration_of_course_months')),
                        'num_credits': _safe_int(u.get('no_of_credits')),
                        'semester': _normalise_semester(u.get('semester')),
                        'application_deadline': _safe_date(u.get('inter_adm_deadline')),
                        'required_documents_raw': str(u.get('doc_required', '')).strip(),
                        'application_link': app_link[:200] if app_link else '',
                        'department_link': dept_link[:200] if dept_link else '',
                        'total_scholarships': _safe_int(u.get('total_scholarships'), 0) or 0,
                        'total_scholarship_amount': _safe_float(u.get('total_scholarshipsamount'), 0) or 0,
                    }
                )
                pc += p_created
                pu += (not p_created)

            self.stdout.write(
                f'  ✓ Universities: {uc} created, {uu} updated | '
                f'Programs: {pc} created, {pu} updated | '
                f'Skipped: {sk}'
            )
            total_uc += uc; total_uu += uu
            total_pc += pc; total_pu += pu
            total_sk += sk

        # ── Summary ────────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 55))
        self.stdout.write(self.style.SUCCESS('All Files Imported Successfully!'))
        self.stdout.write(f'  Universities  →  {total_uc} created, {total_uu} updated')
        self.stdout.write(f'  Programs      →  {total_pc} created, {total_pu} updated')
        self.stdout.write(f'  Rows skipped  →  {total_sk}')
        self.stdout.write(self.style.SUCCESS('═' * 55))