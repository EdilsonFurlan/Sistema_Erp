import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from molds.models import Molde, MoldePeca
from django.core.files import File

def test_signal():
    print("Testing Molde Signal Integration...")
    
    # Clean up previous test data if exists
    Molde.objects.filter(nome="Test Signal Molde").delete()
    
    # Path to existing test file
    mld_path = "teste.mld"
    if not os.path.exists(mld_path):
        print(f"Error: {mld_path} not found.")
        return

    # Create a new Molde
    molde = Molde(nome="Test Signal Molde")
    
    # Open the file and save it to the model. 
    # This calling .save() on the file field which triggers the model .save(), which triggers the signal.
    with open(mld_path, 'rb') as f:
        print("Saving Molde with .mld file...")
        molde.arquivo_json.save('teste_signal.mld', File(f), save=True)
    
    # Check if pieces were created
    pieces_count = MoldePeca.objects.filter(molde=molde).count()
    print(f"Molde saved. ID: {molde.id}")
    print(f"MoldePeca count: {pieces_count}")
    
    if pieces_count > 0:
        print("SUCCESS: Signal triggered and pieces created.")
        # Optional: Print names
        for p in MoldePeca.objects.filter(molde=molde):
            print(f" - Created Piece: {p.nome_original} ({p.tipo_geom})")
    else:
        print("FAILURE: No pieces created. Signal might not have fired or import failed.")

if __name__ == "__main__":
    test_signal()
