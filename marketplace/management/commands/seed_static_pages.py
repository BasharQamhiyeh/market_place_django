from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Seed all static-page content (FAQ, Privacy Policy, Terms) "
        "in one shot. Safe to run on a fresh deployment."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help=(
                "Pass --replace to each sub-command, deactivating existing "
                "pages and recreating them from scratch."
            ),
        )

    def handle(self, *args, **options):
        replace = options["replace"]

        self.stdout.write(self.style.MIGRATE_HEADING("\n==> Seeding FAQ …"))
        call_command("seed_faq", verbosity=options["verbosity"])

        self.stdout.write(self.style.MIGRATE_HEADING("\n==> Seeding Privacy Policy …"))
        call_command(
            "seed_privacy_policy",
            replace=replace,
            verbosity=options["verbosity"],
        )

        self.stdout.write(self.style.MIGRATE_HEADING("\n==> Seeding Terms of Use …"))
        call_command(
            "seed_terms",
            replace=replace,
            verbosity=options["verbosity"],
        )

        self.stdout.write(self.style.SUCCESS(
            "\nAll static pages seeded successfully."
        ))
