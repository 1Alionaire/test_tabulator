from .models import PlmSample, PlmSampleWeight, PlmProject, SampleMethod, SampleASbestosType
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import django.utils
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
import math
import random

PLM_ENTRY_REQUIRED_ON_CREATE = {
    'homo_area', 'client_sample', 'lab_sample', 'description',
    'location', 'method', 'row_number', 'layer',
}

PLM_WEIGHT_REQUIRED_ON_CREATE = {'client_sample', 'w_crucible', 'w_crucible_with_sample',
                                 'w_sample', 'w_sample_ashed', 'org',
                                 'w_petri', 'w_petri_with_sample', 'residue', 'caco3' }

class PLMSamplesDataEntryManager():
    def __init__(self, plm_project, input_data, type):
        self.plm_project = plm_project
        self.input_data = input_data
        self.type = type
        if self.type == 'update':
            self.data_to_update = input_data.get('updated', [])
            self.data_to_create = input_data.get('created', [])

        self.error = None

    def validate_whole_object(self):
        if self.type == 'update':
            error = self.validate_updated_data()
            if error is not None:
                return error

            error = self.validate_created_data()
            if error is not None:
                return error

        elif self.type == 'replace_all':
            for record in self.input_data:
                missing = PLM_ENTRY_REQUIRED_ON_CREATE - set(record.keys())
                if missing:
                    return {'error': f"missing required fields"}

    def validate_updated_data(self):
        if self.data_to_update:
            for record in self.data_to_update:
                for field_name, value in record.items():
                    if field_name == 'lab_sample':
                        if value is not None:
                            if len(str(value)) < 6:
                                return {'error': 'changed lab_id is too short'} 
                        else:
                            return {'error': 'lab_id is required'} 

    def validate_created_data(self):
        if self.data_to_create:
            for record in self.data_to_create:
                if not record.get('lab_sample'):
                    return {'error': 'lab_sample is required'} 
                
                missing = PLM_ENTRY_REQUIRED_ON_CREATE - set(record.keys())
                if missing:
                    return {'error': f"missing required fields {record.get('lab_id')} : {missing}"}
                
            lab_id_list = [element.get('lab_sample') for element in self.data_to_create]
            if PlmSample.objects.filter(plm_project=self.plm_project, lab_sample__in=lab_id_list).exists():
                return {'error': 'lab_id already exist'} 

    def table_update_processing(self) -> dict:
        if self.type == 'update':
            result = {'status': 'ok'}
            with transaction.atomic():
                if self.data_to_update:
                    result['updated'] = self._update_data()
                if self.data_to_create:
                    result['created'] = self._create_data()

        elif self.type == 'replace_all':
            samples = []
            with transaction.atomic():
                PlmSample.objects.filter(plm_project=self.plm_project).delete()
                for data in self.input_data:
                    data['row_number'] = int(data['row_number'])
                    samples.append(PlmSample(plm_project=self.plm_project, **data))

                for sample in samples:
                    sample.full_clean()
                    sample.save()

            result = {'status': 'ok'}

        return result

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]
        
        touched_fields = set()

        samples_to_update = {sample.id : sample for sample in 
                                            PlmSample.objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            sample = samples_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field != 'id':
                    setattr(sample, name_field, value)
                    touched_fields.add(name_field)

            sample.time_update = django.utils.timezone.now()

        return PlmSample.objects.bulk_update(
                        samples_to_update.values(), sorted(touched_fields | {'time_update'})
                    )

    def _create_data(self):
        samples = []
        for data in self.data_to_create:
            samples.append(PlmSample(plm_project=self.plm_project, **data))

        for sample in samples:
            sample.full_clean()
            sample.save()

        return len(samples)

class PLMSamplesWeightManager():
    def __init__(self, plm_project, input_data):
        self.plm_project = plm_project
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])

    def validate_whole_object(self):
        work_data = self.data_to_update + self.data_to_create
        for record in work_data:
            field_names = set(record.keys())
            missing = PLM_WEIGHT_REQUIRED_ON_CREATE - field_names
            if missing:
                return {'error': f"missing required fields "}

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            if self.data_to_update:
                result['updated'] = self._update_data()
            if self.data_to_create:
                result['created'] = self._create_data()
            if self.data_to_delete:
                result['deleted'] = self._delete_data()

        return result

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]
        touched_fields = set()

        samples_to_update = {sample.id : sample for sample in 
                            PlmSampleWeight.objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            sample = samples_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field != 'id':
                    setattr(sample, name_field, value)
                    touched_fields.add(name_field)

            sample.time_update = django.utils.timezone.now()

        updated = PlmSampleWeight.objects.bulk_update(
                        samples_to_update.values(), sorted(touched_fields | {'time_update'})
                    )

        client_weight_samples = [data['client_sample'] for data in work_data if data['client_sample'] is not None and data['client_sample'] != '']
        print(client_weight_samples)
        # Taking all samples for update
        samples_to_update = {sample.client_sample : sample for sample in  
                            PlmSample.objects.select_for_update().filter(plm_project=self.plm_project, client_sample__in=client_weight_samples)}
        
        for data in work_data:
            weight_client_sample = data['client_sample']
            try:
                weight_record = PlmSampleWeight.objects.get(plm_project=self.plm_project, client_sample=weight_client_sample) # take weight with client id
                sample_to_update = samples_to_update[weight_client_sample] #take sample with client id
                if sample_to_update:
                    setattr(sample_to_update, 'weight', weight_record) # Filling new value
            except:
                pass
            setattr(sample_to_update, 'time_update', django.utils.timezone.now())  # new time update

        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'time_update'}))

        return updated

    def _create_data(self):
        weights = []
        for data in self.data_to_create:
            weights.append(PlmSampleWeight(plm_project=self.plm_project, **data))

        for weight in weights:
            weight.full_clean()
            weight.save()

        # Taking all samples for update
        samples_to_update = {sample.client_sample : sample for sample in  
                            PlmSample.objects.select_for_update().filter(plm_project=self.plm_project)}

        for data in self.data_to_create:
            weight_record = PlmSampleWeight.objects.get(client_sample=data['client_sample']) # take weight with client id
            sample_to_update = samples_to_update[data['client_sample']] #take sample with client id
            setattr(sample_to_update, 'weight', weight_record) # Filling new value 
            sample_to_update.time_update = django.utils.timezone.now()  # new time update

        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'time_update'}))

        return len(weights)

    def _delete_data(self):
        PlmSampleWeight.objects.filter(pk__in=self.data_to_delete).delete()
        return len(self.data_to_delete)

