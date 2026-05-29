from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Card, CardStat


@receiver(post_save, sender=Card)
def create_card_stat(sender, instance, created, **kwargs):
    if created:
        CardStat.objects.create(card=instance)