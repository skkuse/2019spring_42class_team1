from django.urls import path
from seonbi.api import video_detail, filter_detail

app_name = 'api'

urlpatterns = [
    path('videos/<int:video_id>/', video_detail),
    path('videos/<int:video_id>/filter/<int:filter_id>', filter_detail)
]
