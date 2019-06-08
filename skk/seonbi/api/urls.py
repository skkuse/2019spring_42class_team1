from django.urls import path
from seonbi.api import video_detail

app_name = 'api'

urlpatterns = [
    path('videos/<int:video_id>/', video_detail),
]
