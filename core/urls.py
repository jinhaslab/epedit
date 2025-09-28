# /home/rag/papps/epedit/epedit_project/urls.py

from django.contrib import admin
from django.urls import path, include, re_path, reverse_lazy # re_path 임포트 확인
from django.conf import settings
from django.views.static import serve as static_serve # <-- serve 임포트 확인

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('records.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
   
]

urlpatterns += [
    re_path(r'^data/(?P<path>.*)$', static_serve, { # <-- Nginx rewrite 후 받는 경로: /data/...
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^static/(?P<path>.*)$', static_serve, { # <-- Nginx rewrite 후 받는 경로: /static/...
        'document_root': settings.STATIC_ROOT,
    }),
]