from celery import shared_task

from .sync import sync_sources


@shared_task(name="apps.robot.tasks.consultar_fontes_drive")
def consultar_fontes_drive():
    return sync_sources()
