from django.db import models

# Create your models here.
from django.db import models


class Topology(models.Model):
    description = models.TextField(default="none", verbose_name="Description")
    name = models.TextField(default="noname", verbose_name="name")
    json = models.TextField(verbose_name="json")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(verbose_name="modified", auto_now=True)

    class Meta:
        verbose_name = 'Topology'
        verbose_name_plural = 'topologies'
