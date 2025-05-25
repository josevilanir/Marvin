# MARVIN: Assistente de Voz Pessoal (Backend Refatorado)

## Visão Geral

MARVIN é um assistente de voz pessoal desenvolvido em Python, agora com uma arquitetura de backend refatorada para maior robustez e escalabilidade. Ele permite interagir com diversos serviços e executar comandos de voz para controlar seu ambiente digital.

Esta versão foca no backend do Marvin, que processa os comandos de voz e interage com os serviços. Um frontend desktop será desenvolvido separadamente para interagir com este backend.

## Arquitetura do Backend

O backend do MARVIN é construído com os seguintes componentes principais:

* **MainController**: Orquestra o fluxo de comandos, inicializa serviços e a interface de voz.
* **Services**: Módulos dedicados para cada funcionalidade principal:
    * `SpotifyService`: Interage com a API do Spotify.
    * `SystemService`: Controla funções do sistema operacional, data/hora, volume, timer, etc.
    * `YouTubeService`: Controla a navegação e reprodução no YouTube via Selenium.
    * `WhatsAppService`: Automatiza o envio de mensagens no WhatsApp Web via PyAutoGUI.
* **VoiceInterface**:
    * `SpeechRecognizer`: Converte a fala do usuário em texto.
    * `SpeechSynthesizer`: Converte o texto de resposta do Marvin em voz.
* **NLP (Natural Language Processing)**:
    * `IntentProcessor`: Usa expressões regulares para identificar a intenção do usuário e extrair entidades dos comandos de voz.
* **Core**:
    * `ConfigManager`: Gerencia configurações e credenciais de forma segura.
    * `Constants`: Define constantes para o projeto.

## Pré-requisitos

Antes de começar, certifique-se de ter as seguintes ferramentas e configurações:

* **Python 3.10+**
* **Pip** (gerenciador de pacotes do Python)
* **PortAudio** (para `PyAudio`, uma dependência do `SpeechRecognition`)
* **Google Chrome** instalado (para `YouTubeService` via Selenium)
* **ChromeDriver** compatível com sua versão do Chrome (o Selenium Manager pode tentar instalá-lo automaticamente, mas tê-lo no PATH é mais garantido).
* **Conta no Spotify Developer**: Para obter credenciais da API do Spotify.
* **WhatsApp Web**: Logado no seu navegador padrão para que o `WhatsAppService` funcione.
* **Para Linux (para `WhatsAppService` e `SpeechRecognizer`)**:
    * `scrot` (para screenshots, às vezes uma dependência do PyAutoGUI)
    * `xclip` ou `xsel` (para `pyperclip`)
    * `alsa-utils` (ou equivalentes para gerenciamento de áudio)

## Configuração do Ambiente

1.  **Clone o Repositório (se aplicável):**
    ```bash
    # git clone ...
    # cd marvin_professional
    ```

