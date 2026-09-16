import random
import string

def generate_rand_string_4():
    length = 8
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
     