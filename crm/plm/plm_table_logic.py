from .models import PlmSample, PlmSampleWeight, PlmProject, SampleMethod, SampleASbestosType
from django.db import transaction
import django.utils
from django.db.models import Max
import math
import random
from utils.utils import generate_weight_item
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from qc.models import PlmQCReplicateDuplicateItem, PlmTypeAnalysisSample, PlmTypeQCSample
from django.core import serializers
import json
from tem.models import TEMGridRecord

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

def generate_qc_sample(inp_project, copy_of_sample, copy_of_weight, max_row_number, prefix, is_nob_qb, is_tem_qc):
    sample = PlmSample(plm_project=inp_project, 
                        row_number=max_row_number,
                        client_sample=(prefix + copy_of_sample.client_sample),
                        lab_sample=(prefix + copy_of_sample.lab_sample),
                        weight=copy_of_weight,
                        is_qc_sample = is_nob_qb, 
                        tem_is_qc_sample = is_tem_qc,
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


        tem_grid_book_record = TEMGridRecord.objects.filter(filled=False, qc=True).order_by("position").first() #take the lowest non-filled record

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

        tem_grid_book_record = TEMGridRecord.objects.filter(filled=False, qc=True).order_by("position").first() #take the lowest non-filled record

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
    select_project = PlmProject.objects.get(pk=input_project_id)
    max_row_number = PlmSample.objects.filter(plm_project=input_project_id).aggregate(Max('row_number'))['row_number__max']

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
    
    return max_row_number - max_row_number_before



def complete_qc_process(plm_project):
    all_qc_records = None
    counter = 0
    all_samples = PlmSample.objects.filter(plm_project=plm_project)
    qc_samples = all_samples.filter(Q(is_qc_sample=True) | Q(tem_is_qc_sample=True))

    if PlmQCReplicateDuplicateItem.objects.filter(project=plm_project).exists():
        all_qc_records = PlmQCReplicateDuplicateItem.objects.filter(project=plm_project).values('qc_sample__lab_sample', 'original_sample__method')

    if all_qc_records:
        for qc_sample in qc_samples:
            if all_qc_records.filter(qc_sample__lab_sample=qc_sample.lab_sample, qc_sample__method=qc_sample.method).exists():
                pass
            else:
                generatePlmQCReplicateDuplicateItem(inp_qc_sample=qc_sample,inp_project=plm_project,inp_all_samples=all_samples)
                counter += 1
    else:
        for qc_sample in qc_samples:
            generatePlmQCReplicateDuplicateItem(inp_qc_sample=qc_sample,inp_project=plm_project,inp_all_samples=all_samples)
            counter += 1

    return counter
    
def generatePlmQCReplicateDuplicateItem(inp_qc_sample, inp_project, inp_all_samples):
    original_sample = inp_all_samples.get(lab_sample=inp_qc_sample.lab_sample[1:])
    input_qc_type = PlmTypeQCSample.Replicate if inp_qc_sample.lab_sample[0] == 'R' else PlmTypeQCSample.Duplicate
    if inp_qc_sample.method == SampleMethod.Sample1981:
        input_analysis_type = PlmTypeAnalysisSample.PLM
    if inp_qc_sample.method == SampleMethod.Sample1986:
        input_analysis_type = PlmTypeAnalysisSample.NOB
    if inp_qc_sample.method in [SampleMethod.Sample1984, SampleMethod.Sample1986, SampleMethod.Sample1986] and inp_qc_sample.tem_is_qc_sample:
        input_analysis_type = PlmTypeAnalysisSample.EPT

    PlmQCReplicateDuplicateItem.objects.create(qc_type = input_qc_type,
                                            analysis_type=input_analysis_type,
                                            project=inp_project,
                                            original_sample=original_sample,
                                            qc_sample=inp_qc_sample,
                                            analyst=inp_project.analyst,
                                            reviewer=inp_project.reviewed_by)

def validate_plm_project(plm_project, for_what='report'):
    errors = []
    report_fields = {'analyst':'No analyst',
                    'date_collect':'No date collect',
                    'date_analyze':'No date analysis', 
                    'date_report': 'No date report'}

    qc_fields = {'date_analyze':'No date analysis',
                'date_review':'No date review', 
                'analyst':'No analyst',
                'reviewed_by': 'No reviewer'}
    
    if for_what == 'report':
        fields = report_fields
    elif for_what == 'qc':
        fields = qc_fields

    for field, text_error in fields.items():
        if getattr(plm_project, field) is None:
            errors.append(text_error)
    
    return errors