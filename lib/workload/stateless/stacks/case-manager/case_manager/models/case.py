from django.db import models

from case_manager.fields import OrcaBusIdField
from case_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from case_manager.models.case_data import CaseData
from case_manager.models.library import Library


class CaseManager(OrcaBusBaseManager):
    pass


class Case(OrcaBusBaseModel):

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='case')

    cref = models.CharField(max_length=255)  # Curation reference
    name = models.CharField(max_length=255) # Auto-assigned name
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=255) # predefined types or 'custom'

    compute_env = models.CharField(max_length=255)
    data_env = models.CharField(max_length=255)

    # relationships
    case_data = models.ForeignKey(CaseData, null=True, blank=True, on_delete=models.CASCADE())
    libraries = models.ManyToManyField(Library, through="LibraryAssociation")
    # state # ForeignKey relationship on State model

    objects = CaseManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, name: {self.name}"


    def get_all_states(self):
        # retrieve all states (DB records rather than a queryset)
        return list(self.states.all())  # TODO: ensure order by timestamp ?

    def get_latest_state(self):
        # retrieve all related states and get the latest one
        return self.states.order_by('-timestamp').first()


class LibraryAssociationManager(OrcaBusBaseManager):
    pass


class LibraryAssociation(OrcaBusBaseModel):
    orcabus_id = OrcaBusIdField(primary_key=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    association_date = models.DateTimeField()
    status = models.CharField(max_length=255)

    objects = LibraryAssociationManager()
