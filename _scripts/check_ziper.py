import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from encaixe.models import Material

def check_materials():
    # Buscando por algo que pareça ziper
    materiais = Material.objects.filter(nome__icontains='ZIPER')
    print(f"Encontrados {materiais.count()} materiais com 'ZIPER':")
    for m in materiais:
        print(f" - ID: {m.id} | Nome: '{m.nome}' | Unidade: '{m.unidade}' | É Tecido: {m.eh_tecido}")

if __name__ == '__main__':
    check_materials()
