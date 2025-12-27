from django.shortcuts import render, redirect, get_object_or_404
import json
from encaixe.models import Pedido, PedidoItem, Molde, MoldePeca, PedidoConfig, Material, Cor, Produto, ProdutoPecaCor

from encaixe.services.material_calculator import get_material_requirements_for_orders

def order_list(request):
    orders = Pedido.objects.all().order_by('-data')
    return render(request, 'encaixe/order_list.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Pedido, id=order_id)
    return render(request, 'encaixe/order_detail.html', {'order': order})

def create_order(request):
    if request.method == 'POST':
        client_name = request.POST.get('client')
        qty = int(request.POST.get('qty'))
        
        # New: Product selection (replaces Variant)
        produto_id = request.POST.get('produto')
        
        if produto_id:
            # AUTO-CONFIG FLOW
            produto = Produto.objects.get(id=produto_id)
            pedido = Pedido.objects.create(cliente=client_name)
            
            # Create Item linked to Product
            item = PedidoItem.objects.create(
                pedido=pedido, 
                molde=produto.molde, 
                produto=produto,
                quantidade=qty
            )
            
            # Auto-Populate Configs
            # 1. Get Standard Colors from Product
            product_rules = {
                rule.molde_peca_id: rule.cor
                for rule in ProdutoPecaCor.objects.filter(produto=produto)
            }
            
            # 2. Populate Order Config (Material = Generic, Color = Product Color)
            pieces = MoldePeca.objects.filter(molde=produto.molde)
            for piece in pieces:
                tecido = piece.material_padrao
                cor = product_rules.get(piece.id)
                
                if tecido and cor:
                    PedidoConfig.objects.create(
                        pedido_item=item,
                        molde_peca=piece,
                        material=tecido,
                        cor=cor
                    )
            
            # Skip manual config, go straight to visualize
            return redirect('visualize_order', item_id=item.id)
            
        else:
            # LEGACY FLOW (Manual Config)
            molde_id = request.POST.get('molde')
            pedido = Pedido.objects.create(cliente=client_name)
            molde = Molde.objects.get(id=molde_id)
            item = PedidoItem.objects.create(pedido=pedido, molde=molde, quantidade=qty)
            return redirect('configure_order_item', item_id=item.id)

    moldes = Molde.objects.all()
    produtos = Produto.objects.all()
    return render(request, 'encaixe/create_order.html', {'moldes': moldes, 'produtos': produtos})

def configure_order_item(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id)
    pieces = MoldePeca.objects.filter(molde=item.molde)
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
    return render(request, 'encaixe/configure_order.html', context)

def visualize_order(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id)
    configs = PedidoConfig.objects.filter(pedido_item=item)
    
    # Reconstruct logical "pieces" for the visualization from DB
    pieces_data = []
    
    for config in configs:
        peca = config.molde_peca
        geom = peca.geometria_json
        
        # Override name with DB name to be safe
        geom['name'] = peca.nome_original
        # Inject color HEX code
        
        pieces_data.append({
            'name': peca.nome_original,
            'qty': peca.qtd_padrao,
            'geom': geom,
            'color': config.cor.hex_code,
            'color_name': config.cor.nome,
            'fabric_name': config.material.nome,
            'fabric_width': config.material.largura_padrao_mm
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
    return render(request, 'encaixe/visualize.html', context)

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
    return render(request, 'encaixe/order_materials.html', {'order': order, 'report': report_list})
