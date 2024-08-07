import subprocess

def abrir_calculadora():
    subprocess.Popen(['start', 'calc'], shell=True)
