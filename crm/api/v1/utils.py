from rest_framework.generics import get_object_or_404
from pcm.models import PcmProject
from plm.models import PlmProject

def get_active_project(id, type):
    if type == "pcm":
        return get_object_or_404(PcmProject.objects.select_related('project', 'analyst'),
                                 pk=id, project__deleted=False)

    if type == "plm":
        return get_object_or_404(PlmProject.objects.select_related('project', 'analyst'),
                                 pk=id, project__deleted=False)

class VersionConflictError(Exception):
    def __init__(self, message="Someone already update data. Please reload page"):
        super().__init__(message)

def check_versions(entities, records):
    conflicted = sorted(r["id"] for r in records if entities[r["id"]].version != r["version"])
    if conflicted:
        raise VersionConflictError()