2.  **Crie e Ative um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    ```
    * No Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * No Linux/macOS:
        ```bash
        source venv/bin/activate
        ```

3.  **Instale as Dependências do Backend:**
    Navegue até a pasta `backend/` e instale as dependências:
    ```bash
    cd backend
    pip install -r requirements.txt
    # Ou requirements_backend.txt se você renomeou
    ```
    Certifique-se de que seu `requirements.txt` (ou `requirements_backend.txt`) inclua todas as bibliotecas necessárias: `speechrecognition`, `pyaudio`, `gtts`, `pygame`, `spotipy`, `python-dotenv`, `selenium`, `webdriver-manager` (opcional), `pyautogui`, `pyperclip`, `numpy`, `noisereduce`, `pycaw` (para Windows).

4.  **Configure as Credenciais e Recursos:**
    * **Arquivo `.env`**: Crie um arquivo chamado `.env` na raiz do projeto (`marvin_professional/.env`) ou na raiz do backend (`marvin_professional/backend/.env`). Adicione suas credenciais do Spotify:
        ```env
        SPOTIPY_CLIENT_ID="SEU_CLIENT_ID_AQUI"
        SPOTIPY_CLIENT_SECRET="SEU_CLIENT_SECRET_AQUI"
        SPOTIPY_REDIRECT_URI="SEU_REDIRECT_URI_AQUI"
        ```
        **Importante**: Adicione `.env` ao seu arquivo `.gitignore`.
    * **Som do Alarme**:
        * Crie a pasta `backend/app/resources/`.
        * Coloque o arquivo de som `despertador.mp3` dentro desta pasta.
    * **Constantes**: Verifique o arquivo `backend/app/core/constants.py` e certifique-se de que `RESOURCE_PATH` aponta corretamente para a pasta `resources`.

## Executando o Backend do MARVIN

Para iniciar o backend do Marvin e o loop de interação por voz:

1.  Navegue até a pasta raiz do projeto (`marvin_professional/` se você estiver seguindo a estrutura sugerida).
2.  Execute o `main_controller.py` como um módulo (isso ajuda o Python a resolver os imports do pacote `app` corretamente):
    ```bash
    python -m backend.main_controller
    ```
    Alternativamente, se você estiver dentro da pasta `backend/` e seu `PYTHONPATH` estiver configurado para incluir a pasta `marvin_professional/`, você pode tentar executar:
    ```bash
    python main_controller.py
    ```

Após a inicialização bem-sucedida, Marvin dirá "Marvin está pronto." e começará a ouvir pela palavra de ativação "Marvin".

## Comandos de Voz do MARVIN

Diga **"Marvin"** seguido de um dos comandos abaixo. Os exemplos de frases são sugestões; o `IntentProcessor` usa expressões regulares para tentar entender variações.

---

### Comandos Gerais e do Sistema (`SystemService`)

* **Que horas são?**
    * Ex: "Marvin, que horas são?"
    * Ex: "Marvin, horas."
* **Fale sobre você:**
    * Ex: "Marvin, me fale mais de você."
    * Ex: "Marvin, quem é você?"
* **Abrir Calculadora:**
    * Ex: "Marvin, abrir calculadora."
    * Ex: "Marvin, calculadora."
* **Abrir Aplicativo [Nome do Aplicativo]:**
    * Ex: "Marvin, abrir aplicativo bloco de notas."
    * Ex: "Marvin, abra o aplicativo spotify."
    * Ex: "Marvin, abrir steam."
* **Pesquisar na Web por [Termo da Pesquisa]:**
    * Ex: "Marvin, pesquisar na web por cotação do dólar."
    * Ex: "Marvin, procure por receitas de bolo de chocolate."
* **Definir Timer de [Duração]:**
    * Ex: "Marvin, defina um timer de 5 minutos."
    * Ex: "Marvin, timer para 1 hora e 30 segundos."
* **Ajustar Volume para [Nível%]:**
    * Ex: "Marvin, ajuste o volume para 50%."
    * Ex: "Marvin, volume para 75."

---

### Comandos do Spotify (`SpotifyService`)

* **Tocar Música [Nome da Música]:**
    * Ex: "Marvin, tocar música Bohemian Rhapsody."
    * Ex: "Marvin, toque som Lose Yourself Eminem."
* **Pausar Spotify/Música:**
    * Ex: "Marvin, pausar música."
    * Ex: "Marvin, pause o spotify."
* **Retomar/Play Spotify/Música:**
    * Ex: "Marvin, play no spotify."
    * Ex: "Marvin, continuar música."
* **Próxima Música:**
    * Ex: "Marvin, próxima música."
    * Ex: "Marvin, avançar spotify."
* **Música Anterior:**
    * Ex: "Marvin, música anterior."
    * Ex: "Marvin, voltar música no spotify."
* **Listar Playlists:**
    * Ex: "Marvin, listar minhas playlists."
    * Ex: "Marvin, quais são minhas playlists?"
* **Tocar Playlist [Nome ou Número da Playlist] (opcional: no modo [aleatório/padrão]):**
    * Ex: "Marvin, tocar playlist Minhas Favoritas."
    * Ex: "Marvin, toque a playlist número um."
    * Ex: "Marvin, tocar playlist Rock Clássico no modo aleatório."
* **Adicionar Música [Nome da Música] à Playlist [Nome da Playlist]:**
    * Ex: "Marvin, adicionar música Stairway to Heaven à playlist Rock Clássico."
* **Listar Músicas da Playlist [Nome da Playlist]:**
    * Ex: "Marvin, listar músicas da playlist Minhas Favoritas."
    * Ex: "Marvin, o que tem na playlist número dois?"
* **Conectar Dispositivo Spotify (ou Listar):**
    * Ex: "Marvin, listar dispositivos spotify."
    * Ex: "Marvin, conectar spotify ao dispositivo Echo Dot." (Se o nome for reconhecido)

---

### Comandos do YouTube (`YouTubeService`)

* **Tocar/Pesquisar [Termo da Pesquisa] no YouTube:**
    * Ex: "Marvin, tocar vídeos de gatos engraçados no YouTube."
    * Ex: "Marvin, pesquisar como fazer pão no YouTube."
    * Ex: "Marvin, youtube receitas de lasanha."
* **Clicar no Vídeo Número/Posição [Número]:**
    * Ex: "Marvin, clicar no vídeo número dois."
    * Ex: "Marvin, selecionar o vídeo na posição 3."
    * Ex: "Marvin, tocar o primeiro vídeo."
* **Selecionar Canal (após uma pesquisa que mostre canais):**
    * Ex: "Marvin, selecionar o canal."
* **Controlar Vídeo do YouTube:**
    * Pausar/Retomar: "Marvin, pausar vídeo." / "Marvin, play no vídeo do youtube."
    * Tela Cheia: "Marvin, tela cheia no youtube."
    * Sair da Tela Cheia: "Marvin, sair da tela cheia."
    * Maximizar Janela: "Marvin, maximizar janela do youtube."
* **Pular Anúncio/Comercial:**
    * Ex: "Marvin, pular anúncio."
* **Voltar no YouTube (Página Anterior):**
    * Ex: "Marvin, voltar no youtube."

---

### Comandos do WhatsApp (`WhatsAppService`)

* **Enviar Mensagem para [Nome do Contato] dizendo [Mensagem]:**
    * Ex: "Marvin, enviar mensagem para João dizendo Olá, tudo bem?"
    * Ex: "Marvin, whatsapp para Maria com a mensagem Feliz aniversário!"
    * **Atenção**: Requer que o WhatsApp Web esteja logado e a janela do navegador ganhe foco rapidamente após ser aberta.

---

### Encerrar o Marvin

* **Tchau / Adeus / Desligar Marvin:**
    * Ex: "Marvin, tchau."
    * Ex: "Marvin, desligar marvin."

---

## Desenvolvimento Futuro

* Implementação de um frontend desktop dedicado.
* Aprimoramento do `IntentProcessor` com NLU mais avançado.
* Gerenciamento de estado de conversação para diálogos mais complexos.
* Maior configurabilidade de caminhos de aplicativos e preferências do usuário (possivelmente via banco de dados).
* Testes unitários e de integração abrangentes.

## Solução de Problemas Comuns

* **Erro de Microfone/SpeechRecognition**: Verifique se o microfone está conectado, funcionando e selecionado corretamente pelo sistema. Instale `PyAudio` e `PortAudio`.
* **Falha na Autenticação do Spotify**: Garanta que as credenciais no arquivo `.env` estão corretas e possuem o escopo necessário. Na primeira vez, o Spotipy pode imprimir um URL no console para você autorizar o aplicativo.
* **ChromeDriver/Selenium não funciona**: Verifique se o ChromeDriver está no PATH ou se o Selenium Manager está funcionando. A versão do ChromeDriver deve ser compatível com a do seu Google Chrome.
* **PyAutoGUI/WhatsApp não funciona**: Certifique-se de que a janela do WhatsApp Web está em foco. Em alguns sistemas Linux, `pyautogui` pode exigir configuração adicional (`scrot` instalado, servidor Xorg em vez de Wayland por padrão para algumas funcionalidades). `pyperclip` no Linux requer `xclip` ou `xsel`.