import pytest
import re
from unittest.mock import Mock
from backend.app.nlp.intent_processor import IntentProcessor
from re import compile, IGNORECASE


@pytest.fixture
def processor():
    mock_controller = Mock()

    mock_controller.spotify_service.play_music.return_value = {
        "message": "Tocando Imagine no Spotify."
    }

    mock_controller.whatsapp_service.send_message.return_value = {
        "message": "Mensagem enviada com sucesso."
    }

    mock_controller.system_service.desligar.return_value = {
        "message": "Desligando o sistema."
    }

    mock_controller.system_service.reiniciar.return_value = {
        "message": "Reiniciando o sistema."
    }

    processor = IntentProcessor(mock_controller)

    processor.intent_patterns = [
    {
        "name": "GET_TIME",
        "regex": compile(r"^que horas (são|é)$", IGNORECASE),
        "handler": lambda e, **_: "Agora são 12:34."
    },
    {
        "name": "GET_MARVIN_INFO",
        "regex": compile(r"^quem é você$", IGNORECASE),
        "handler": lambda e, **_: "Sou Marvin, seu assistente pessoal desenvolvido por José Vilanir."
    },
    {
        "name": "PLAY_SPOTIFY_SONG",
        "regex": re.compile(r"toque (?P<nome_musica>.+)"),
        "entities": {"nome_musica": 1},
        "handler": lambda e, **_: mock_controller.spotify_service.play_music(e["nome_musica"])["message"]
    },
    {
        "name": "SEND_WHATSAPP_MESSAGE",
        "regex": re.compile(r"mande mensagem para (?P<nome_contato>\w+) dizendo (?P<mensagem>.+)"),
        "entities": {"nome_contato": 1, "messagem": 2},
        "handler": lambda e, **_: mock_controller.whatsapp_service.send_message(e["nome_contato"], e["messagem"])["message"]
    },
    {
        "name": "SHUTDOWN_PC",
        "regex": re.compile(r"desligar (o )?pc"),
        "handler": lambda e, **_: mock_controller.system_service.desligar()["message"]
    },
    {
        "name": "RESTART_PC",
        "regex": re.compile(r"reiniciar (o )?pc"),
        "handler": lambda e, **_: mock_controller.system_service.reiniciar()["message"]
    },
]

    return processor


def test_get_time_intent(processor):
    result = processor.process("que horas são")
    assert "Agora são" in result


def test_get_marvin_info_intent(processor):
    result = processor.process("quem é você")
    assert "Sou Marvin" in result


def test_play_spotify_song_intent(processor):
    result = processor.process("toque Imagine")
    assert result == "Tocando Imagine no Spotify."


def test_send_whatsapp_message_intent(processor):
    result = processor.process("mande mensagem para Fulano dizendo Olá")
    assert result == "Mensagem enviada com sucesso."


def test_shutdown_pc_intent(processor):
    result = processor.process("desligar o pc")
    assert result == "Desligando o sistema."


def test_restart_pc_intent(processor):
    result = processor.process("reiniciar o pc")
    assert result == "Reiniciando o sistema."


def test_unknown_intent(processor):
    result = processor.process("me diga a previsão do tempo")
    assert result == "Desculpe, não consegui entender o comando."


def test_missing_music_name(processor):
    result = processor.process("toque")
    assert result == "Desculpe, não consegui entender o comando."


def test_missing_whatsapp_data(processor):
    result = processor.process("mande mensagem")
    assert result == "Desculpe, não consegui entender o comando."

def test_play_spotify_song_sem_nome(processor):
    result = processor.process("toque ")
    assert result == "Desculpe, não consegui entender o comando."

def test_get_time_com_extra_na_frase(processor):
    result = processor.process("que horas são agora?")
    assert result == "Desculpe, não consegui entender o comando."

def test_get_marvin_info_case_insensitive(processor):
    result = processor.process("QUEM É VOCÊ")
    assert result == "Sou Marvin, seu assistente pessoal desenvolvido por José Vilanir."

def test_send_whatsapp_sem_mensagem(processor):
    result = processor.process("mande mensagem para Fulano")
    assert result == "Desculpe, não consegui entender o comando."

def test_comando_totalmente_inesperado(processor):
    result = processor.process("abracadabra voar azul céu")
    assert result == "Desculpe, não consegui entender o comando."

