from django.core.management.base import BaseCommand

from traffic.models import Intersection

SEED = [
    ("Ibn Gabirol / Arlozorov", "Tel Aviv", 32.087800, 34.781900),
    ("Begin / Kaplan", "Tel Aviv", 32.073500, 34.788600),
    ("Dizengoff / King George", "Tel Aviv", 32.077900, 34.774300),
    ("Allenby / Rothschild", "Tel Aviv", 32.064000, 34.772900),
    ("Jaffa Road / King George", "Jerusalem", 31.782500, 35.217800),
    ("Herzl / HaNassi", "Haifa", 32.809300, 34.991800),
]


class Command(BaseCommand):
    help = "Create a few demo intersections (idempotent)."

    def handle(self, *args, **options):
        created = 0
        for name, city, lat, lng in SEED:
            _, was_created = Intersection.objects.get_or_create(
                name=name, city=city, defaults={"latitude": lat, "longitude": lng}
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"{created} intersection(s) created."))
