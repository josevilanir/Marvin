MARVIN: Assistente de Voz
Visão Geral
MARVIN é um assistente de voz desenvolvido em Python que permite interagir com o Spotify, além de executar comandos de voz básicos. Ele é capaz de tocar playlists, controlar a reprodução de músicas, listar dispositivos, conectar-se a dispositivos, pausar, retomar, avançar e retroceder músicas, e reconhecer comandos em inglês.

Funcionalidades
Tocar Playlist: Reproduz uma playlist do Spotify com opção de modo padrão ou aleatório.
Controlar Reprodução: Pausar, retomar, avançar e retroceder músicas.
Listar Dispositivos: Lista dispositivos disponíveis para reprodução no Spotify.
Conectar a Dispositivo: Conecta o MARVIN a um dispositivo selecionado para reprodução.
Listar Músicas de uma Playlist: Lista todas as músicas de uma playlist especificada.
Reconhecimento de Voz: Reconhece comandos de voz em português e inglês.
Síntese de Fala: Responde aos comandos de voz utilizando síntese de fala.
Pré-requisitos
Antes de começar, certifique-se de ter as seguintes ferramentas instaladas:

Python 3.11 ou superior
Pip (gerenciador de pacotes do Python)
portaudio (para uso do PyAudio)
Conta no Spotify com permissões de desenvolvedor e um aplicativo registrado para obter as credenciais necessárias
Instalação
Clone o repositório:

git clone https://github.com/seu-usuario/marvin.git
cd marvin

Crie um ambiente virtual (opcional, mas recomendado):

python -m venv venv
source venv/bin/activate # Para Linux e macOS
.\venv\Scripts\activate # Para Windows

Instale as dependências:

pip install -r requirements.txt

Configurar as Credenciais do Spotify:

Crie um arquivo chamado config.py na raiz do projeto e adicione suas credenciais do Spotify:

SPOTIPY_CLIENT_ID = 'your_spotify_client_id'
SPOTIPY_CLIENT_SECRET = 'your_spotify_client_secret'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback/'

Uso
Executando o MARVIN
Para iniciar o MARVIN, execute o arquivo main.py:

python main.py

Comandos de Voz
Tocar Playlist:

Comando: "Tocar playlist"
Exemplo de resposta: "Qual playlist você deseja ouvir?" (Após a resposta) "Você deseja ouvir no modo padrão ou aleatório?"
Controlar Reprodução:

Comandos: "Pausar", "Retomar", "Próxima música", "Música anterior"
Listar Dispositivos:

Comando: "Listar dispositivos"
Conectar a Dispositivo:

Comando: "Conectar dispositivo"
Listar Músicas de uma Playlist:

Comando: "Listar músicas da playlist"
