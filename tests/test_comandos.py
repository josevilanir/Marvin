import pytest
from unittest.mock import patch
from comandos.tocar_musica import pausar_musica


def test_pausar_musica_sem_dispositivo():
    with patch('comandos.tocar_musica.listar_dispositivos_spotify', return_value=[]):
        with pytest.raises(Exception) as excinfo:
            pausar_musica()
        assert str(
            excinfo.value) == "Nenhum dispositivo disponível. Por favor, verifique se há dispositivos conectados."


def test_pausar_musica_sucesso():
    with patch('comandos.tocar_musica.listar_dispositivos_spotify', return_value=['Dispositivo 1']), \
            patch('comandos.tocar_musica.sp.pause_playback') as mock_pause:

        pausar_musica()
        mock_pause.assert_called_once()


def test_pausar_musica_erro():
    with patch('comandos.tocar_musica.listar_dispositivos_spotify', return_value=['Dispositivo 1']), \
            patch('comandos.tocar_musica.sp.pause_playback', side_effect=Exception("Erro ao pausar")):

        with pytest.raises(Exception) as excinfo:
            pausar_musica()
        assert str(excinfo.value) == "Erro ao pausar"
