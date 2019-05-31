from django.db import models


class Video(models.Model):
    id = models.AutoField(primary_key=True)
    filename = models.TextField()
    url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Censor(models.Model):
    id = models.AutoField(primary_key=True)
    # 검열이 필욜한 장면과 검열된 부분의 시간이 다를 수 있다.
    scene_from = models.BigIntegerField
    scene_to = models.BigIntegerField
    censor_from = models.BigIntegerField
    censor_to = models.BigIntegerField
    src_video = models.ForeignKey(Video, on_delete=models.CASCADE)
    cause = models.CharField(max_length=20)
