from __future__ import absolute_import
from skk.celery import app
from seonbi.models import Video, DetectedScene, FilteredResult
from seonbi.videos import upload_to_gcp, detect, delete_gcp_file, filter
import os
import ffmpeg
import datetime


@app.task(name='upload_and_detect')
def upload_and_detect(video_id, src_path, gcp_path):
    video = Video.objects.get(id=video_id)
    try:
        video.url = upload_to_gcp(src_path, gcp_path)
        video.status = Video.Status.UPLOADED
        video.save()
        _ = detect(src_path, video)
        os.remove(src_path)
    except Exception as ex:
        print(ex)
        video.status = Video.Status.FAILED
        video.save()


@app.task(name='delete_video')
def delete_video(url):
    delete_gcp_file(url)


@app.task(name='filter_and_upload')
def filter_and_upload(fr_id, scene_ids, removal=False):
    fr = FilteredResult.objects.get(id=fr_id)
    scenes = DetectedScene.objects.filter(id__in=scene_ids).values()
    try:
        filtered_path = filter(fr, scenes, removal)

        fr.status = FilteredResult.Status.UPLOADING
        fr.save()
        now = datetime.datetime.now()
        gcp_path = os.path.join(
            '%d-%d-%d' % (now.year, now.month, now.day), os.path.basename(filtered_path))
        url = upload_to_gcp(filtered_path, gcp_path)
        os.remove(filtered_path)

        fr.url = url
        fr.status = FilteredResult.Status.COMPLETE
        fr.save()
    except Exception as ex:
        print(ex)
        fr.status = FilteredResult.Status.FAILED
        fr.save()
