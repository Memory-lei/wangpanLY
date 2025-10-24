"""
URL configuration for wangpanLY project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # 将 login/ 路由转发到 app 应用的 urls.py
    path("",views.login,name="login" ),
    # path('login_check', views.login_check,name="login_check"),

    path('containers/', views.containers),#显示容器界面
    path('objects/<data2>/', views.objects),#显示对象界面
    path('index/main1/<container_name>/', views.create_container),  # 添加容器路由
    path('main4/<container_name>/<object_name>/', views.delete_object),  # 删除文件路由
    path('hmz/main5/<container_name>/', views.delete_container),  # 与前端删除按钮的href对应
]
