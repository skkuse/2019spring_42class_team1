from django.db import models


class Video(models.Model):
    class Status:
        UPLOADED = 'UPLOADED'
        DETECTING = 'DETECTING'
        DETECTED = 'DETECTED'
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20)
    filename = models.TextField()
    url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class DetectedScene(models.Model):
    class DetectionCause:
        NUDITY = 'NUDITY'
        SWEAR = 'SWEAR'    # 욕설
    id = models.AutoField(primary_key=True)
    src_video = models.ForeignKey(Video, on_delete=models.CASCADE)
    start_millis = models.BigIntegerField()
    end_millis = models.BigIntegerField()
    cause = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
