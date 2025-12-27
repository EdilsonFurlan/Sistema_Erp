from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, EntradaEstoque, Cor, EstoqueMaterial
from .forms import MaterialForm, EntradaEstoqueForm, CorForm, AddColorToMaterialForm
from django.contrib import messages

# --- MATERIAIS ---

def material_list(request):
    materials = Material.objects.all().order_by('nome')
    
    # Calculate totals
    total_value = sum(m.estoque_atual * float(m.preco_medio) for m in materials)
    
    context = {
        'materials': materials,
        'total_value': total_value
    }
    return render(request, 'inventory/material_list.html', context)

def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material criado com sucesso!')
            return redirect('material_list')
    else:
        form = MaterialForm()
    
    return render(request, 'inventory/material_create.html', {'form': form, 'title': 'Novo Material'})

def material_edit(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material atualizado com sucesso!')
            return redirect('material_list')
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'inventory/material_create.html', {'form': form, 'title': f'Editar {material.nome}'})

def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        try:
            material.delete()
            messages.success(request, 'Material excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir: {e}')
            
        return redirect('material_list')
        
    return render(request, 'inventory/material_confirm_delete.html', {'material': material})



def material_add_color(request, pk):
    material = get_object_or_404(Material, pk=pk)
    
    if request.method == 'POST':
        form = AddColorToMaterialForm(request.POST)
        if form.is_valid():
            cor = form.cleaned_data['cor']
            # Create EstoqueMaterial if it doesn't exist
            obj, created = EstoqueMaterial.objects.get_or_create(
                material=material,
                cor=cor,
                defaults={'quantidade': 0}
            )
            if created:
                messages.success(request, f'Cor {cor.nome} adicionada ao {material.nome} com sucesso!')
            else:
                messages.info(request, f'A cor {cor.nome} já estava adicionada ao {material.nome}.')
            return redirect('material_list')
    else:
        form = AddColorToMaterialForm()
    
    return render(request, 'inventory/material_add_color.html', {
        'form': form, 
        'material': material,
        'title': f'Adicionar Cor ao {material.nome}'
    })

# --- MOVIMENTAÇÕES ---

def stock_entry_create(request):
    if request.method == 'POST':
        form = EntradaEstoqueForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('movement_list')
    else:
        form = EntradaEstoqueForm()

    return render(request, 'inventory/stock_entry.html', {'form': form})

def movement_list(request):
    movements = EntradaEstoque.objects.all().order_by('-data')
    return render(request, 'inventory/movement_list.html', {'movements': movements})

# --- CORES ---

def color_list(request):
    colors = Cor.objects.all().order_by('nome')
    return render(request, 'inventory/color_list.html', {'colors': colors})

def color_create(request):
    if request.method == 'POST':
        form = CorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cor adicionada com sucesso!')
            return redirect('color_list')
    else:
        form = CorForm()
    
    return render(request, 'inventory/color_create.html', {'form': form, 'title': 'Nova Cor'})
