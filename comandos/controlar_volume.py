from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL


def ajustar_volume(volume_str):
    try:
        # Obter o volume do sistema
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Converter a string em um valor numérico
        volume_valor = float(volume_str)

        # Verificar se o volume está entre 0 e 100
        if 0 <= volume_valor <= 100:
            # Definir o volume em uma escala de 0.0 a 1.0
            volume.SetMasterVolumeLevelScalar(volume_valor / 100, None)
            print(f"Volume ajustado para {volume_valor}%")
        else:
            print("Por favor, insira um valor entre 0 e 100.")

    except Exception as e:
        print(f"Erro ao ajustar o volume: {e}")
