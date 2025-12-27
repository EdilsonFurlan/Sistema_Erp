import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import Material

def check_units():
    print("Checking Material Units...")
    mats = Material.objects.filter(eh_tecido=True)
    for m in mats:
        print(f"ID: {m.id} | Nome: {m.nome} | Unidade: '{m.unidade}' (Type: {type(m.unidade)})")

if __name__ == '__main__':
    check_units()
