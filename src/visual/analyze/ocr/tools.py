from typing import *
from model import OCROutput
import string

punctuation = r"""`'"()%&*+-,./\:;?"""
ru_alpha = ''.join(chr(i) for i in range(ord('а'), ord('я')))
alphabet = dict(en=string.ascii_letters + punctuation, ru=ru_alpha + ru_alpha.upper() + punctuation)


def choose_lang(variants: Dict[str, OCROutput]) -> str:
    res = {}
    for l, data in variants.items():
        txt = ' '.join(j.text for j in data.texts)
        orig_len = len(txt)
        l_txt = list(filter(lambda x: x.lower() in alphabet[l], txt))
        res[l] = len(l_txt) / orig_len
    return max(res.items(), key=lambda x: x[1])[0]
