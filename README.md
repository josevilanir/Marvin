# MARVIN: Assistente de Voz

## Visão Geral

*MARVIN* é um assistente de voz desenvolvido em Python que permite interagir com o Spotify, além de executar comandos de voz básicos. Ele é capaz de tocar playlists, controlar a reprodução de músicas, listar dispositivos, conectar-se a dispositivos, pausar, retomar, avançar e retroceder músicas, e reconhecer comandos em português e inglês. Além disso, o Marvin também pode realizar pesquisas na web, controlar o volume do computador, enviar mensagens no WhatsApp, e controlar vídeos no YouTube.

## Funcionalidades

- **Realizar pesquisa:** Abre seu navegador padrão e realiza uma pesquisa.
- **Data e hora:** Diz a data e a hora do dia.
- **Abrir aplicativo:** Abre qualquer aplicativo na área de trabalho ou presente no dicionário do projeto.
- **Tocar Playlist:** Reproduz uma playlist do Spotify com opção de modo padrão ou aleatório.
- **Controlar Reprodução:** Pausar, retomar, avançar e retroceder músicas.
- **Listar Dispositivos:** Lista dispositivos disponíveis para reprodução no Spotify.
- **Conectar a Dispositivo:** Conecta o *MARVIN* a um dispositivo selecionado para reprodução.
- **Listar Músicas de uma Playlist:** Lista todas as músicas de uma playlist especificada.
- **Reconhecimento de Voz:** Reconhece comandos de voz em português e inglês.
- **Síntese de Fala:** Responde aos comandos de voz utilizando síntese de fala.
- **Controle do YouTube:** Pesquisa vídeos, seleciona e reproduz vídeos e/ou canais no YouTube
- **Envio de Mensagens no WhatsApp:** Envia mensagens para contatos via WhatsApp.

## Pré-requisitos

Antes de começar, certifique-se de ter as seguintes ferramentas instaladas:

- **Python 3.11** ou superior
- **Pip** (gerenciador de pacotes do Python)
- **portaudio** (para uso do PyAudio)
- Conta no Spotify com permissões de desenvolvedor e um aplicativo registrado para obter as credenciais necessárias

## Instalação

1. Clone o repositório:

    ```bash
    git clone https://github.com/seu-usuario/marvin.git
    cd marvin
    ```

2. Crie um ambiente virtual (opcional, mas recomendado):

    ```bash
    python -m venv venv
    ```

    - Para Linux e macOS:

        ```bash
        source venv/bin/activate
        ```

    - Para Windows:

        ```bash
        .\venv\Scripts\activate
        ```

3. Instale as dependências:

    ```bash
    pip install -r requirements.txt
    ```

4. Configurar as Credenciais:

    - **Spotify:** Crie um arquivo chamado `config.py` na raiz do projeto e adicione suas credenciais do Spotify:

    ```python
    SPOTIPY_CLIENT_ID = 'your_spotify_client_id'
    SPOTIPY_CLIENT_SECRET = 'your_spotify_client_secret'
    SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback/'
    ```

    ```python
    TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
    TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
    TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'
    ```

# Comandos para execução:
Após iniciar o Marvin, você pode utilizar os seguintes comandos de voz:

- "Que horas são?" - Marvin informará a hora atual.
- "Abrir navegador" - Marvin abrirá o navegador e pedirá o termo a ser pesquisado.
- "Tocar música no Spotify" - Marvin tocará uma música da sua playlist.
- "Enviar mensagem no WhatsApp" - Marvin abrirá o whatsapp e pedirá o nome do contato e a mensagem.
- "Tocar NOME_DO_VIDEO no YouTube" - Marvin buscará um vídeo no YouTube.