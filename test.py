import difflib

from config import codes, comments, suggestions, diff_const

for code in codes:
    "Проверка, что подбор работает правильно"
    found = difflib.get_close_matches(code, codes.keys(), cutoff=diff_const, n=1)[0]
    assert found == code

for ads in codes:
    string = f'Адрес: {ads}\n' + "\n".join(f'Код {i}: {x}' for i, x in enumerate(codes.get(ads, []))) + "\n"
    string += "Комментарии:" + "\t".join(str(i) for i in comments.get(ads, [])) + "\n"
    string += "\n".join(f'Предложенный код {i}: {x}' for i, x in enumerate(suggestions.get(ads, [])))
    assert len(string) < 4096, f"Длина вывода адреса {ads} превышает допустимый размер (4096)"
