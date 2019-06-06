from __future__ import absolute_import
from skk.celery import app
from seonbi.models import Video
from seonbi.videos import upload_to_gcp, detect
import os


@app.task(name='upload_video_to_gcp')
def upload_video(video_id, src_path, gcp_path):
    video = Video.objects.get(id=video_id)
    try:
        video.url = upload_to_gcp(src_path, gcp_path)
        video.status = Video.Status.UPLOADED
        video.save()
    except:
        video.status = Video.Status.FAILED
        video.save()


@app.task(name='detect_scenes')
def detect_scenes(video_id, src_path):
    video = Video.objects.get(id=video_id)
    try:
        _ = detect(src_path, video)
    except:
        video.status = Video.Status.FAILED
        video.save()
