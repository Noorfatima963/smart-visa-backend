from django.core.management.base import BaseCommand
from documents.models import DocumentDefinition

class Command(BaseCommand):
    help = 'Initialize standard document definitions'

    def handle(self, *args, **kwargs):
        definitions = [
            # Universal
            {
                'name': 'Passport (Front & Back)',
                'slug': 'passport',
                'description': 'Scanned copy of the first and last pages of your passport.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True
            },
            {
                'name': 'CV / Resume',
                'slug': 'cv',
                'description': 'Updated Curriculum Vitae.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True
            },
            
            # USA Specific
            {
                'name': 'I-20 Form',
                'slug': 'usa-i20',
                'description': 'Certificate of Eligibility for Nonimmigrant Student Status.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True
            },
            {
                'name': 'Financial Proof (Bank Statement)',
                'slug': 'usa-finance',
                'description': 'Proof of liquid assets to cover tuition and living expenses.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True
            },

            # UK Specific
            {
                'name': 'CAS Statement',
                'slug': 'uk-cas',
                'description': 'Confirmation of Acceptance for Studies.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': True
            },
            {
                'name': 'TB Test Report',
                'slug': 'uk-tb-test',
                'description': 'Tuberculosis test from an approved clinic.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': True
            },

            # Germany Specific
            {
                'name': 'Blocked Account Proof',
                'slug': 'de-blocked-account',
                'description': 'Confirmation of blocked account (Sperrkonto).',
                'country': 'DE',
                'phase': 'VISA',
                'is_mandatory': True
            },
        ]

        for doc_data in definitions:
            obj, created = DocumentDefinition.objects.update_or_create(
                slug=doc_data['slug'],
                defaults=doc_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.name}"))
            else:
                self.stdout.write(f"Updated: {obj.name}")
