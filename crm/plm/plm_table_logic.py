from .models import PlmSample, PlmSampleWeight, PlmProject, SampleMethod, SampleASbestosType
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import django.utils
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
import math
import random
from utils.utils import generate_weight_item
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from tem.models import TEMGridQCRecord

PLM_ENTRY_REQUIRED_ON_CREATE = {
    'homo_area', 'client_sample', 'lab_sample', 'description',
    'location', 'method', 'row_number', 'layer',
}

PLM_WEIGHT_REQUIRED_ON_CREATE = {'client_sample', 'w_crucible', 'w_crucible_with_sample',
                                 'w_sample', 'w_sample_ashed', 'org',
                                 'w_petri', 'w_petri_with_sample', 'residue', 'caco3' }


def copy_weight_item(plm_project, sample_to_copy, prefix):
    if sample_to_copy.weight is not None:
        copied_weight = PlmSampleWeight(plm_project=plm_project, 
                                            client_sample=(prefix + sample_to_copy.weight.client_sample),
                                            w_crucible=sample_to_copy.weight.w_crucible,
                                            w_crucible_with_sample=sample_to_copy.weight.w_crucible_with_sample,
                                            w_sample=sample_to_copy.weight.w_sample,
                                            w_sample_ashed=sample_to_copy.weight.w_sample_ashed,
                                            org=sample_to_copy.weight.org, 
                                            w_petri=sample_to_copy.weight.w_petri,
                                            w_petri_with_sample=sample_to_copy.weight.w_petri_with_sample,
                                            residue=sample_to_copy.weight.residue,
                                            caco3=sample_to_copy.weight.caco3)
        copied_weight.full_clean()
        copied_weight.save()
        return copied_weight
    else:
        return None

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

            self._update_plm_samples()

        return result

    def _update_plm_samples(self):
        PlmSample.objects.filter(plm_project=self.plm_project).exclude(method=SampleMethod.Sample1981).update(weight=None)

        samples_to_update = {sample.client_sample : sample for sample in  
                                    PlmSample.objects.select_for_update().filter(plm_project=self.plm_project).exclude(method=SampleMethod.Sample1981)}

        for client_id, sample_object in samples_to_update.items():
            weight_record = PlmSampleWeight.objects.filter(plm_project=self.plm_project, client_sample=client_id).first()
            if weight_record:
                setattr(sample_object, 'weight', weight_record) # Filling new value
                setattr(sample_object, 'time_update', django.utils.timezone.now())  # new time update
                
        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'time_update'}))


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

def generate_qc_sample(inp_project, copy_of_sample, copy_of_weight, max_row_number, prefix, is_nob_qb, is_tem_qc):
    sample = PlmSample(plm_project=inp_project, 
                        row_number=max_row_number,
                        client_sample=(prefix + copy_of_sample.client_sample),
                        lab_sample=(prefix + copy_of_sample.lab_sample),
                        weight=copy_of_weight,
                        is_qc_sample = is_nob_qb, 
                        is_tem_qc_sample = is_tem_qc, 
                        asb_type = copy_of_sample.asb_type,
                        homo_area= copy_of_sample.homo_area,
                        layer= copy_of_sample.layer,
                        description= copy_of_sample.description,
                        location= copy_of_sample.location,
                        method= copy_of_sample.method,
                        color= copy_of_sample.color,
                        analysis_temperature= copy_of_sample.analysis_temperature,
                        texture= copy_of_sample.texture,
                        morphology= copy_of_sample.morphology,
                        ri_alpha_oil= copy_of_sample.ri_alpha_oil,
                        ri_delta_oil= copy_of_sample.ri_delta_oil,
                        sign_of_elongation= copy_of_sample.sign_of_elongation,
                        extinction_angle= copy_of_sample.extinction_angle,
                        pleochroism_color= copy_of_sample.pleochroism_color,
                        birefringence= copy_of_sample.birefringence,
                        other_fiber= copy_of_sample.other_fiber,
                        other_fiber_property= copy_of_sample.other_fiber_property,
                        other_fiber_percent= copy_of_sample.other_fiber_percent,
                        tem_microscope_alignment=copy_of_sample.tem_microscope_alignment, 
                        tem_eccentricity_adjusted=copy_of_sample.tem_eccentricity_adjusted, 
                        tem_grid_pre_acceptability=copy_of_sample.tem_grid_pre_acceptability, 
                        tem_grid_box=copy_of_sample.tem_grid_box,
                        tem_grid_box_id_1=copy_of_sample.tem_grid_box_id_1,
                        tem_grid_box_id_2=copy_of_sample.tem_grid_box_id_2,
                        tem_na_or_ps=copy_of_sample.tem_na_or_ps,
                        is_blank=copy_of_sample.is_blank)
    sample.full_clean()
    sample.save()

    return sample

