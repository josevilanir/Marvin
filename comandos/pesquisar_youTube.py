import webbrowser
import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

def pesquisar_youtube_chrome(pesquisa):
    # Configurar o WebDriver para usar o Chrome
        try:
        # Tentando inicializar o WebDriver para o Chrome
            print("Tentando iniciar o WebDriver para o Chrome...")
            driver = webdriver.Chrome()  # Pode substituir por webdriver.Chrome(executable_path='/caminho/para/chromedriver')

            print("WebDriver iniciado com sucesso.")
            driver.get('https://www.youtube.com')

        # Aguarde o carregamento da página
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "search_query"))
            )

        # Localizar a barra de pesquisa e inserir o termo de pesquisa
            search_box = driver.find_element(By.NAME, "search_query")
            search_box.send_keys(pesquisa)
            search_box.send_keys(Keys.RETURN)

        # Aguarde os resultados carregarem
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
            )

            return driver

        except TimeoutError as e:
            print(f"Erro ao inicializar o WebDriver ou realizar a pesquisa: {e}")
            print(traceback.format_exc())
            driver.refresh()  # Recarrega a página em caso de falha
            return None

def voltar_para_pesquisa(driver):
    try:
        # Retroceder à página de pesquisa
        driver.back()
        print("Retornou para a página de pesquisa.")
        
        # Aguarde a página de pesquisa carregar novamente
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
        )

    except Exception as e:
        print(f"Erro ao tentar voltar para a página de pesquisa: {e}")
        print(traceback.format_exc())

def pausar_retornar_video(driver):
    try:
        driver.execute_script("var video = document.querySelector('video'); video.paused ? video.play() : video.pause();")
        print("Vídeo pausado ou retomado com sucesso.")
    except Exception as e:
        print(f"Erro ao tentar pausar ou retomar o vídeo: {e}")

def tela_cheia_chrome(driver):
    try:
        driver.fullscreen_window()
        print("Chrome está agora em tela cheia.")
    except Exception as e:
        print(f"Erro ao tentar colocar o Chrome em tela cheia: {e}")

def maximizar_janela(driver):
    try:
        # Maximizar a janela do Chrome
        driver.maximize_window()
        print("Janela maximizada.")
    except Exception as e:
        print(f"Erro ao tentar maximizar a janela: {e}")

def sair_tela_cheia():
    try:
        # Simular o pressionamento da tecla 'Esc' usando pyautogui
        pyautogui.press('esc')
        print("Tecla 'Esc' pressionada para sair da tela cheia.")
    except Exception as e:
        print(f"Erro ao tentar sair da tela cheia: {e}")

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

def navegar_aba(driver, aba="videos"):
    try:
        # Pegar a URL atual do canal
        canal_url = driver.current_url

        # Garantir que estamos na aba correta (Vídeos, Shorts, etc.)
        if aba.lower() not in canal_url:
            # Construir a URL da aba específica
            canal_url_aba = f"https://www.youtube.com/@{canal_url.split('@')[1].split('/')[0]}/{aba.lower()}"
            
            # Navegar para a URL da aba
            driver.get(canal_url_aba)
            print(f"Navegado para a aba {aba.capitalize()}.")
    except Exception as e:
        print(f"Erro ao tentar navegar para a aba '{aba.capitalize()}': {e}")

def clicar_video_canal(driver, video_title):
    try:
        # Navegar para a aba de vídeos
        navegar_aba(driver, "videos")
         
        # Aguardar até que os vídeos estejam carregados na página
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
        )

        # Converter o título do vídeo informado pelo usuário para minúsculas
        video_title_lower = video_title.lower()

        # Encontrar todos os vídeos na página
        videos = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
        
        print(f"Vídeos encontrados: {[video.get_attribute('title') for video in videos]}")

        # Verificar se algum dos vídeos na página corresponde ao título informado
        for video in videos:
            if video_title_lower in video.get_attribute('title').lower():
                # Usar JavaScript para clicar
                driver.execute_script("arguments[0].click();", video)
                print(f"Vídeo '{video_title}' foi clicado.")
                return
        
        print(f"Vídeo com o título '{video_title}' não encontrado.")

    except Exception as e:
        print(f"Erro ao tentar clicar no vídeo '{video_title}': {e}")

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
    pyautogui.moveTo(1332, 787)  # As coordenadas (300, 300) são um exemplo; ajuste conforme necessário
    pyautogui.click()