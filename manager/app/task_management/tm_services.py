# -*- coding: iso-8859-1 -*-
import json
from datetime import datetime
from manager.app.task_management import tm_models


def is_task_free(task_source, task_type):
    """
    Comprueba si un tipo de tarea está disponible

    Args:
        task_source (str): Fuente de datos.
        task_type (str): Tipo de tarea.

    Returns (bool):
        True si no existe un tracker para ese tipo de tarea, False si existe.
    """

    if tm_models.ActiveTask.objects(task_source=task_source, task_type=task_type).first():
        return False
    else:
        return True


def get_active_tasks():
    """
    Busca todos los trackers activos.

    Returns (list):
        Una lista con todos los trackers activos si hay.
    """

    tasks = list()

    for item in tm_models.ActiveTask.objects():
        tasks.append(json.loads(item.to_json()))

    return tasks


def start_task_tracker(task_source, task_type):
    """
    Crea un nuevo tracker para una tarea.

    Args:
        task_source (str): Colección de BD en la cual se realizara la actualizacion/ingesta de datos.
        task_type (str): Tarea de la que se hace el seguimiento.
        query_parameters (dict): Los parámetros pasados a la tarea.

    Returns (str):
        ID del tracker.
    """

    tracker = tm_models.ActiveTask(
        task_source=task_source,
        task_type=task_type,
        finished=False,
        current_progress=0,
        full_progress=0,
    )

    tracker.save()

    return str(tracker.id)


def update_progress(tracker_id, current_progress, full_progress):
    """
    Actualiza el progreso de una tarea.

    Args:
        tracker_id (str): ID del tracker la tarea.
        current_progress (int): Número de tareas completadas.
        full_progress (int): Número de tareas totales.
    """

    if tracker_id:
        tracker = find_tracker(tracker_id)

        if tracker:
            tracker.current_progress = current_progress
            tracker.full_progress = full_progress

            tracker.save()


def stop_tracker(tracker_id):
    """
    Detiene un tracker.

    Args:
        tracker_id (str): ID del tracker que se va a detener.
    """

    tracker = find_tracker(tracker_id)
    tracker.delete()


def finish_tracker(tracker_id):
    """
    Marca un tracker como completo.

    Args:
        tracker_id (str): ID del tracker que se va a completar.
    """

    tracker = find_tracker(tracker_id)
    tracker.finished = True
    tracker.finished_at = datetime.now()

    tracker.save()


def find_tracker(tracker_id):
    """
    Busca un objeto tracker a partir de una ID.

    Args:
        tracker_id (str): ID del tracker a buscar.

    Returns (ct_models.ActiveTask):
        El objeto que trackea el progreso.
    """

    tracker = tm_models.ActiveTask.objects(id=tracker_id).first()

    return tracker
