import re


def _check_gibberish(text: str) -> float:
    if not text: return 1.0
    words = text.split()
    mixed_script_words = 0
    for word in words:
        cyrlat = bool(re.search(r'[IHOPCTYAEKMXBNa]{4,}', word))
        lat = len(re.findall(r'[a-zA-Z]', word))
        cyr = len(re.findall(r'[а-яА-ЯёЁ]', word))
        sym = len(re.findall(r"[!\"#\$%&'\(\)\*\+,-./:;<=>?@[\]^_`{|}~]", word))
        l_case = len(re.findall(r"[a-zа-я]", word))
        u_case = len(re.findall(r"[A-ZА-Я]", word))
        h_lat, h_cyr, h_sym, is_lc, is_uc = lat > 1, cyr > 1, sym > 1, l_case > 1, u_case > 1
        mixed_script_words += bool(
            sum([h_lat, h_sym, h_cyr]) > 1 or \
            (is_lc and is_uc) or \
            cyrlat
        )
    if len(words) == 0: return 1.0
    return mixed_script_words / len(words)


def check_text_adequate(text: str, threshold: float = 0.15) -> bool:
    return _check_gibberish(text) < threshold
