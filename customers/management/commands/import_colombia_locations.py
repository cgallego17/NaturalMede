import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from customers.models import City, Country, Department


DEFAULT_JSON_PATH = (
    r"C:\Users\User\Documents\ncs3\NSC-INTERNATIONAL\data"
    r"\countries+states+cities.json"
)


class Command(BaseCommand):
    help = "Importa Colombia (departamentos y ciudades) desde countries+states+cities.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=DEFAULT_JSON_PATH,
            help="Ruta al archivo countries+states+cities.json",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No escribe en BD; solo muestra conteos.",
        )

    def handle(self, *args, **options):
        json_path = options["path"]
        dry_run = options["dry_run"]

        path = Path(json_path)
        if not path.exists():
            raise CommandError(f"No existe el archivo: {json_path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise CommandError(f"Error leyendo JSON: {exc}")

        country = next(
            (
                c
                for c in data
                if c.get("name") == "Colombia"
                or c.get("iso2") == "CO"
                or c.get("iso3") == "COL"
            ),
            None,
        )

        if not country:
            raise CommandError("No se encontró Colombia dentro del JSON")

        states = country.get("states") or []
        state_count = len(states)
        city_count = sum(len(s.get("cities") or []) for s in states)

        self.stdout.write(
            self.style.SUCCESS(
                f"Colombia detectado: {state_count} departamentos, {city_count} ciudades"
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("dry-run: no se escribió en BD"))
            return

        with transaction.atomic():
            country_obj, _ = Country.objects.get_or_create(
                external_id=int(country["id"]),
                defaults={
                    "name": country.get("name") or "Colombia",
                    "iso2": country.get("iso2"),
                    "iso3": country.get("iso3"),
                },
            )

            created_departments = 0
            created_cities = 0

            for state in states:
                dept_external_id = int(state["id"])
                dept_name = (state.get("name") or "").strip()
                dept_iso2 = state.get("iso2")

                dept, dept_created = Department.objects.get_or_create(
                    country=country_obj,
                    external_id=dept_external_id,
                    defaults={
                        "name": dept_name,
                        "iso2": dept_iso2,
                    },
                )

                if not dept.name and dept_name:
                    dept.name = dept_name
                    dept.save(update_fields=["name"])

                if dept_created:
                    created_departments += 1

                for city in state.get("cities") or []:
                    city_external_id = int(city["id"])
                    city_name = (city.get("name") or "").strip()

                    _, city_created = City.objects.get_or_create(
                        department=dept,
                        external_id=city_external_id,
                        defaults={
                            "name": city_name,
                        },
                    )
                    if city_created:
                        created_cities += 1

            self.stdout.write(
                self.style.SUCCESS(
                    "Import finalizado. "
                    f"Nuevos departamentos: {created_departments}. "
                    f"Nuevas ciudades: {created_cities}."
                )
            )
