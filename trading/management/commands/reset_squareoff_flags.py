from django.core.management.base import BaseCommand
from trading.models import SquareOffRule
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resets the triggered_today flag for all active SquareOffRules.'

    def handle(self, *args, **options):
        # Only reset rules that were active and triggered today.
        updated_count = SquareOffRule.objects.filter(active=True, triggered_today=True).update(triggered_today=False)
        self.stdout.write(self.style.SUCCESS(f'Successfully reset triggered_today for {updated_count} rules.'))
        logger.info(f'Daily reset: {updated_count} SquareOffRules had their triggered_today flag reset.')
