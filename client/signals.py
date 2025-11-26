# client/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Client, ClientStageHistory


@receiver(pre_save, sender=Client)
def track_stage_change(sender, instance, **kwargs):
    """Auto-track stage changes"""
    if not instance.pk:
        return

    try:
        old_instance = Client.objects.get(pk=instance.pk)

        if old_instance.current_stage != instance.current_stage:
            ClientStageHistory.objects.create(
                client=instance,
                from_stage=old_instance.current_stage,
                to_stage=instance.current_stage,
                changed_by=None,
                remarks=f'Stage changed: {old_instance.current_stage} → {instance.current_stage}'
            )
    except Client.DoesNotExist:
        pass