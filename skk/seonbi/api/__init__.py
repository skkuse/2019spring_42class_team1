from django.http import JsonResponse
from seonbi.models import Video, DetectedScene


def get_video_detail(request, video_id):
    video = Video.objects.get(id = video_id)
    detected_scenes = DetectedScene.objects.filter(src_video = video).values()
    return JsonResponse({
        'video': {
            'status': video.status,
            'filename': video.filename,
            'url': video.url,
            'created_at': video.created_at
        },
        'detected_scenes': [
            {'start_millis': scene['start_millis'], 'end_millis': scene['end_millis'], 'cause': scene['cause']} for scene in detected_scenes
        ]
    })
