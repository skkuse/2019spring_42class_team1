from __future__ import absolute_import
from skk.celery import app
from seonbi.models import Video
from seonbi.videos import upload_to_gcp, detect
import os


@app.task(name='upload_and_detect')
def upload_and_detect(video_id, src_path, gcp_path):
    video = Video.objects.get(id=video_id)
    try:
        video.url = upload_to_gcp(src_path, gcp_path)
        video.status = Video.Status.UPLOADED
        video.save()
        _ = detect(src_path, video)
    except:
        video.status = Video.Status.FAILED
        video.save()