def generate_plm_qc_sample(max_row_number, select_project):
    samples_to_copy = PlmSample.original_samples.filter(plm_project=select_project, 
                                                            method=SampleMethod.Sample1981).exclude(asb_type=SampleASbestosType.NotAnalyzed)
        
    amount_rep_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1981).count() / 15)
    amount_dup_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1981).count() / 50)

    for _ in range(amount_rep_samples):
        random_sample_to_copy = random.choice(samples_to_copy)
        sample = generate_qc_sample(inp_project=select_project, 
                           copy_of_sample=random_sample_to_copy, 
                           copy_of_weight=None, 
                           max_row_number=max_row_number, 
                           prefix='R', 
                           is_nob_qb=True, 
                           is_tem_qc=False)

        max_row_number += 1

    for _ in range(amount_dup_samples):
        random_sample_to_copy = random.choice(samples_to_copy)
        sample = generate_qc_sample(inp_project=select_project, 
                                   copy_of_sample=random_sample_to_copy, 
                                   copy_of_weight=None, 
                                   max_row_number=max_row_number, 
                                   prefix='D', 
                                   is_nob_qb=True, 
                                   is_tem_qc=False)
        max_row_number += 1

    return max_row_number

def generate_nob_qc_sample(max_row_number, select_project):
    samples_to_copy = PlmSample.original_samples.filter(plm_project=select_project, 
                                                                method=SampleMethod.Sample1986).exclude(asb_type=SampleASbestosType.NotAnalyzed)
    amount_rep_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1986).count() / 15)
    amount_dup_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1986).count() / 50)

    for _ in range(amount_rep_samples):
        random_sample_to_copy = random.choice(samples_to_copy)
        copied_weight_item = copy_weight_item(plm_project=select_project,
                                              sample_to_copy=random_sample_to_copy,
                                              prefix='R')

        sample = generate_qc_sample(inp_project=select_project, 
                            copy_of_sample=random_sample_to_copy, 
                            copy_of_weight=copied_weight_item, 
                            max_row_number=max_row_number, 
                            prefix='R', 
                            is_nob_qb=True, 
                            is_tem_qc=False)
        
        max_row_number += 1

    for _ in range(amount_dup_samples):
        random_sample_to_copy = random.choice(samples_to_copy)

        if samples_to_copy[0].weight is not None:
            input_range = (float(random_sample_to_copy.weight.residue -10), float(random_sample_to_copy.weight.residue + 10))
        
        generated_weight_info = generate_weight_item(RESIDUE_RANGE=input_range)

        copied_weight_item = PlmSampleWeight(plm_project=select_project, 
                                            client_sample=('D' + random_sample_to_copy.weight.client_sample), **generated_weight_info)

        copied_weight_item.full_clean()
        copied_weight_item.save()

        sample = generate_qc_sample(inp_project=select_project, 
                            copy_of_sample=random_sample_to_copy, 
                            copy_of_weight=copied_weight_item, 
                            max_row_number=max_row_number, 
                            prefix='D', 
                            is_nob_qb=True, 
                            is_tem_qc=False)

        max_row_number += 1

    return max_row_number

