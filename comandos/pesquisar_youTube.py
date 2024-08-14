import webbrowser
import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

def pesquisar_youtube_chrome(pesquisa):
    # Configurar o WebDriver para usar o Chrome
        try:
        # Tentando inicializar o WebDriver para o Chrome
            print("Tentando iniciar o WebDriver para o Chrome...")
            driver = webdriver.Chrome()  # Pode substituir por webdriver.Chrome(executable_path='/caminho/para/chromedriver')

            print("WebDriver iniciado com sucesso.")
            driver.get('https://www.youtube.com')

        # Aguarde o carregamento da página
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "search_query"))
            )

        # Localizar a barra de pesquisa e inserir o termo de pesquisa
            search_box = driver.find_element(By.NAME, "search_query")
            search_box.send_keys(pesquisa)
            search_box.send_keys(Keys.RETURN)

        # Aguarde os resultados carregarem
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
            )

            return driver

        except Exception as e:
                print(f"Erro ao inicializar o WebDriver ou realizar a pesquisa: {e}")
                print(traceback.format_exc())
                return None

def clicar_video(driver, posicao=1):
    if driver is None:
        print("Driver não foi inicializado corretamente.")
        return

    try:
        # Espera até que os elementos dos vídeos estejam visíveis
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
        )
        
        # Busca todos os vídeos listados na página
        videos = driver.find_elements(By.XPATH, '//a[@id="video-title"]')

        if len(videos) >= posicao:
            # Clica no vídeo correspondente à posição desejada
            videos[posicao - 1].click()
        else:
            print(f"Não há vídeos suficientes na lista. Posição solicitada: {posicao}, vídeos disponíveis: {len(videos)}")

    except Exception as e:
        print(f"Erro ao tentar clicar no vídeo na posição {posicao}: {e}")

def selecionar_canal(driver):
    # Aguarde os resultados carregarem
    time.sleep(2)

    # Tentar clicar no canal
    try:
        canal = driver.find_element(By.XPATH, '//ytd-channel-renderer//a[@id="main-link"]')
        canal.click()
    except Exception as e:
        print(f"Erro ao tentar selecionar o canal: {e}")
        return

    # Aguarde o canal carregar
    time.sleep(3)

def pesquisar_youtube(pesquisa):
    # Abre o YouTube no navegador padrão
    url = f"https://www.youtube.com/results?search_query={pesquisa.replace(' ', '+')}"
    webbrowser.open(url)
    
    # Dá tempo para a página carregar
    time.sleep(2)

def abriPrimeiro_video():
    # Move o cursor para o local do primeiro vídeo e clica (ajuste as coordenadas conforme necessário)
    pyautogui.moveTo(750, 200)  # As coordenadas (300, 300) são um exemplo; ajuste conforme necessário
    pyautogui.click()

def Pular_Anuncio():
    # Move o cursor para o local do primeiro vídeo e clica (ajuste as coordenadas conforme necessário)
    pyautogui.moveTo(1339, 762)  # As coordenadas (300, 300) são um exemplo; ajuste conforme necessário
    pyautogui.click()