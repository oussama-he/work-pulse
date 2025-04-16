from urllib.parse import urlparse

from django.db import models


class TimestampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimestampModel):
    class Meta:
        abstract = True


class Project(BaseModel):
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True, max_length=1000)
    description = models.TextField(default="")
    viewed = models.DateTimeField(null=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-viewed"]

    def __str__(self):
        return self.title

    @property
    def source(self):
        return urlparse(self.url).netloc
