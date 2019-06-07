from django.urls import path
from seonbi.api import get_video_detail

app_name = 'api'

urlpatterns = [
    path('videos/<int:video_id>/', get_video_detail),
]
