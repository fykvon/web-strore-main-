import re


def check_name(data):
    """
    Проверка на ФИО пользователя.
    """

    full_name = re.findall(r'\w+', data)
    first_name = ' '.join(full_name[:2]) if len(full_name) > 2 else full_name[0]
    last_name = full_name[-1] if len(full_name) > 1 else ''
    return first_name, last_name
