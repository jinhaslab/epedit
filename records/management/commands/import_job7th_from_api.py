import requests
from django.core.management.base import BaseCommand
from dictionaries.models import JobCodeOccupation


class Command(BaseCommand):
    help = 'Import job data from job7thsearch API hierarchical endpoint'

    def handle(self, *args, **options):
        api_url = "https://sehnr.org/ohsearch/job7thsearch/api/hierarchical/"

        self.stdout.write(f"Fetching data from {api_url}...")

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            self.stdout.write(self.style.SUCCESS(f"Successfully fetched hierarchical data"))

            imported_count = 0
            updated_count = 0

            # Recursively process all categories
            def process_category(category):
                nonlocal imported_count, updated_count

                # Save current category
                if 'id' in category and 'name' in category:
                    job_code = str(category['id']).strip()
                    occupation = str(category['name']).strip()

                    try:
                        obj, created = JobCodeOccupation.objects.update_or_create(
                            job_code=job_code,
                            defaults={'occupation': occupation}
                        )
                        if created:
                            imported_count += 1
                            self.stdout.write(f"  Created: {job_code} - {occupation}")
                        else:
                            updated_count += 1
                            self.stdout.write(f"  Updated: {job_code} - {occupation}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Error saving {job_code}: {e}"))

                # Process children recursively
                if 'children' in category and category['children']:
                    for child in category['children']:
                        process_category(child)

            # Process all top-level categories
            if 'categories' in data:
                for category in data['categories']:
                    process_category(category)

            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Import completed!\n'
                f'   - New records: {imported_count}\n'
                f'   - Updated records: {updated_count}\n'
                f'   - Total: {imported_count + updated_count}'
            ))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Error fetching data from API: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing data: {e}'))
