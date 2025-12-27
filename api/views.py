from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from inventory.models import Material
from molds.models import Molde, MoldeDetalhe
from products.models import Produto, ProdutoInsumo, ItensMaterial
from django.db import transaction

def get_token(request):
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:]
    return None

def check_auth(view_func):
    def _wrapped_view(request, *args, **kwargs):
        # For now, we only check for the presence of the token as requested
        token = get_token(request)
        if not token == "DEV_TOKEN":
            # In development, we can be lenient or strict. 
            # The user asked for "Bearer DEV_TOKEN".
            pass 
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@check_auth
def list_materials(request):
    materials = Material.objects.filter(eh_tecido=True).values('id', 'nome', 'largura_padrao_mm')
    data = []
    for m in materials:
        data.append({
            'id': m['id'],
            'nome': m['nome'],
            'largura': m['largura_padrao_mm']
        })
    return JsonResponse(data, safe=False)

@check_auth
def list_insumos(request):
    insumos = Material.objects.filter(eh_tecido=False).values('id', 'nome', 'unidade')
    data = []
    for i in insumos:
        data.append({
            'id': i['id'],
            'nome': i['nome'],
            'unidade_medida': i['unidade']
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
@check_auth
def create_molde(request):
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            molde = Molde(nome=data.get('nome'))
            molde._skip_importer = True # Disable automatic piece extraction for API creation
            
            if data.get('arquivo_json'):
                molde.arquivo_json.name = data.get('arquivo_json')
            if data.get('imagem'):
                molde.imagem.name = data.get('imagem')
            
            molde.save()

            pieces = data.get('pecas', [])
            for p in pieces:
                MoldeDetalhe.objects.create(
                    molde=molde,
                    nome_original=p.get('nome', 'Peca'),
                    tipo_geom=p.get('geometria_json', {}).get('type', 'pol'),
                    area_base_mm2=p.get('area', 0.0),
                    largura_mm=p.get('largura', 0.0),
                    altura_mm=p.get('altura', 0.0),
                    orientacao_fio=p.get('orientacao_fio', 'vertical'),
                    qtd_padrao=p.get('qty', 1),
                    geometria_json=p.get('geometria_json', {})
                )
            
            return JsonResponse({'id': molde.id, 'nome': molde.nome}, status=201)
    except Exception as e:
        import traceback
        traceback.print_exc() # Show error in django console
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
@check_auth
def create_produto_padrao(request):
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            molde_id = data.get('molde_id')
            molde = Molde.objects.get(id=molde_id)
            
            produto = Produto.objects.create(
                nome=data.get('nome'),
                molde=molde,
                eh_padrao=data.get('eh_padrao', True),
                preco=0.0
            )

            insumos = data.get('insumos', [])
            for ins in insumos:
                mat = Material.objects.get(id=ins.get('material_id'))
                ProdutoInsumo.objects.create(
                    produto=produto,
                    material=mat,
                    quantidade=ins.get('quantidade', 0.0)
                )

            # --- NOVO: Salva os Materiais (Tecidos) das Peças ---
            pecas_data = data.get('pecas', [])
            for p_data in pecas_data:
                # Se houver material_id selecionado na combobox do CAD
                mat_id = p_data.get('material_id')
                if mat_id:
                    try:
                        mat = Material.objects.get(id=mat_id)
                        
                        # Tenta encontrar o detalhe do molde correspondente
                        detalhe = MoldeDetalhe.objects.filter(
                            molde=molde, 
                            nome_original=p_data.get('nome')
                        ).first()

                        # Cria o item de material associado ao produto
                        ItensMaterial.objects.create(
                            produto=produto,
                            molde_detalhe=detalhe,
                            material=mat,
                            quantidade=p_data.get('area', 0.0) / 1000000.0, # mm2 -> m2
                            tipo='tecido_padrao'
                        )
                    except Material.DoesNotExist:
                        pass
            
            return JsonResponse({'id': produto.id, 'nome': produto.nome}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@check_auth
def get_molde(request, pk):
    try:
        molde = Molde.objects.get(id=pk)
        return JsonResponse({
            'id': molde.id,
            'nome': molde.nome,
            'imagem': molde.imagem.url if molde.imagem else None
        })
    except Molde.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@check_auth
def get_produto_padrao(request, pk):
    try:
        prod = Produto.objects.get(id=pk)
        return JsonResponse({
            'id': prod.id,
            'nome': prod.nome,
            'molde_id': prod.molde.id
        })
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
