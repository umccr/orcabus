import json
import logging
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from libumccr import libjson
from libumccr.aws import libeb

from app.models import Subject, Sample, Library, Project, Contact, Individual
from app.models.library import Quality, LibraryType, Phenotype, WorkflowType, sanitize_library_coverage
from app.models.sample import Source
from app.models.utils import get_value_from_human_readable_label
from proc.service.utils import clean_model_history
from app.serializers import LibrarySerializer
from proc.aws.event.event import MetadataStateChangeEvent

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@transaction.atomic
def load_metadata_csv(df: pd.DataFrame, is_emit_eb_events: bool = True, user_id: str = None, reason: str = None):
    """
    Persist metadata records from a pandas dataframe into the db. No record deletion is performed in this method.

    Args:
        df (pd.DataFrame): The source of truth for the metadata in this particular year
        is_emit_eb_events: Emit event bridge events for update/create (only for library records for now)
        user_id: The user_id or email making this sync request
        reason: The reason for the update or insert request

    """
    # Event entries for the event bus
    event_bus_entries = list()

    # Used for statistics
    invalid_data = []
    stats = {
        "library": {
            "create_count": 0,
            "update_count": 0,
        },
        "sample": {
            "create_count": 0,
            "update_count": 0,

        },
        "subject": {
            "create_count": 0,
            "update_count": 0,
        },
        "individual": {
            "create_count": 0,
            "update_count": 0,
        },
        "project": {
            "create_count": 0,
            "update_count": 0,
        },
        "contact": {
            "create_count": 0,
            "update_count": 0,
        },
        'invalid_record_count': 0,
    }

    # this the where records are updated, inserted, linked based on library_id
    for record in df.to_dict('records'):
        try:
            # 1. update or create all data in the model from the given record

            # ------------------------------
            # Individual
            # ------------------------------
            idv = None
            individual_id = record.get('individual_id')
            idv_source = record.get('individual_id_source')

            if individual_id and idv_source:

                idv, is_idv_created, is_idv_updated = Individual.objects.update_or_create_if_needed(
                    search_key={
                        "individual_id": individual_id,
                        "source": idv_source
                    },
                    data={
                        "individual_id": individual_id,
                        "source": idv_source
                    }, user_id=user_id, change_reason=reason
                )
                if is_idv_created:
                    stats['individual']['create_count'] += 1
                if is_idv_updated:
                    stats['individual']['update_count'] += 1

            # ------------------------------
            # Subject
            # ------------------------------

            subject_id = record.get('subject_id')
            subject, is_sub_created, is_sub_updated = Subject.objects.update_or_create_if_needed(
                search_key={"subject_id": subject_id},
                data={
                    "subject_id": subject_id,
                }, user_id=user_id, change_reason=reason
            )

            if is_sub_created:
                stats['subject']['create_count'] += 1
            if is_sub_updated:
                stats['subject']['update_count'] += 1

            if idv:
                # link individual to external subject
                try:
                    subject.individual_set.get(orcabus_id=idv.orcabus_id)
                except ObjectDoesNotExist:
                    subject._change_reason = reason
                    subject.individual_set.add(idv)

                    # We update the stats when new idv is linked to sbj, only if this is not recorded as
                    # update/create in previous upsert method
                    if not is_sub_created and not is_sub_updated:
                        stats['subject']['update_count'] += 1

            # ------------------------------
            # Sample
            # ------------------------------
            sample = None
            sample_id = record.get('sample_id')
            if sample_id:
                sample, is_smp_created, is_smp_updated = Sample.objects.update_or_create_if_needed(
                    search_key={"sample_id": sample_id},
                    data={
                        "sample_id": sample_id,
                        "external_sample_id": record.get('external_sample_id'),
                        "source": get_value_from_human_readable_label(Source.choices, record.get('source')),
                    }, user_id=user_id, change_reason=reason
                )
                if is_smp_created:
                    stats['sample']['create_count'] += 1
                if is_smp_updated:
                    stats['sample']['update_count'] += 1

            # ------------------------------
            # Contact
            # ------------------------------
            contact = None
            contact_id = record.get('project_owner')

            if contact_id:
                contact, is_ctc_created, is_ctc_updated = Contact.objects.update_or_create_if_needed(
                    search_key={"contact_id": contact_id},
                    data={
                        "contact_id": contact_id,
                    }, user_id=user_id, change_reason=reason
                )
                if is_ctc_created:
                    stats['contact']['create_count'] += 1
                if is_ctc_updated:
                    stats['contact']['update_count'] += 1

            # ------------------------------
            # Project: Upsert project with contact as part of the project
            # ------------------------------
            project = None

            project_id = record.get('project_name')
            if project_id:
                project, is_prj_created, is_prj_updated = Project.objects.update_or_create_if_needed(
                    search_key={"project_id": project_id},
                    data={
                        "project_id": project_id,
                    }, user_id=user_id, change_reason=reason
                )
                if is_prj_created:
                    stats['project']['create_count'] += 1
                if is_prj_updated:
                    stats['project']['update_count'] += 1

                # link project to its contact of exist
                if contact:
                    try:
                        project.contact_set.get(orcabus_id=contact.orcabus_id)
                    except ObjectDoesNotExist:
                        project._change_reason = reason
                        project.contact_set.add(contact)

                        # We update the stats when new ctc is linked to prj, only if this is not recorded as
                        # update/create in previous upsert method
                        if not is_prj_created and not is_prj_updated:
                            stats['project']['update_count'] += 1

            # ------------------------------
            # Library: Upsert library record with related sample, subject, project
            # ------------------------------
            library, is_lib_created, is_lib_updated = Library.objects.update_or_create_if_needed(
                search_key={"library_id": record.get('library_id')},
                data={
                    'library_id': record.get('library_id'),
                    'phenotype': get_value_from_human_readable_label(Phenotype.choices, record.get('phenotype')),
                    'workflow': get_value_from_human_readable_label(WorkflowType.choices, record.get('workflow')),
                    'quality': get_value_from_human_readable_label(Quality.choices, record.get('quality')),
                    'type': get_value_from_human_readable_label(LibraryType.choices, record.get('type')),
                    'assay': record.get('assay'),
                    'coverage': sanitize_library_coverage(record.get('coverage')),
                    'override_cycles': record.get('override_cycles'),

                    # relationships
                    'sample_id': sample.orcabus_id,
                    'subject_id': subject.orcabus_id,
                }, user_id=user_id, change_reason=reason
            )

            lib_dict = LibrarySerializer(library).data
            if is_lib_created:
                stats['library']['create_count'] += 1
                event = MetadataStateChangeEvent(
                    action='CREATE',
                    model='LIBRARY',
                    ref_id=lib_dict.get('orcabus_id'),
                    data=lib_dict
                )
                event_bus_entries.append(event.get_put_event_entry())

            if is_lib_updated:
                stats['library']['update_count'] += 1

                event = MetadataStateChangeEvent(
                    action='UPDATE',
                    model='LIBRARY',
                    ref_id=lib_dict.get('orcabus_id'),
                    data=lib_dict,
                )
                event_bus_entries.append(event.get_put_event_entry())

            # link library to its project
            if project:
                try:
                    library.project_set.get(orcabus_id=project.orcabus_id)
                except ObjectDoesNotExist:
                    library._change_reason = reason
                    library.project_set.add(project)
                    # We update the stats when new project is linked to library, only if this is not recorded as
                    # update/create in previous upsert method
                    if not is_lib_created and not is_lib_updated:
                        stats['library']['update_count'] += 1

        except Exception as e:
            if any(record.values()):
                stats['invalid_record_count'] += 1
                invalid_data.append({
                    "reason": e,
                    "data": record
                })
            continue

    # clean up history for django-simple-history model if any
    # Only clean for the past 15 minutes as this is what the maximum lambda cutoff
    clean_model_history(minutes=15)

    if len(invalid_data) > 0:
        logger.warning(f"Invalid record: {invalid_data}")

    if len(event_bus_entries) > 0 and is_emit_eb_events:
        logger.info(f'Dispatch event bridge entries: {libjson.dumps(event_bus_entries)}')
        libeb.dispatch_events(event_bus_entries)

    logger.info(f"Processed LabMetadata: {json.dumps(stats)}")
    return stats


def download_csv_to_pandas(url: str) -> pd.DataFrame:
    """
    Download csv file from a given url and return it as a pandas dataframe
    """
    return pd.read_csv(url)


def drop_incomplete_csv_records(df: pd.DataFrame):
    """
    For custom csv, we are dropping records when found empty on any of these columns defined below.

    CSV header: subject_id, library_id
    """

    # The fields are sanitized to camel_case in the sanitize_lab_metadata_df
    df = df.drop(df[df.library_id.isnull()].index, errors='ignore')
    df = df.drop(df[df.subject_id.isnull()].index, errors='ignore')

    df = df.reset_index(drop=True)
    return df
