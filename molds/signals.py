from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Molde
from encaixe.services.molde_importer import process_molde_json
import os

@receiver(post_save, sender=Molde)
def trigger_molde_import(sender, instance, created, **kwargs):
    if getattr(instance, '_skip_importer', False):
        return
    
    if instance.arquivo_json:
        try:
            # We call the importer service. 
            # Note: process_molde_json handles both .mld binary and legacy JSON.
            # It also handles clearing existing pieces if needed (though current impl appends/updates might duplicate if not careful).
            # Let's inspect process_molde_json again to be sure about duplication.
            # For now, we trust the importer service to do its job.
            process_molde_json(instance)
        except Exception as e:
            # Log error but don't crash the save transaction if possible?
            # Or crash to let user know import failed?
            # Printing for now as per project pattern.
            print(f"Error auto-importing pieces for Molde {instance.nome}: {e}")
