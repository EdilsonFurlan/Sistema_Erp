from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cliente
from .forms import ClienteForm

def client_list(request):
    clientes = Cliente.objects.all().order_by('nome')
    return render(request, 'clients/client_list.html', {'clientes': clientes})

def client_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso!')
            return redirect('client_list')
    else:
        form = ClienteForm()
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Novo Cliente'})

def client_update(request, client_id):
    cliente = get_object_or_404(Cliente, id=client_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso!')
            return redirect('client_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Editar Cliente'})

def client_delete(request, client_id):
    cliente = get_object_or_404(Cliente, id=client_id)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente excluído com sucesso.')
        return redirect('client_list')
    return render(request, 'clients/client_confirm_delete.html', {'cliente': cliente})
