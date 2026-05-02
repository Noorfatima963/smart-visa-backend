"""
Management command to import university data from scraped JSON files.

Usage:
    python manage.py import_universities --folder /path/to/json/folder/
    python manage.py import_universities --file path/to/file.json
    python manage.py import_universities --folder /path/to/folder/ --clear
    python manage.py import_universities --folder ... --dry-run --audit-csv /tmp/conflicts.csv
    python manage.py import_universities --folder ... --canonical-key name_geo --id-aliases aliases.json
"""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from universities.models import University, UniversityProgram

CANONICAL_EXTERNAL_ID = 'external_id'
CANONICAL_NAME_GEO = 'name_geo'

_ALIAS_MAX_STEPS = 32


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


def _normalize_uni_name(name):
    return ' '.join(str(name or '').upper().split())


def _geo_key(u):
    """Stable identity for dedupe-by-institution (same scraper name + location)."""
    return (
        _normalize_uni_name(u.get('university', '')),
        str(u.get('city', '')).strip().upper(),
        str(u.get('country', 'USA') or 'USA').strip().upper(),
    )


def _load_id_aliases(path):
    if not path:
        return {}
    if not os.path.exists(path):
        raise CommandError(f"Alias file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise CommandError('ID alias file must be a JSON object mapping scraped id -> canonical id strings.')
    out = {}
    for k, v in raw.items():
        ks, vs = str(k).strip(), str(v).strip()
        if ks and vs:
            out[ks] = vs
    return out


def _resolve_alias_chain(external_id, aliases):
    if not aliases:
        return external_id
    cur = external_id
    seen = set()
    for _ in range(_ALIAS_MAX_STEPS):
        if cur in seen:
            raise CommandError(f'Circular university id alias chain involving "{external_id}"')
        seen.add(cur)
        nxt = aliases.get(cur)
        if not nxt or nxt == cur:
            break
        cur = nxt
    return cur


def _collect_json_files(options):
    """Resolve --folder / --file / default into a list of paths."""
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
        return json_files

    if options.get('file'):
        f = options['file']
        if not os.path.exists(f):
            raise CommandError(f"File not found: {f}")
        return [f]

    default = os.path.join(
        settings.BASE_DIR,
        'univerity-jsondata',
    )
    if not os.path.exists(default):
        raise CommandError(
            "No file specified. Use --file <path> or --folder <path> "
            f"(default sample not found at {default})"
        )
    return [default]


def _scan_geo_conflicts(files_to_process):
    """
    First pass: find (name, city, country) keys that map to more than one scraped universitiesid.
    Returns conflict_keys set and key_to_ids for stdout summary.
    """
    key_to_ids = defaultdict(set)
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        for u in _extract_records(raw):
            if not isinstance(u, dict):
                continue
            uid = str(u.get('universitiesid', '')).strip()
            uni_name = str(u.get('university', '')).strip()
            if not uid or not uni_name:
                continue
            key_to_ids[_geo_key(u)].add(uid)
    conflict_keys = {k for k, ids in key_to_ids.items() if len(ids) > 1}
    return conflict_keys, key_to_ids


def _resolve_external_id_for_row(u, aliases, canonical_key, geo_canonical):
    raw = str(u.get('universitiesid', '')).strip()
    rid = _resolve_alias_chain(raw, aliases)
    if canonical_key == CANONICAL_NAME_GEO:
        gk = _geo_key(u)
        if gk not in geo_canonical:
            geo_canonical[gk] = rid
        return geo_canonical[gk]
    return rid


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
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse files and print counts without writing to the database.',
        )
        parser.add_argument(
            '--audit-csv',
            type=str,
            default=None,
            metavar='PATH',
            help='Write rows whose institution key maps to multiple scraped universitiesid to this CSV.',
        )
        parser.add_argument(
            '--id-aliases',
            type=str,
            default=None,
            metavar='PATH',
            help='JSON object mapping scraped universitiesid -> canonical universitiesid before import.',
        )
        parser.add_argument(
            '--canonical-key',
            type=str,
            choices=[CANONICAL_EXTERNAL_ID, CANONICAL_NAME_GEO],
            default=CANONICAL_EXTERNAL_ID,
            help=(
                'external_id: one DB university per scraped universitiesid (after --id-aliases). '
                'name_geo: merge rows sharing normalized name+city+country onto the first-seen id.'
            ),
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        audit_csv_path = options['audit_csv']
        canonical_key = options['canonical_key']
        aliases = _load_id_aliases(options['id_aliases'])

        files_to_process = _collect_json_files(options)

        self.stdout.write(f'\nFound {len(files_to_process)} file(s) to process:')
        for f in files_to_process:
            self.stdout.write(f'  • {os.path.basename(f)}')

        self.stdout.write(f'  Canonical key: {canonical_key}')
        if aliases:
            self.stdout.write(f'  ID aliases loaded: {len(aliases)} mapping(s)')
        if dry_run:
            self.stdout.write(self.style.WARNING('  Dry-run: no database writes.'))

        conflict_keys, key_to_ids = _scan_geo_conflicts(files_to_process)
        n_conflict_groups = len(conflict_keys)
        if n_conflict_groups:
            self.stdout.write(
                self.style.WARNING(
                    f'\nInstitution keys (name+city+country) with multiple scraped universitiesid: '
                    f'{n_conflict_groups}'
                )
            )
            preview = list(conflict_keys)[:8]
            for key in preview:
                name, city, country = key
                ids = sorted(key_to_ids[key])
                self.stdout.write(f'  • {name} | {city} | {country}  →  ids {ids}')
            if len(conflict_keys) > 8:
                self.stdout.write(f'  … ({len(conflict_keys) - 8} more)')

        if audit_csv_path:
            n_written = self._write_audit_csv(
                audit_csv_path, files_to_process, conflict_keys
            )
            self.stdout.write(self.style.SUCCESS(f'\nAudit CSV written: {audit_csv_path} ({n_written} rows)'))

        if dry_run and options['clear']:
            self.stdout.write(self.style.WARNING('--clear ignored during --dry-run'))

        if not dry_run:
            if options['clear']:
                self.stdout.write(self.style.WARNING('\nClearing existing data...'))
                UniversityProgram.objects.all().delete()
                University.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Cleared.\n'))

        total_uc = total_uu = total_pc = total_pu = total_sk = 0
        geo_canonical = {}
        uni_seen = set()
        prog_seen = set()

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

                raw_uid = str(u.get('universitiesid', '')).strip()
                uni_name = str(u.get('university', '')).strip()

                if not raw_uid or not uni_name:
                    sk += 1
                    continue

                try:
                    external_id = _resolve_external_id_for_row(
                        u, aliases, canonical_key, geo_canonical
                    )
                except CommandError:
                    raise
                if not external_id:
                    sk += 1
                    continue

                fin_aid_raw = str(u.get('uni_fin_aid', '')).strip().lower()
                uni_obj = None

                if dry_run:
                    if external_id not in uni_seen:
                        uni_seen.add(external_id)
                        uc += 1
                    else:
                        uu += 1
                else:
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

                prog_key = (external_id, program_name, degree_type)

                if dry_run:
                    if prog_key not in prog_seen:
                        prog_seen.add(prog_key)
                        pc += 1
                    else:
                        pu += 1
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
            total_uc += uc
            total_uu += uu
            total_pc += pc
            total_pu += pu
            total_sk += sk

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 55))
        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry-run complete (no DB changes).'))
        else:
            self.stdout.write(self.style.SUCCESS('All Files Imported Successfully!'))
        self.stdout.write(f'  Universities  →  {total_uc} created, {total_uu} updated')
        self.stdout.write(f'  Programs      →  {total_pc} created, {total_pu} updated')
        self.stdout.write(f'  Rows skipped  →  {total_sk}')
        self.stdout.write(self.style.SUCCESS('═' * 55))

    def _write_audit_csv(self, path, files_to_process, conflict_keys):
        """Rows from institution keys that appear with multiple scraped universitiesid."""
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        n = 0
        fieldnames = [
            'scraped_universitiesid',
            'resolved_institution_key_name',
            'city',
            'country',
            'university_display',
            'program',
            'degree_type',
            'source_file',
        ]
        with open(path, 'w', encoding='utf-8', newline='') as out:
            w = csv.DictWriter(out, fieldnames=fieldnames)
            w.writeheader()
            for file_path in files_to_process:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                for u in _extract_records(raw):
                    if not isinstance(u, dict):
                        continue
                    uid = str(u.get('universitiesid', '')).strip()
                    uni_name = str(u.get('university', '')).strip()
                    if not uid or not uni_name:
                        continue
                    gk = _geo_key(u)
                    if gk not in conflict_keys:
                        continue
                    name, city, country = gk
                    w.writerow({
                        'scraped_universitiesid': uid,
                        'resolved_institution_key_name': name,
                        'city': city,
                        'country': country,
                        'university_display': uni_name,
                        'program': str(u.get('program', '')).strip(),
                        'degree_type': str(u.get('degree_type', '')).strip(),
                        'source_file': os.path.basename(file_path),
                    })
                    n += 1
        return n