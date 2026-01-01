from celery import Celery, Signature
from celery.app.task import Task
from celery.local import class_property
from celery.result import AsyncResult
from celery.utils.objects import FallbackContext

classes = [Celery, Task, AsyncResult, Signature, FallbackContext, class_property]

for cls in classes:
    setattr(  # noqa: B010
        cls,
        "__class_getitem__",
        classmethod(lambda cls, *args, **kwargs: cls),
    )
