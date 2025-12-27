from django.shortcuts import render, redirect, get_object_or_404
import json
from sales.models import Pedido, PedidoItem, PedidoConfig
from products.models import Produto
from molds.models import Molde, MoldeDetalhe
from inventory.models import Material, Cor
from .forms import PedidoForm, PedidoItemFormSet

from clients.models import Cliente
from sales.services.material_calculator import get_material_requirements_for_orders

def order_list(request):
    orders = Pedido.objects.all().order_by('-data').prefetch_related('itens')
    return render(request, 'sales/order_list.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Pedido, id=order_id)
    return render(request, 'sales/order_detail.html', {'order': order})

def create_order(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        qty = int(request.POST.get('qty'))
        
        # Selection: Produto (Final Product with Colors)
        produto_id = request.POST.get('produto')
        
        # Fetch Client Object
        client_obj = get_object_or_404(Cliente, id=client_id)
        
        if produto_id:
            # AUTO-CONFIG FLOW
            produto_sku = Produto.objects.get(id=produto_id)
            produto_ref = produto_sku.parent
            
            pedido = Pedido.objects.create(
                cliente=client_obj.nome, # Backward compatibility
                cliente_cadastro=client_obj
            )
            
            # Create Item linked to SKU
            item = PedidoItem.objects.create(
                pedido=pedido, 
                molde=produto_ref.molde, 
                produto=produto_sku,
                quantidade=qty
            )
            
            # Auto-Populate Configs?
            # Model GAP: No link between Pieces and ItensMaterial.
            # We skip auto-config for now. User must configure manually.
            
            return redirect('visualize_order', item_id=item.id)
            
        else:
            # LEGACY FLOW (Manual Config) - Still supported via Molde direct selection?
            # If user selects Molde directly (no Product/Color preset).
            molde_id = request.POST.get('molde')
            if molde_id:
                pedido = Pedido.objects.create(
                    cliente=client_obj.nome,
                    cliente_cadastro=client_obj
                )
                molde = Molde.objects.get(id=molde_id)
                item = PedidoItem.objects.create(pedido=pedido, molde=molde, quantidade=qty)
                return redirect('configure_order_item', item_id=item.id)
            else:
                 return redirect('order_list') # Fallback

    moldes = Molde.objects.all()
    produtos = Produto.objects.filter(parent__isnull=False).select_related('parent') 
    clientes = Cliente.objects.all().order_by('nome')
    return render(request, 'sales/create_order.html', {'moldes': moldes, 'produtos': produtos, 'clientes': clientes})


def configure_order_item(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id)
    # MoldePeca -> MoldeDetalhe
    pieces = MoldeDetalhe.objects.filter(molde=item.molde)
    tecidos = Material.objects.filter(eh_tecido=True)
    cores = Cor.objects.all()

    if request.method == 'POST':
        # Save configurations
        for piece in pieces:
            tecido_id = request.POST.get(f'tecido_{piece.id}')
            cor_id = request.POST.get(f'cor_{piece.id}')
            
            if tecido_id and cor_id:
                PedidoConfig.objects.update_or_create(
                    pedido_item=item,
                    molde_peca=piece,
                    defaults={
                        'material_id': tecido_id,
                        'cor_id': cor_id
                    }
                )
        return redirect('visualize_order', item_id=item.id)

    # Load existing configs
    existing_configs_dict = {
        conf.molde_peca_id: conf 
        for conf in PedidoConfig.objects.filter(pedido_item=item)
    }
    
    # Prepare list for template
    pieces_with_config = []
    for p in pieces:
        pieces_with_config.append({
            'piece': p,
            'config': existing_configs_dict.get(p.id)
        })

    context = {
        'item': item,
        'pieces_data': pieces_with_config, # New list
        'tecidos': tecidos,
        'cores': cores,
    }
    return render(request, 'sales/configure_order.html', context)

def visualize_order(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id)
    configs = PedidoConfig.objects.filter(pedido_item=item)
    
    # Reconstruct logical "pieces" for the visualization from DB
    pieces_data = []

    if configs.exists():
        # SCENARIO A: Custom Configuration (PedidoConfig)
        for config in configs:
            peca = config.molde_peca
            geom = peca.geometria_json
            
            # Override name with DB name to be safe
            geom['name'] = peca.nome_original
            
            pieces_data.append({
                'name': peca.nome_original,
                'qty': peca.qtd_padrao,
                'geom': geom,
                'color': config.cor.hex_code if config.cor else '#cccccc',
                'color_name': config.cor.nome if config.cor else 'Padrão',
                'fabric_name': config.material.nome if config.material else 'Indefinido',
                'fabric_width': config.material.largura_padrao_mm if config.material else 1500
            })
            
    elif item.produto:
        # SCENARIO B: Standard SKU (Product)
        sku = item.produto
        molde = item.molde or sku.molde
        
        # 1. Map Piece -> Material/Color from ItensMaterial
        # We need to find which material applies to which piece.
        # ItensMaterial has a 'molde_detalhe' FK.
        sku_materials_map = {}
        for im in sku.itens_material.all():
            if im.molde_detalhe:
                sku_materials_map[im.molde_detalhe.id] = im
        
        # 2. Iterate all pieces of the mold
        for peca in molde.detalhes.all():
            # Find material for this piece
            im = sku_materials_map.get(peca.id)
            
            material = im.material if im else None
            cor = im.cor if im else None
            
            # If no specific mapping, maybe use a default or skip?
            # For visualization, better to show it in grey than hide it.
            
            geom = peca.geometria_json
            geom['name'] = peca.nome_original
            
            pieces_data.append({
                'name': peca.nome_original,
                'qty': peca.qtd_padrao,
                'geom': geom,
                'color': cor.hex_code if cor else '#e2e8f0',
                'color_name': cor.nome if cor else 'Padrão',
                'fabric_name': material.nome if material else 'Tecido Base',
                'fabric_width': material.largura_padrao_mm if material and material.largura_padrao_mm else 1500
            })

    # Prepare data structure expected by visualize.html (similar to teste.json)
    json_data = {'pieces': pieces_data}
    
    # Use the first configured fabric width as default
    default_width = 1500
    if configs.exists():
        default_width = configs.first().material.largura_padrao_mm

    fabric_width = int(request.GET.get('width', default_width))

    context = {
        'json_data': json.dumps(json_data),
        'quantity': item.quantidade,
        'fabric_width': fabric_width,
        'order_item': item
    }
    return render(request, 'sales/visualize.html', context)

def order_materials(request, order_id):
    order = get_object_or_404(Pedido, id=order_id)
    report_data = get_material_requirements_for_orders([order])
    
    # Format for template
    report_list = []
    for (material, cor), data in report_data.items():
        report_list.append({
            'material': material,
            'cor': cor,
            'qtd': data['qtd'],
            'unidade': material.unidade,
        })
    
    report_list.sort(key=lambda x: x['material'].nome)
    return render(request, 'sales/order_materials.html', {'order': order, 'report': report_list})

def order_upsert(request, pk=None):
    if pk:
        order = get_object_or_404(Pedido, pk=pk)
        title = f"Editar Pedido #{order.id}"
    else:
        order = None
        title = "Novo Pedido"
    
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=order)
        formset = PedidoItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            created_order = form.save()
            
            # Formset save commit=False to populate Molde and calculate total
            items = formset.save(commit=False)
            total_pedido = 0
            for item in items:
                item.pedido = created_order
                if item.produto:
                    # Auto-populate Molde from Product Reference
                    item.molde = item.produto.parent.molde
                
                # Force subtotal calculation
                if item.preco_unitario and item.quantidade:
                    item.subtotal = item.preco_unitario * item.quantidade
                
                item.save()
                total_pedido += item.subtotal
            
            # Save deleted instances and subtract from total if they were already saved
            for obj in formset.deleted_objects:
                if obj.pk:
                    obj.delete()
            
            # Update order total
            created_order.valor_total = total_pedido
            created_order.save()
            
            if 'save_continue' in request.POST:
                 return redirect('sales_order_update', pk=created_order.pk)
            return redirect('order_list')
    else:
        form = PedidoForm(instance=order)
        formset = PedidoItemFormSet(instance=order)
    
    return render(request, 'sales/order_form.html', {
        'form': form, 
        'formset': formset,
        'order': order,
        'title': title
    })

def add_item_row(request):
    """
    Optional: HTMX helper to render a single row.
    Currently bypassing this in favor of client-side empty_form cloning 
    for better formset index handling without complex server state.
    """
def release_item(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id)
    # Check if configured? (Optional validation)
    if item.configuracoes.exists() or item.produto:
         item.status = 'LIBERADO_PRODUCAO'
         item.save()
    return redirect('order_detail', order_id=item.pedido.id)
