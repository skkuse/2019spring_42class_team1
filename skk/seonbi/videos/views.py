from django.core import serializers
from django.shortcuts import render
from seonbi.models import Video, DetectedScene


def index(request):
    return render(request, 'videos.html', {'videos': Video.objects.all()})


def detail(request, video_id):
    return render(request, 'video_detail.html', {'video_id': video_id})


def filter(request, video_id, filter_id):
    return render(request, 'filter_video.html', {'video_id': video_id, 'filter_id': filter_id})
