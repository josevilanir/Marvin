# MARVIN: Assistente de Voz

## Visão Geral

*MARVIN* é um assistente de voz desenvolvido em Python que permite interagir com o Spotify, além de executar comandos de voz básicos. Ele é capaz de tocar playlists, controlar a reprodução de músicas, listar dispositivos, conectar-se a dispositivos, pausar, retomar, avançar e retroceder músicas, e reconhecer comandos em inglês.

## Funcionalidades

- **Tocar Playlist**: Reproduz uma playlist do Spotify com opção de modo padrão ou aleatório.
- **Controlar Reprodução**: Pausar, retomar, avançar e retroceder músicas.
- **Listar Dispositivos**: Lista dispositivos disponíveis para reprodução no Spotify.
- **Conectar a Dispositivo**: Conecta o *MARVIN* a um dispositivo selecionado para reprodução.
- **Listar Músicas de uma Playlist**: Lista todas as músicas de uma playlist especificada.
- **Reconhecimento de Voz**: Reconhece comandos de voz em português e inglês.
- **Síntese de Fala**: Responde aos comandos de voz utilizando síntese de fala.

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

4. Configurar as Credenciais do Spotify:

    Crie um arquivo chamado `config.py` na raiz do projeto e adicione suas credenciais do Spotify:

    ```python
    SPOTIPY_CLIENT_ID = 'your_spotify_client_id'
    SPOTIPY_CLIENT_SECRET = 'your_spotify_client_secret'
    SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback/'
    ```

## Uso

### Executando o MARVIN

Para iniciar o *MARVIN*, execute o arquivo `main.py`:

```bash
python main.py