def generate_tem_qc_sample(max_row_number, select_project):
    samples_to_copy = PlmSample.original_samples.filter(plm_project=select_project, method__in=[SampleMethod.Sample1984, 
                                                                                                SampleMethod.Sample1986, 
                                                                                                SampleMethod.Sample1994]).exclude(Q(asb_type=SampleASbestosType.NotAnalyzed) | Q(tem_na_or_ps='PS'))
                
    amount_rep_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method__in=[SampleMethod.Sample1984, 
                                                                                                            SampleMethod.Sample1986, 
                                                                                                            SampleMethod.Sample1994]).exclude(Q(asb_type=SampleASbestosType.NotAnalyzed) | Q(tem_na_or_ps='PS')).count() / 15)
    
    amount_dup_samples = math.ceil(PlmSample.original_samples.filter(plm_project=select_project, method__in=[SampleMethod.Sample1984, 
                                                                                                            SampleMethod.Sample1986, 
                                                                                                            SampleMethod.Sample1994]).exclude(Q(asb_type=SampleASbestosType.NotAnalyzed) | Q(tem_na_or_ps='PS')).count() / 50)

    for _ in range(amount_rep_samples):
        random_sample_to_copy = random.choice(samples_to_copy)
        copied_weight_item = copy_weight_item(plm_project=select_project, 
                                              sample_to_copy=random_sample_to_copy,
                                              prefix='R')

        sample = generate_qc_sample(inp_project=select_project, 
                            copy_of_sample=random_sample_to_copy, 
                            copy_of_weight=copied_weight_item, 
                            max_row_number=max_row_number, 
                            prefix='R', 
                            is_nob_qb=False, 
                            is_tem_qc=True)


        tem_grid_book_record = TEMGridQCRecord.objects.filter(filled=False).order_by("position").first() #take the lowest non-filled record

        if tem_grid_book_record is not None:
            tem_grid_book_record.plm_tem_project = select_project
            tem_grid_book_record.plm_tem_sample = sample
            tem_grid_book_record.filled = True
            tem_grid_book_record.save(update_fields=["plm_tem_project", "plm_tem_sample", "filled"])

        sample.tem_grid_box = tem_grid_book_record.grid_box
        sample.tem_grid_box_id_1 = tem_grid_book_record.grid_id_1
        sample.tem_grid_box_id_2 = tem_grid_book_record.grid_id_2
        sample.full_clean()
        sample.save(update_fields=["tem_grid_box", "tem_grid_box_id_1", "tem_grid_box_id_2"])
        
        max_row_number += 1

    for _ in range(amount_dup_samples):
        random_sample_to_copy = random.choice(samples_to_copy)
        copied_weight_item = copy_weight_item(plm_project=select_project,
                                              sample_to_copy=random_sample_to_copy,
                                              prefix='D')

        sample = generate_qc_sample(inp_project=select_project, 
                            copy_of_sample=random_sample_to_copy, 
                            copy_of_weight=copied_weight_item, 
                            max_row_number=max_row_number, 
                            prefix='D', 
                            is_nob_qb=False, 
                            is_tem_qc=True)

        tem_grid_book_record = TEMGridQCRecord.objects.filter(filled=False).order_by("position").first() #take the lowest non-filled record

        if tem_grid_book_record is not None:
            tem_grid_book_record.plm_tem_project = select_project
            tem_grid_book_record.plm_tem_sample = sample
            tem_grid_book_record.filled = True
            tem_grid_book_record.save(update_fields=["plm_tem_project", "plm_tem_sample", "filled"])

        sample.tem_grid_box = tem_grid_book_record.grid_box
        sample.tem_grid_box_id_1 = tem_grid_book_record.grid_id_1
        sample.tem_grid_box_id_2 = tem_grid_book_record.grid_id_2
        sample.full_clean()
        sample.save(update_fields=["tem_grid_box", "tem_grid_box_id_1", "tem_grid_box_id_2"])
        
        max_row_number += 1

    return max_row_number
    

def generate_qc_entry_process(input_project_id):
    max_row_number = PlmSample.objects.aggregate(Max('row_number'))['row_number__max']
    select_project = PlmProject.objects.get(pk=input_project_id)

    if max_row_number < 1000:
        max_row_number = 1000
    else:
        max_row_number += 1

    max_row_number_before = max_row_number
    
    if PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1981).exists():
        max_row_number = generate_plm_qc_sample(max_row_number, select_project)
    
    if PlmSample.original_samples.filter(plm_project=select_project, method=SampleMethod.Sample1986).exists():
        max_row_number = generate_nob_qc_sample(max_row_number, select_project)

    if PlmSample.original_samples.filter(plm_project=select_project, method__in=[SampleMethod.Sample1984, 
                                                                                 SampleMethod.Sample1986, 
                                                                                 SampleMethod.Sample1994]).exclude(tem_na_or_ps='PS').exists():
        max_row_number = generate_tem_qc_sample(max_row_number, select_project)
    
    return max_row_number_before - max_row_number

def validate_plm_project_for_report(plm_project):
    errors = []
    if plm_project.analyst is None:
        errors.append('No analyst') 
    if plm_project.date_collect is None:
        errors.append('No date collected') 
    if plm_project.date_analyze is None:
        errors.append('No date analysis')
    if plm_project.date_report is None:
        errors.append('No date report')
    return errors