def generate_qc_sample(input_project_id):
    max_row_number = PlmSample.objects.aggregate(Max('row_number'))['row_number__max']
    select_project = PlmProject.objects.get(pk=input_project_id)
    created_plm_qc_amount = 0
    created_nob_qc_amount = 0
    created_tem_qc_amount = 0

    samples = []

    if max_row_number < 1000:
        max_row_number = 1000
    
    if PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1981).exists():
        samples_to_copy = PlmSample.original_samples.filter(plm_project=select_project, 
                                                            method=SampleMethod.Sample1981).exclude(asb_type=SampleASbestosType.NotAnayzed)
        print(samples_to_copy)
        
        amount_rep_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1981).count() / 15)
        amount_dup_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1981).count() / 50)

        

        for rep in range(amount_rep_samples):
            random_sample_to_copy = random.choice(samples_to_copy)
            samples.append(PlmSample(plm_project=select_project, 
                                        row_number=max_row_number,
                                        client_sample=('R' + random_sample_to_copy.client_sample),
                                        lab_sample=('R' + random_sample_to_copy.lab_sample),
                                        is_qc_sample = True, 
                                        asb_type = random_sample_to_copy.asb_type,
                                        homo_area= random_sample_to_copy.homo_area,
                                        layer= random_sample_to_copy.layer,
                                        description= random_sample_to_copy.description,
                                        location= random_sample_to_copy.location,
                                        method= random_sample_to_copy.method,
                                        color= random_sample_to_copy.color,
                                        analysis_temperature= random_sample_to_copy.analysis_temperature,
                                        texture= random_sample_to_copy.texture,
                                        morphology= random_sample_to_copy.morphology,
                                        ri_alpha_oil= random_sample_to_copy.ri_alpha_oil,
                                        ri_delta_oil= random_sample_to_copy.ri_delta_oil,
                                        sign_of_elongation= random_sample_to_copy.sign_of_elongation,
                                        extinction_angle= random_sample_to_copy.extinction_angle,
                                        pleochroism_color= random_sample_to_copy.pleochroism_color,
                                        birefringence= random_sample_to_copy.birefringence,
                                        other_fiber= random_sample_to_copy.other_fiber,
                                        other_fiber_property= random_sample_to_copy.other_fiber_property,
                                        other_fiber_percent= random_sample_to_copy.other_fiber_percent))
            max_row_number += 1

        for dup in range(amount_dup_samples):
            random_sample_to_copy = random.choice(samples_to_copy)
            samples.append(PlmSample(plm_project = select_project, 
                                    row_number = max_row_number,
                                    client_sample = ('D' + random_sample_to_copy.client_sample),
                                    lab_sample = ('D' + random_sample_to_copy.lab_sample),
                                    is_qc_sample = True, 
                                    asb_type = random_sample_to_copy.asb_type,
                                    homo_area = random_sample_to_copy.homo_area,
                                    layer = random_sample_to_copy.layer,
                                    description = random_sample_to_copy.description,
                                    location = random_sample_to_copy.location,
                                    method = random_sample_to_copy.method,
                                    color = random_sample_to_copy.color,
                                    analysis_temperature= random_sample_to_copy.analysis_temperature,
                                    texture= random_sample_to_copy.texture,
                                    morphology= random_sample_to_copy.morphology,
                                    ri_alpha_oil= random_sample_to_copy.ri_alpha_oil,
                                    ri_delta_oil= random_sample_to_copy.ri_delta_oil,
                                    sign_of_elongation= random_sample_to_copy.sign_of_elongation,
                                    extinction_angle= random_sample_to_copy.extinction_angle,
                                    pleochroism_color= random_sample_to_copy.pleochroism_color,
                                    birefringence= random_sample_to_copy.birefringence,
                                    other_fiber= random_sample_to_copy.other_fiber,
                                    other_fiber_property= random_sample_to_copy.other_fiber_property,
                                    other_fiber_percent= random_sample_to_copy.other_fiber_percent))
            max_row_number += 1

    if PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1986).exists():
        samples_to_copy = PlmSample.original_samples.filter(plm_project=select_project, 
                                                            method=SampleMethod.Sample1986).exclude(asb_type=SampleASbestosType.NotAnayzed)
        print(samples_to_copy)
        
        amount_rep_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1986).count() / 15)
        amount_dup_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1986).count() / 50)

        for rep in range(amount_rep_samples):
            random_sample_to_copy = random.choice(samples_to_copy)
            copied_weight_item = None
            if samples_to_copy[0].weight is not None:

                copied_weight_item = PlmSampleWeight(plm_project=select_project, 
                                                    client_sample=('R' + random_sample_to_copy.weight.client_sample),
                                                    w_crucible=random_sample_to_copy.weight.w_crucible,
                                                    w_crucible_with_sample=random_sample_to_copy.weight.w_crucible_with_sample,
                                                    w_sample=random_sample_to_copy.weight.w_sample,
                                                    w_sample_ashed=random_sample_to_copy.weight.w_sample_ashed,
                                                    org=random_sample_to_copy.weight.org, 
                                                    w_petri=random_sample_to_copy.weight.w_petri,
                                                    w_petri_with_sample=random_sample_to_copy.weight.w_petri_with_sample,
                                                    residue=random_sample_to_copy.weight.residue,
                                                    caco3=random_sample_to_copy.weight.caco3)
                copied_weight_item.full_clean()
                copied_weight_item.save()

            samples.append(PlmSample(plm_project=select_project, 
                                        row_number=max_row_number,
                                        client_sample=('R' + random_sample_to_copy.client_sample),
                                        lab_sample=('R' + random_sample_to_copy.lab_sample),
                                        is_qc_sample = True, 
                                        asb_type = random_sample_to_copy.asb_type,
                                        homo_area= random_sample_to_copy.homo_area,
                                        layer= random_sample_to_copy.layer,
                                        description= random_sample_to_copy.description,
                                        location= random_sample_to_copy.location,
                                        method= random_sample_to_copy.method,
                                        color= random_sample_to_copy.color,
                                        weight=copied_weight_item,
                                        analysis_temperature= random_sample_to_copy.analysis_temperature,
                                        texture= random_sample_to_copy.texture,
                                        morphology= random_sample_to_copy.morphology,
                                        ri_alpha_oil= random_sample_to_copy.ri_alpha_oil,
                                        ri_delta_oil= random_sample_to_copy.ri_delta_oil,
                                        sign_of_elongation= random_sample_to_copy.sign_of_elongation,
                                        extinction_angle= random_sample_to_copy.extinction_angle,
                                        pleochroism_color= random_sample_to_copy.pleochroism_color,
                                        birefringence= random_sample_to_copy.birefringence,
                                        other_fiber= random_sample_to_copy.other_fiber,
                                        other_fiber_property= random_sample_to_copy.other_fiber_property,
                                        other_fiber_percent= random_sample_to_copy.other_fiber_percent, 
                                        tem_microscope_alignment=random_sample_to_copy.tem_microscope_alignment, 
                                        tem_eccentricity_adjusted=random_sample_to_copy.tem_eccentricity_adjusted, 
                                        tem_grid_pre_acceptability=random_sample_to_copy.tem_grid_pre_acceptability, 
                                        ))
            max_row_number += 1

    
    for sample in samples:
        sample.full_clean()
        sample.save()

    return len(samples)
