from core import models


class AuditModelMixin(models.BaseTimestampModel,
                      models.BaseTrackingModel):
    """
    Mixin that provides created_by, created, modified_by, modified fields

    Includes
        - BaseTimestampModel
        - BaseTrackingModel
    """

    class Meta:
        abstract = True
