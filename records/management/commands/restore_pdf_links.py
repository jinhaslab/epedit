# records/management/commands/restore_pdf_links.py
from django.core.management.base import BaseCommand
from records.models import DiseaseRecord
from django.db.models import Q

class Command(BaseCommand):
    help = 'Restores empty pdf_link fields from original_pdf_link.'

    def handle(self, *args, **options):
        self.stdout.write('Starting to restore PDF links...')
        
        # Find records where pdf_link is null or empty, but original_pdf_link has a value
        records_to_fix = DiseaseRecord.objects.filter(
            Q(pdf_link__isnull=True) | Q(pdf_link=''),
            original_pdf_link__isnull=False
        ).exclude(original_pdf_link='')

        if not records_to_fix.exists():
            self.stdout.write(self.style.SUCCESS('No records needed fixing.'))
            return

        updated_count = 0
        for record in records_to_fix:
            record.pdf_link = record.original_pdf_link
            record.save(update_fields=['pdf_link'])
            updated_count += 1
            self.stdout.write(f'  - Fixed record FID: {record.fid}')

        self.stdout.write(self.style.SUCCESS(f'Successfully restored {updated_count} PDF links.'))
