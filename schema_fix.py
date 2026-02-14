from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Forces the missing unit_id column into property_invoice'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("Checking property_invoice schema...")
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM property_invoice LIKE 'unit_id'")
            result = cursor.fetchone()
            
            if not result:
                self.stdout.write("Column unit_id missing. Forcing creation...")
                # Note: We use BIGINT to match Django 5.x default primary key types
                cursor.execute("ALTER TABLE property_invoice ADD COLUMN unit_id BIGINT")
                cursor.execute("ALTER TABLE property_invoice ADD CONSTRAINT inv_unit_fk FOREIGN KEY (unit_id) REFERENCES property_unit(id)")
                self.stdout.write(self.style.SUCCESS("Successfully added unit_id column."))
            else:
                self.stdout.write(self.style.SUCCESS("Column unit_id already exists."))