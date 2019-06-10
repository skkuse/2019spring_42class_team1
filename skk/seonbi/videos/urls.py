from django.urls import path
import seonbi.videos.views as views


app_name = 'videos'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:video_id>/', views.detail, name='detail'),
    path('<int:video_id>/filter/<int:filter_id>', views.filter, name='filter')
]
