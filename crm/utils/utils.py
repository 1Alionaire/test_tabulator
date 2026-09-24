import random
import string
from decimal import Decimal, ROUND_HALF_UP

def generate_rand_string_4():
    length = 8
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def weight_rounder(input_value):
    return Decimal(str(input_value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

DECIMALS       = 4                  # точность весов

def r(x):
    return round(x, DECIMALS)


def calc(d):
    """Пересчёт процентов из (уже округлённых) весов — проверка."""
    w_sample = weight_rounder(d["w_crucible_with_sample"] - d["w_crucible"])
    org = weight_rounder((d["w_crucible_with_sample"] - d["w_sample_ashed"]) / w_sample * 100)
    residue = weight_rounder((d["w_petri_with_sample"] - d["w_petri"]) / w_sample * 100)
    caco3 = weight_rounder(100 - residue - org)
    return w_sample, org, residue, caco3


def generate_weight_item(max_tries=1000, RESIDUE_RANGE = (20.0, 40.0)):
        # ---- Настройки ---------------------------------------------------------
    CRUCIBLE_RANGE = (8.1000, 8.6000)   # w_crucible, г
    PETRI_RANGE    = (8.1000, 8.7000)   # w_petri и w_petri_with_sample, г
    SAMPLE_RANGE   = (0.1000, 0.5000)   # масса навески w_sample, г (подставь свою)
    ORG_RANGE      = (30.0, 95.0)        # org, %
    CACO3_MIN      = 0.5                # caco3 должен быть не меньше этого, %


    for _ in range(max_tries):
        # 1. Базовые веса
        var_crucible = r(random.uniform(*CRUCIBLE_RANGE))
        w_sample = r(random.uniform(*SAMPLE_RANGE))

        # 2. Сначала целевые проценты
        residue_pct = random.uniform(*RESIDUE_RANGE)
        org_hi = min(ORG_RANGE[1], 100 - residue_pct - CACO3_MIN)
        if org_hi <= ORG_RANGE[0]:
            continue
        org_pct = random.uniform(ORG_RANGE[0], org_hi)

        # 3. Чашка Петри: вес с остатком тоже должен влезть в 8.1–9.1
        residue_mass = w_sample * residue_pct / 100
        petri_hi = PETRI_RANGE[1] - residue_mass
        if petri_hi <= PETRI_RANGE[0]:
            continue
        w_petri = r(random.uniform(PETRI_RANGE[0], petri_hi))

        # 4. Обратный расчёт весов из процентов
        w_crucible_with_sample = r(var_crucible + w_sample)
        d = {
            "w_crucible": weight_rounder(var_crucible),
            "w_crucible_with_sample": weight_rounder(w_crucible_with_sample),
            "w_sample_ashed": weight_rounder(r(w_crucible_with_sample - w_sample * org_pct / 100)),
            "w_petri": weight_rounder(w_petri),
            "w_petri_with_sample": weight_rounder(r(w_petri + residue_mass)),
        }

        # 5. Проверка после округления
        w_s, org, res, caco3 = calc(d)
        if (w_s > 0 and org > 0 and caco3 >= CACO3_MIN
                and RESIDUE_RANGE[0] <= res <= RESIDUE_RANGE[1]
                and PETRI_RANGE[0] <= d["w_petri_with_sample"] <= PETRI_RANGE[1]):
            d.update(w_sample=r(w_s), org=round(org, 2),
                     residue=round(res, 2), caco3=round(caco3, 2))
            return d

    raise RuntimeError("Не удалось подобрать значения — проверь, совместимы ли интервалы")
