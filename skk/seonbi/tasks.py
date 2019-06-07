from __future__ import absolute_import
from skk.celery import app
from seonbi.models import Video, DetectedScene
from seonbi.videos import upload_to_gcp, detect
import os
import ffmpeg


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


@app.task(name='blur_and_upload')
def blur_and_upload(video_id, src_path):
    video = Video.objects.get(id=video_id)
    scenes = DetectedScene.objects.filter(src_video=video).values()
    in_file = ffmpeg.input(src_path)
    for scene in scenes:
        in_file.overlay(
            in_file.crop(x=100, y=100, width=200, height=200).filter_('boxblur', luma_radius=10, luma_power=10),
            x=100,
            y=100,
            enable='between(t, 0, 5)'
        )
    in_file.output('./blur_%s' % src_path).run(overwrite_output=True)
