def numero_por_extenso_para_numero(extenso):
    numeros_por_extenso = {
        'zero': 0,
        'primeiro': 1,
        'segunda': 2,
        'terceira': 3,
        'quarta': 4,
        'quinta': 5,
        'sexta': 6,
        'setima': 7,
        'oitava': 8,
        'nove': 9,
        'dez': 10,
        'onze': 11,
        'doze': 12,
        'treze': 13,
        'quatorze': 14,
        'quinze': 15,
        'dezesseis': 16,
        'dezessete': 17,
        'dezoito': 18,
        'dezenove': 19,
        'vinte': 20}

    # Verifica se o input é None
    if extenso is None:
        return None

    # Verifica se o input é um número inteiro
    if isinstance(extenso, int):
        return extenso

    # Se o input é uma string, tenta converter
    if isinstance(extenso, str):
        extenso = extenso.lower()
        return numeros_por_extenso.get(extenso, None)

    return None
