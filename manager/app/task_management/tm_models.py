# -*- coding: iso-8859-1 -*-
from mongoengine import fields
from datetime import datetime


class ActiveTask(fields.Document):
    """
    Contiene metadatos de una descarga iniciada de una fuente de datos.
    """

    task_source = fields.StringField(null=True)
    task_type = fields.StringField(null=True)
    started_at = fields.DateTimeField(default=datetime.now())
    finished_at = fields.DateTimeField(null=True)
    current_progress = fields.IntField(null=True, default=0)
    full_progress = fields.IntField(null=True, default=0)
    finished = fields.BooleanField(null=True, default=False)

    meta = {
        'collection': 'Active_Tasks',
        'index_cls': False,
        'indexes': [
            {'fields': ['task_type'], 'unique': False}
        ]
    }
