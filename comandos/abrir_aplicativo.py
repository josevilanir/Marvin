# comandos/abrir_aplicativo.py
import subprocess
import platform
import os


def abrir_aplicativo(nome_aplicativo):
    if platform.system() == "Windows":
        # Caminho da área de trabalho do usuário
        area_de_trabalho = os.path.join(os.path.expanduser("~"), "Desktop")

        # Dicionário de aplicativos e seus caminhos
        aplicativos = {
            "bloco de notas": "notepad.exe",
            "calculadora": "calc.exe",
            # Exemplo para Google Chrome
            "spotify": "C:\\Users\\Vilanir\\AppData\\Roaming\\Spotify\\Spotify.exe",
            "steam": "C:\\Program Files (x86)\\Steam\\steam.exe"

        }

        if nome_aplicativo.lower() in aplicativos:
            caminho_aplicativo = aplicativos[nome_aplicativo.lower()]
            subprocess.Popen([caminho_aplicativo], shell=True)
        else:
            # Verifique se o aplicativo é um atalho na área de trabalho
            atalho = os.path.join(area_de_trabalho, f"{nome_aplicativo}.lnk")
            if os.path.exists(atalho):
                subprocess.Popen([atalho], shell=True)
            else:
                # Tente abrir diretamente como um executável
                if not nome_aplicativo.lower().endswith('.exe'):
                    nome_aplicativo += '.exe'
                subprocess.Popen([nome_aplicativo], shell=True)
    else:
        raise OSError("Sistema operacional não suportado.")
