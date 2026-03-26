from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import *

app_name = 'main'

urlpatterns = [
    # Това е вашият основен изглед за началната страница (където ще бъде Vue.js)
    path('', index, name='index'),

    # Това е новият API endpoint за обработката на изображенията
    path('api/process/', ImageBatchProcessView.as_view(), name='api-process'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

