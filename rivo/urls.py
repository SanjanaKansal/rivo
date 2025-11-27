from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/chat/', include('chat.urls')),
    path('api/v1/account/', include('account.urls')),
    path('api/v1/clients/', include('client.urls')),
    path('dashboard/', include('dashboard.urls')),
]
