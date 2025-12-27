import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings") # Adjust if project name is different
django.setup()

from molds.models import Molde, MoldePeca, MoldeMaterial
from molds.models import Molde, MoldePeca, MoldeMaterial
from encaixe.services.molde_importer import process_molde_json
from django.core.files import File

# Create a Dummy Molde
molde, _ = Molde.objects.get_or_create(nome="Test Import Molde")

# Point to the existing JSON
json_path = "MoldeInsumo.json"
with open(json_path, 'rb') as f:
    molde.arquivo_json.save("MoldeInsumo.json", File(f), save=True)

print(f"Molde ID: {molde.id} - JSON File: {molde.arquivo_json.path}")

# Run Importer
print("Running Importer...")
process_molde_json(molde)

# Verify Results
print("-" * 30)
print("VERIFYING INSUMOS (Accessories):")
insumos = MoldeMaterial.objects.filter(molde=molde)
for i in insumos:
    print(f" - {i.material.nome}: {i.quantidade} {i.material.unidade} (Tipo: {i.tipo})")

print("-" * 30)
print("VERIFYING PECAS (Pieces):")
pecas = MoldePeca.objects.filter(molde=molde)
for p in pecas:
    mat_nome = p.material_padrao.nome if p.material_padrao else "N/A"
    print(f" - {p.nome_original}: Qtd {p.qtd_padrao}, Material: {mat_nome}")
