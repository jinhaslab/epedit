import json
import os
from django.core.management.base import BaseCommand
from dictionaries.models import DiseaseDictionaryEntry
from django.conf import settings


class Command(BaseCommand):
    help = 'Imports KCD-9 hierarchical data from kcd_hierarchical_data.json to DiseaseDictionaryEntry.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/rag/papps/dzdz/kcd_hierarchical_data.json',
            help='Path to kcd_hierarchical_data.json file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing disease dictionary before import'
        )

    def handle(self, *args, **options):
        json_file_path = options['file']

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"JSON file not found at: {json_file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Importing KCD-9 data from: {json_file_path}"))

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'categories' not in data:
                self.stdout.write(self.style.ERROR("'categories' key not found in JSON file."))
                return

            # Clear existing dictionary if requested
            if options['clear']:
                count = DiseaseDictionaryEntry.objects.all().count()
                DiseaseDictionaryEntry.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f"Cleared {count} existing disease dictionary entries."))

            # Recursive function to extract all disease codes and names
            def extract_diseases(categories, level=1):
                diseases = []
                for cat in categories:
                    # Extract code and name
                    code = cat.get('id', '')
                    name = cat.get('name', '')

                    if code and name:
                        diseases.append({'code': code, 'name': name, 'level': level})

                    # Recursively process children
                    if cat.get('children'):
                        diseases.extend(extract_diseases(cat['children'], level + 1))

                return diseases

            # Extract all diseases from hierarchy
            all_diseases = extract_diseases(data['categories'])

            self.stdout.write(self.style.SUCCESS(f"Found {len(all_diseases)} disease entries to import."))

            # Bulk create disease dictionary entries
            created_count = 0
            skipped_count = 0

            for disease in all_diseases:
                code = disease['code']
                name = disease['name']

                # Check if entry already exists
                if DiseaseDictionaryEntry.objects.filter(disease_name=name).exists():
                    skipped_count += 1
                    continue

                # Create new entry
                DiseaseDictionaryEntry.objects.create(
                    disease_name=name,
                    disease_code=code
                )
                created_count += 1

                # Progress report every 1000 entries
                if created_count % 1000 == 0:
                    self.stdout.write(f"  Created {created_count} entries...")

            self.stdout.write(self.style.SUCCESS(f"\n✅ Import completed!"))
            self.stdout.write(self.style.SUCCESS(f"  - Created: {created_count} new entries"))
            self.stdout.write(self.style.SUCCESS(f"  - Skipped: {skipped_count} duplicates"))
            self.stdout.write(self.style.SUCCESS(f"  - Total in DB: {DiseaseDictionaryEntry.objects.count()}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing KCD data: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
