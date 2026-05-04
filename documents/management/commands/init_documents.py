from django.core.management.base import BaseCommand
from documents.models import DocumentDefinition


class Command(BaseCommand):
    help = 'Initialize standard document definitions for all countries'

    def handle(self, *args, **kwargs):
        definitions = [

            # ─────────────────────────────────────────
            # UNIVERSAL  (country='ALL')
            # ─────────────────────────────────────────
            {
                'name': 'Passport (Front & Back)',
                'slug': 'passport',
                'description': 'Scanned copy of the bio-data page and last page of your valid passport.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'CV / Resume',
                'slug': 'cv',
                'description': 'Updated Curriculum Vitae highlighting academic and professional experience.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'University Offer / Acceptance Letter',
                'slug': 'offer-letter',
                'description': 'Official letter of admission from the university.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Bank Statement (6 Months)',
                'slug': 'bank-statement',
                'description': 'Most recent 6-month bank statement showing sufficient funds.',
                'country': 'ALL',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'English Proficiency Certificate (IELTS/TOEFL/PTE)',
                'slug': 'english-proficiency',
                'description': 'Official score report from an accepted English language test.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Academic Transcripts',
                'slug': 'transcripts',
                'description': 'Official academic transcripts from all previous institutions.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Medical Certificate',
                'slug': 'medical-certificate',
                'description': 'Health certificate from a registered medical practitioner.',
                'country': 'ALL',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Police Clearance Certificate',
                'slug': 'police-clearance',
                'description': 'Criminal background clearance certificate from your home country.',
                'country': 'ALL',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Passport-Sized Photographs',
                'slug': 'photos',
                'description': 'Recent passport-sized photographs as per the destination country specifications.',
                'country': 'ALL',
                'phase': 'VISA',
                'is_mandatory': True,
                'requires_ai_extraction': False,
            },
            {
                'name': 'Statement of Purpose (SOP)',
                'slug': 'sop',
                'description': 'Personal essay explaining your academic goals and reasons for choosing the program.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Letters of Recommendation',
                'slug': 'recommendation-letters',
                'description': 'At least two academic or professional reference letters.',
                'country': 'ALL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Health / Travel Insurance',
                'slug': 'travel-insurance',
                'description': 'Valid health or travel insurance coverage for the duration of stay.',
                'country': 'ALL',
                'phase': 'PRE-DEPARTURE',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # USA  (F-1 Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'I-20 Form (SEVIS)',
                'slug': 'usa-i20',
                'description': 'Certificate of Eligibility for Nonimmigrant Student Status issued by the university.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'SEVIS Fee Receipt (I-901)',
                'slug': 'usa-sevis-fee',
                'description': 'Proof of payment of the SEVIS I-901 fee.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'DS-160 Confirmation Page',
                'slug': 'usa-ds160',
                'description': 'Completed and submitted DS-160 online nonimmigrant visa application confirmation.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Visa Interview Appointment Letter',
                'slug': 'usa-interview-appt',
                'description': 'Scheduled visa interview appointment confirmation from the US Embassy/Consulate.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Financial Proof / Sponsorship Letter',
                'slug': 'usa-finance',
                'description': 'Proof of liquid assets or sponsor letter covering tuition and living expenses.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'GRE / GMAT Score Report',
                'slug': 'usa-gre-gmat',
                'description': 'Official standardized test scores required by the university.',
                'country': 'USA',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },
            {
                'name': 'Enrollment / Tuition Fee Receipt',
                'slug': 'usa-enrollment-receipt',
                'description': 'Proof of paid enrollment or tuition deposit.',
                'country': 'USA',
                'phase': 'VISA',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # UK  (Student Visa – Tier 4)
            # ─────────────────────────────────────────
            {
                'name': 'CAS (Confirmation of Acceptance for Studies)',
                'slug': 'uk-cas',
                'description': 'CAS reference number issued by your UK university.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'TB Test Certificate',
                'slug': 'uk-tb-test',
                'description': 'Tuberculosis test result from a UK Visas & Immigration approved clinic.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'UKVI IELTS / English Test Report',
                'slug': 'uk-ukvi-english',
                'description': 'IELTS for UKVI or other approved Secure English Language Test (SELT).',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Financial Evidence (28-Day Bank Statement)',
                'slug': 'uk-finance',
                'description': 'Bank statement showing required funds held continuously for 28 days.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'ATAS Certificate (if required)',
                'slug': 'uk-atas',
                'description': 'Academic Technology Approval Scheme certificate for certain STEM subjects.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': False,
            },
            {
                'name': 'Parental / Guardian Consent Letter',
                'slug': 'uk-parental-consent',
                'description': 'Required if applicant is under 18 years old.',
                'country': 'UK',
                'phase': 'VISA',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # CANADA  (Study Permit)
            # ─────────────────────────────────────────
            {
                'name': 'Letter of Acceptance (DLI)',
                'slug': 'ca-acceptance-letter',
                'description': 'Acceptance letter from a Designated Learning Institution (DLI).',
                'country': 'CA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Financial Support',
                'slug': 'ca-finance',
                'description': 'Bank statement or GIC showing funds to cover tuition and living costs.',
                'country': 'CA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Guaranteed Investment Certificate (GIC)',
                'slug': 'ca-gic',
                'description': 'GIC from a participating Canadian financial institution (SDS stream).',
                'country': 'CA',
                'phase': 'VISA',
                'is_mandatory': False,
            },
            {
                'name': 'Quebec Acceptance Certificate (CAQ)',
                'slug': 'ca-caq',
                'description': 'Required if studying in the province of Quebec.',
                'country': 'CA',
                'phase': 'VISA',
                'is_mandatory': False,
            },
            {
                'name': 'Biometrics Enrollment Receipt',
                'slug': 'ca-biometrics',
                'description': 'Proof of biometric data submission at a Service Canada or IRCC office.',
                'country': 'CA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Immigration Medical Exam (IME) Results',
                'slug': 'ca-medical-exam',
                'description': 'Medical examination completed by a panel physician approved by IRCC.',
                'country': 'CA',
                'phase': 'VISA',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # AUSTRALIA  (Student Visa – Subclass 500)
            # ─────────────────────────────────────────
            {
                'name': 'Confirmation of Enrolment (CoE)',
                'slug': 'au-coe',
                'description': 'CoE document issued by an Australian CRICOS-registered institution.',
                'country': 'AU',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Overseas Student Health Cover (OSHC)',
                'slug': 'au-oshc',
                'description': 'OSHC insurance policy valid for the duration of your student visa.',
                'country': 'AU',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Genuine Temporary Entrant (GTE) Statement',
                'slug': 'au-gte',
                'description': 'Personal statement explaining your intention to stay temporarily in Australia.',
                'country': 'AU',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Financial Capacity',
                'slug': 'au-finance',
                'description': 'Evidence of funds for tuition, travel, and living expenses.',
                'country': 'AU',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Skills Assessment (if applicable)',
                'slug': 'au-skills-assessment',
                'description': 'Required for certain vocational or trade programs.',
                'country': 'AU',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # GERMANY  (Student Applicant Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Blocked Account (Sperrkonto) Proof',
                'slug': 'de-blocked-account',
                'description': 'Confirmation of blocked account holding the required annual living amount.',
                'country': 'DE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'University Admission Letter / Study Place Confirmation',
                'slug': 'de-admission-letter',
                'description': 'Official Zulassung (admission) letter from a German university.',
                'country': 'DE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'APS Certificate (for certain nationalities)',
                'slug': 'de-aps',
                'description': 'Academic Evaluation Centre certificate verifying academic qualifications.',
                'country': 'DE',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },
            {
                'name': 'Proof of German / English Proficiency',
                'slug': 'de-language',
                'description': 'TestDaF, DSH, or IELTS/TOEFL depending on the program language.',
                'country': 'DE',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Health Insurance Proof',
                'slug': 'de-health-insurance',
                'description': 'German statutory or recognized health insurance certificate.',
                'country': 'DE',
                'phase': 'PRE-DEPARTURE',
                'is_mandatory': True,
            },
            {
                'name': 'Enrollment Confirmation (Immatrikulationsbescheinigung)',
                'slug': 'de-immatrikulation',
                'description': 'Official enrollment certificate from the German university.',
                'country': 'DE',
                'phase': 'POST-ARRIVAL',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # NEW ZEALAND  (Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Offer of Place (Enrollment Letter)',
                'slug': 'nz-offer-of-place',
                'description': 'Enrollment letter from a New Zealand NZQA-accredited institution.',
                'country': 'NZ',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Funds',
                'slug': 'nz-finance',
                'description': 'Evidence of sufficient funds for tuition and living costs.',
                'country': 'NZ',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Medical and Chest X-Ray Certificate',
                'slug': 'nz-medical-xray',
                'description': 'Medical examination and chest X-ray from an Immigration New Zealand panel doctor.',
                'country': 'NZ',
                'phase': 'VISA',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # IRELAND  (Study Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Acceptance / Enrollment Letter',
                'slug': 'ie-acceptance',
                'description': 'Official letter from an Irish ILEP-listed institution.',
                'country': 'IE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Tuition Fee Payment',
                'slug': 'ie-tuition-payment',
                'description': 'Receipt showing payment of course tuition fees.',
                'country': 'IE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Accommodation',
                'slug': 'ie-accommodation',
                'description': 'Confirmed accommodation details in Ireland.',
                'country': 'IE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Private Medical Insurance',
                'slug': 'ie-health-insurance',
                'description': 'Health insurance policy valid in Ireland.',
                'country': 'IE',
                'phase': 'VISA',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # FRANCE  (VLS-TS / Long-Stay Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Campus France Attestation',
                'slug': 'fr-campus-france',
                'description': 'Proof of completed Campus France procedure (mandatory for most nationalities).',
                'country': 'FR',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'University Acceptance Letter',
                'slug': 'fr-acceptance',
                'description': 'Official enrollment or conditional acceptance from a French institution.',
                'country': 'FR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Accommodation in France',
                'slug': 'fr-accommodation',
                'description': 'Rental agreement, university housing confirmation, or host declaration.',
                'country': 'FR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'French Proficiency Certificate (DELF/DALF/TCF)',
                'slug': 'fr-language',
                'description': 'Required for French-medium programs.',
                'country': 'FR',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # NETHERLANDS  (MVV / Residence Permit)
            # ─────────────────────────────────────────
            {
                'name': 'Proof of Admission (Dutch University)',
                'slug': 'nl-admission',
                'description': 'Admission letter from a recognised Dutch higher education institution.',
                'country': 'NL',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Apostille-Certified Diplomas',
                'slug': 'nl-apostille-diplomas',
                'description': 'Apostille-certified copies of previous degrees and transcripts.',
                'country': 'NL',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Sufficient Funds',
                'slug': 'nl-finance',
                'description': 'Bank statement or scholarship letter covering living costs.',
                'country': 'NL',
                'phase': 'VISA',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # SWEDEN  (Student Residence Permit)
            # ─────────────────────────────────────────
            {
                'name': 'University Admission Decision',
                'slug': 'se-admission',
                'description': 'Official decision letter from a Swedish university or university college.',
                'country': 'SE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Full Tuition Fee Payment',
                'slug': 'se-tuition',
                'description': 'Receipt confirming full tuition fee payment for the first semester/year.',
                'country': 'SE',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Financial Means',
                'slug': 'se-finance',
                'description': 'Evidence of sufficient funds (approx. SEK 8,514/month) for living expenses.',
                'country': 'SE',
                'phase': 'VISA',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # JAPAN  (Student Visa – CoE)
            # ─────────────────────────────────────────
            {
                'name': 'Certificate of Eligibility (CoE)',
                'slug': 'jp-coe',
                'description': 'Certificate of Eligibility issued by Japanese Immigration on behalf of the school.',
                'country': 'JP',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Admission Letter from Japanese School',
                'slug': 'jp-admission',
                'description': 'Acceptance letter from a Japanese MOE-approved institution.',
                'country': 'JP',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Guarantor / Financial Sponsor Statement',
                'slug': 'jp-guarantor',
                'description': 'Signed statement from a financial guarantor along with their bank details.',
                'country': 'JP',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Japanese Language Proficiency (JLPT / NAT-TEST)',
                'slug': 'jp-language',
                'description': 'Required for Japanese-medium programs.',
                'country': 'JP',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # SOUTH KOREA  (D-2 Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Admission Letter (Korean University)',
                'slug': 'kr-admission',
                'description': 'Official acceptance letter from a Korean university.',
                'country': 'KR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Financial Ability',
                'slug': 'kr-finance',
                'description': 'Bank statement or deposit certificate meeting the minimum balance requirement.',
                'country': 'KR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'TOPIK Score (Korean Proficiency)',
                'slug': 'kr-topik',
                'description': 'Required for Korean-medium programs.',
                'country': 'KR',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # MALAYSIA  (Student Pass)
            # ─────────────────────────────────────────
            {
                'name': 'Offer Letter from Malaysian Institution',
                'slug': 'my-offer-letter',
                'description': 'Acceptance letter from a MOHE-approved Malaysian institution.',
                'country': 'MY',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'EMGS Health Screening Report',
                'slug': 'my-emgs-health',
                'description': 'Medical screening done through Education Malaysia Global Services (EMGS).',
                'country': 'MY',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Academic Qualifications (Certified)',
                'slug': 'my-academic-docs',
                'description': 'Certified true copies of all academic certificates and transcripts.',
                'country': 'MY',
                'phase': 'ADMISSION',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # SINGAPORE  (Student's Pass)
            # ─────────────────────────────────────────
            {
                'name': 'In-Principle Approval (IPA) Letter',
                'slug': 'sg-ipa',
                'description': 'IPA letter from ICA approving the Student\'s Pass application.',
                'country': 'SG',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'eForm 16 (ICA Application Form)',
                'slug': 'sg-eform16',
                'description': 'Completed eForm 16 for Student\'s Pass application via SOLAR system.',
                'country': 'SG',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Acceptance Letter from Singapore Institution',
                'slug': 'sg-acceptance',
                'description': 'Official enrollment letter from an MOE/CPE-registered institution.',
                'country': 'SG',
                'phase': 'VISA',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # TURKEY  (Student Residence Permit)
            # ─────────────────────────────────────────
            {
                'name': 'Acceptance Letter (Turkish University)',
                'slug': 'tr-acceptance',
                'description': 'Acceptance letter from a YÖK-accredited Turkish university.',
                'country': 'TR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Proof of Accommodation in Turkey',
                'slug': 'tr-accommodation',
                'description': 'Rental contract or dormitory reservation in Turkey.',
                'country': 'TR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Health Insurance in Turkey',
                'slug': 'tr-health-insurance',
                'description': 'Valid health insurance policy covering Turkey.',
                'country': 'TR',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'YTB Scholarship Approval (if applicable)',
                'slug': 'tr-ytb-scholarship',
                'description': 'Türkiye Scholarships approval letter from the Presidency for Turks Abroad.',
                'country': 'TR',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # CHINA  (X1 / X2 Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'JW201 / JW202 Form',
                'slug': 'cn-jw-form',
                'description': 'Application form for foreign students studying in China issued by the university.',
                'country': 'CN',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Admission Notice from Chinese University',
                'slug': 'cn-admission',
                'description': 'Official admission notice from a Chinese Ministry of Education-approved university.',
                'country': 'CN',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Physical Examination Record for Foreigners',
                'slug': 'cn-physical-exam',
                'description': 'Health examination form completed at a China-approved health screening facility.',
                'country': 'CN',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'HSK Certificate (Chinese Proficiency)',
                'slug': 'cn-hsk',
                'description': 'Required for Chinese-medium programs.',
                'country': 'CN',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },
            {
                'name': 'CSC Scholarship Approval (if applicable)',
                'slug': 'cn-csc-scholarship',
                'description': 'Chinese Government Scholarship (CSC) approval letter.',
                'country': 'CN',
                'phase': 'ADMISSION',
                'is_mandatory': False,
            },

            # ─────────────────────────────────────────
            # RUSSIA  (Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Invitation Letter from Russian University',
                'slug': 'ru-invitation',
                'description': 'Official invitation issued by the Russian university through the Ministry of Internal Affairs.',
                'country': 'RU',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'HIV Test Certificate',
                'slug': 'ru-hiv-test',
                'description': 'Negative HIV test result from an accredited medical lab.',
                'country': 'RU',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Migration Card Registration',
                'slug': 'ru-migration-card',
                'description': 'Migration card received upon entry, required for further registration.',
                'country': 'RU',
                'phase': 'POST-ARRIVAL',
                'is_mandatory': True,
            },

            # ─────────────────────────────────────────
            # SAUDI ARABIA  (Student Visa)
            # ─────────────────────────────────────────
            {
                'name': 'Acceptance Letter (Saudi University)',
                'slug': 'sa-acceptance',
                'description': 'Acceptance letter from a Ministry of Education-recognised Saudi institution.',
                'country': 'SA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Sponsor / Scholarship Approval Letter',
                'slug': 'sa-sponsor',
                'description': 'Letter from a Saudi government body, employer, or scholarship authority.',
                'country': 'SA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
            {
                'name': 'Medical Fitness Certificate',
                'slug': 'sa-medical',
                'description': 'Health certificate from an approved medical centre confirming fitness to study.',
                'country': 'SA',
                'phase': 'VISA',
                'is_mandatory': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for doc_data in definitions:
            obj, created = DocumentDefinition.objects.update_or_create(
                slug=doc_data['slug'],
                defaults=doc_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✔ Created : {obj.country} | {obj.name}"))
            else:
                updated_count += 1
                self.stdout.write(f"  ↺ Updated : {obj.country} | {obj.name}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! {created_count} created, {updated_count} updated "
            f"({created_count + updated_count} total definitions)."
        ))
