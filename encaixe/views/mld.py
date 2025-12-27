from django.http import JsonResponse, HttpResponse
from django.conf import settings
import os
from encaixe.utils import read_mld_file

# Default test file path
DEFAULT_MLD_PATH = os.path.join(settings.BASE_DIR, 'teste.mld')

def detalhe_projeto_view(request):
    """
    Returns JSON data from a .mld file.
    Accepts 'path' query parameter, defaults to DEFAULT_MLD_PATH.
    """
    caminho_arquivo = request.GET.get('path', DEFAULT_MLD_PATH)
    
    try:
        conteudo = read_mld_file(caminho_arquivo)
        # Retorna apenas os dados do projeto como JSON para o frontend
        return JsonResponse(conteudo['data'])
    except FileNotFoundError:
        return JsonResponse({'erro': 'Arquivo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=400)

def capa_projeto_view(request):
    """
    Returns the PNG thumbnail from a .mld file.
    Accepts 'path' query parameter, defaults to DEFAULT_MLD_PATH.
    """
    caminho_arquivo = request.GET.get('path', DEFAULT_MLD_PATH)
    
    try:
        conteudo = read_mld_file(caminho_arquivo)
        # Retorna a imagem (thumbnail) diretamente
        return HttpResponse(conteudo['thumbnail'], content_type="image/png")
    except FileNotFoundError:
        return HttpResponse(status=404)
    except Exception:
        return HttpResponse(status=400)
