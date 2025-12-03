from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.Showcase.models import (
    Media,
    Project,
    ProjectMedia,
    Competition,
    CompetitionMedia,
)


class Command(BaseCommand):
    help = "Seed demo data for Showcase (media, projects, competitions)."

    def handle(self, *args, **options):
        User = get_user_model()

        # pick any existing user, or create a demo one
        user = User.objects.order_by("id").first()
        if not user:
            user = User.objects.create_user(
                username="demo.admin",
                password="demo1234",
                institutional_id="DEMO-001",
                email="demo@example.com",
                role_type="admin",
            )
            self.stdout.write(self.style.SUCCESS(f"Created demo user {user.username}"))
        else:
            self.stdout.write(
                self.style.WARNING(f"Using existing user {user.username} (id={user.id})")
            )

        # these filenames must exist in frontend assets/images
        image_files = ["1.jpg", "2.jpg", "3.jpg"]
        medias: list[Media] = []

        for idx, fname in enumerate(image_files, start=1):
            m, _ = Media.objects.get_or_create(
                media_type="image",
                path_or_url=fname,  # ShowcaseAdmin uses basename and loads from assets/images
                defaults={
                    "mime_type": "image/jpeg",
                    "caption": f"Sample {idx}",
                    "alt_text": f"Sample image {idx}",
                    "uploaded_by": user,
                },
            )
            medias.append(m)

        self.stdout.write(self.style.SUCCESS(f"Have {len(medias)} media rows"))

        p1, _ = Project.objects.get_or_create(
            title="Smart Bin",
            defaults={
                "description": "An IoT waste-segregation bin.",
                "submitted_by": user,
                "status": "approved",
                "is_public": True,
                "category": "capstone",
                "context": "hardware",
                "external_url": "https://example.com/smart-bin",
                "author_display": "Alice, Bob",
            },
        )

        p2, _ = Project.objects.get_or_create(
            title="Study Buddy",
            defaults={
                "description": "A student helper app.",
                "submitted_by": user,
                "status": "approved",
                "is_public": True,
                "category": "software",
                "context": "mobile",
                "external_url": "https://example.com/study-buddy",
                "author_display": "Carol",
            },
        )

        if medias:
            ProjectMedia.objects.get_or_create(
                project=p1,
                media=medias[0],
                defaults={"is_primary": True, "sort_order": 1},
            )
        if len(medias) > 1:
            ProjectMedia.objects.get_or_create(
                project=p1,
                media=medias[1],
                defaults={"is_primary": False, "sort_order": 2},
            )
        if len(medias) > 2:
            ProjectMedia.objects.get_or_create(
                project=p2,
                media=medias[2],
                defaults={"is_primary": True, "sort_order": 1},
            )

        comp, _ = Competition.objects.get_or_create(
            name="TechFest 2025",
            defaults={
                "organizer": "CMU",
                "start_date": "2025-03-01",
                "end_date": "2025-03-03",
                "description": "Annual technology fair.",
                "event_type": "expo",
                "external_url": "https://example.com/techfest",
                "submitted_by": user,
                "status": "published",
                "is_public": True,
            },
        )

        if medias:
            CompetitionMedia.objects.get_or_create(
                competition=comp,
                media=medias[0],
                defaults={"is_primary": True, "sort_order": 1},
            )

        self.stdout.write(self.style.SUCCESS("Showcase demo data seeded."))
