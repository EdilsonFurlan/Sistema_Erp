from django.contrib import admin
from django.urls import path, include
from encaixe.views import legacy, home, mld

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home.index, name='home'),
    
    # Apps
    path('products/', include('products.urls')), # Namespacing helps but keeping flat for now to match existin logic
    path('sales/', include('sales.urls')),
    path('purchases/', include('purchases.urls')),
    path('production/', include('production.urls')),
    path('inventory/', include('inventory.urls')),
    path('molds/', include('molds.urls')),
    path('clients/', include('clients.urls')),

    # API REST (For CadMolde and external integrations)
    path('api/', include('api.urls')),

    # MLD Project Views
    path('project/detail/', mld.detalhe_projeto_view, name='project_detail'),
    path('project/cover/', mld.capa_projeto_view, name='project_cover'),

    # Legacy / Misc
    path('visualize/', legacy.visualize_encaixe, name='visualize_encaixe'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
