from datetime import datetime


def obter_data_e_hora():
    agora = datetime.now()
    data_e_hora = agora.strftime("São %H:%M.")
    return data_e_hora
