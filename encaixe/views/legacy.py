from django.shortcuts import render
from django.conf import settings
import os
import json

def visualize_encaixe(request):
    json_path = os.path.join(settings.BASE_DIR, 'teste.json')
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    order_data = json.dumps(data)
    
    fabric_width = 1500 # Default width in mm
    if request.GET.get('width'):
        fabric_width = int(request.GET.get('width'))

    return render(request, 'encaixe/visualize.html', {
        'json_data': order_data,
        'fabric_width': fabric_width,
        'quantity': 1
    })
