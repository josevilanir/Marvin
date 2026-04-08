# MARVIN v2 — Assistente de IA Pessoal

> Assistente estilo JARVIS em português brasileiro.  
> Voz local, IA via Groq, widget flutuante PyQt6, proatividade em background.

---

## Arquitetura

```
main.py
├── frontend/
│   ├── marvin_widget.py    # Janela PyQt6 always-on-top, draggable, system tray
│   ├── bridge.py           # Fronteira thread-safe Qt ↔ backend (sinais + QThread)
│   ├── chat_panel.py       # Histórico de chat com bubbles
│   ├── system_panel.py     # CPU / RAM / status em tempo real
│   ├── voice_animator.py   # Animação de ondas (idle / speaking / listening)
│   └── assets/style.qss    # Dark HUD theme (cyan #00d4ff)
│
└── backend/
    ├── main_controller.py           # Controlador principal (modo headless/voz)
    └── app/
        ├── ai/
        │   ├── ai_processor.py       # Groq + function calling loop
        │   ├── tool_registry.py      # Registro de ferramentas para o LLM
        │   ├── service_registrar.py  # Registra todos os serviços no registry
        │   ├── conversation_manager.py # Memória curta (RAM) + longa (SQLite)
        │   ├── jarvis_personality.py  # System prompt do Marvin
        │   ├── system_observer.py     # Métricas psutil em background thread
        │   └── proactivity_agent.py   # Alertas proativos (pausa, RAM, processo)
        ├── services/
        │   ├── spotify_service.py
        │   ├── youtube_service.py
        │   ├── whatsapp_service.py
        │   └── system_service.py
        └── voice_interface/
            ├── speech_recognizer.py   # STT via Whisper/SpeechRecognition
            └── speech_synthesizer.py  # TTS via pyttsx3 (voz Microsoft Maria PT-BR)
```

**Modelo:** `llama-3.3-70b-versatile` via Groq API (gratuito)  
**TTS:** pyttsx3 — local, zero latência, zero rede  
**STT:** Whisper  
**UI:** PyQt6 — widget sempre visível, animações 30fps

---

## Instalação

### Pré-requisitos
- Python 3.12+
- Windows 10/11 (TTS e janela ativa usam APIs Win32)
- Conta Groq gratuita: [console.groq.com](https://console.groq.com)
- Conta Spotify Developer (opcional): [developer.spotify.com](https://developer.spotify.com)

### Passos

```bash
git clone <repo>
cd Marvin

# Instalar dependências
pip install -r backend/requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env   # edite com suas chaves
```

### Arquivo `.env`

```env
GROQ_API_KEY="gsk_..."

# Spotify (opcional)
SPOTIPY_CLIENT_ID="..."
SPOTIPY_CLIENT_SECRET="..."
SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
```

---

## Como rodar

```bash
# Interface gráfica (recomendado)
python main.py

# Modo headless (linha de comando)
cd backend
python main_controller.py
```

---

## Ferramentas disponíveis (19 total)

### Sistema
| Comando de exemplo | Ferramenta |
|---|---|
| "Que horas são?" | `get_datetime` |
| "Abre a calculadora" | `open_application` |
| "Pesquisa Python na web" | `search_web` |
| "Define um timer de 10 minutos" | `start_timer` |
| "Coloca o volume em 50%" | `set_system_volume` |

### Spotify
| Comando de exemplo | Ferramenta |
|---|---|
| "Toca Bohemian Rhapsody" | `play_music` |
| "Pausa a música" | `pause_music` |
| "Retoma a música" | `resume_music` |
| "Próxima faixa" | `next_track` |
| "Faixa anterior" | `previous_track` |
| "Aumenta o volume do Spotify para 70" | `set_spotify_volume` |
| "O que está tocando?" | `get_current_track` |
| "Toca a playlist Lofi" | `play_playlist` |

### YouTube
| Comando de exemplo | Ferramenta |
|---|---|
| "Pesquisa lofi hip hop no YouTube" | `youtube_search` |
| "Clica no primeiro vídeo" | `youtube_play_video` |
| "Pausa o vídeo" | `youtube_pause` |
| "Tela cheia" | `youtube_fullscreen` |
| "Pula o anúncio" | `youtube_skip_ad` |
| "Volta a página" | `youtube_go_back` |

### WhatsApp
| Comando de exemplo | Ferramenta |
|---|---|
| "Manda mensagem para João dizendo oi" | `send_whatsapp` |

---

## Proatividade

O Marvin monitora o sistema em background e fala sem ser perguntado:

| Gatilho | Condição | Cooldown |
|---|---|---|
| **Pausa** | 2h sem atividade | 2h |
| **RAM alta** | RAM > 85% por 60s | 30min |
| **Processo aberto** | VS Code, Chrome, OBS, etc. | 1x por sessão |

---

## Testes

```bash
cd backend
pytest tests/services -v
```

52 testes — todos passando.

---

## Estrutura de memória

- **Curta:** últimas 20 mensagens em RAM (deque)  
- **Longa:** histórico completo em SQLite (`data/marvin_memory.db`)

---

## Variáveis de ambiente

| Variável | Obrigatório | Descrição |
|---|---|---|
| `GROQ_API_KEY` | ✓ | Chave da API Groq |
| `SPOTIPY_CLIENT_ID` | Opcional | ID do app Spotify |
| `SPOTIPY_CLIENT_SECRET` | Opcional | Secret do app Spotify |
| `SPOTIPY_REDIRECT_URI` | Opcional | URI de redirect Spotify |
