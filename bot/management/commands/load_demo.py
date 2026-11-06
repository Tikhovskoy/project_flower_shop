import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from bot.models import Bouquet, Composition


class Command(BaseCommand):
    help = (
        "Загружает демо-каталог: вымышленные букеты и композиции вместе с картинками. "
        "Заказов и консультаций в демо-данных нет."
    )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        demo_media = base_dir / "demo" / "media"
        fixture = base_dir / "fixtures" / "demo.json"

        for path in (demo_media, fixture):
            if not path.exists():
                raise CommandError(f"Не найдено: {path}")

        shutil.copytree(demo_media, settings.MEDIA_ROOT, dirs_exist_ok=True)
        call_command("loaddata", str(fixture), verbosity=0)

        self.stdout.write(
            self.style.SUCCESS(
                f"Демо загружено: букетов — {Bouquet.objects.count()}, "
                f"композиций — {Composition.objects.count()}."
            )
        )
