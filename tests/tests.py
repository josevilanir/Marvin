import pytest
from unittest.mock import patch, MagicMock
from comandos.tocar_musica import pausar_musica, listar_dispositivos_spotify

def test_pausar_musica_sem_dispositivo():
    with patch('comandos.listar_dispositivos_spotify', return_value=[]):
        with pytest.raises(Exception) as excinfo:
            pausar_musica()
        assert str(excinfo.value) == "Nenhum dispositivo disponível. Por favor, verifique se há dispositivos conectados."

def test_pausar_musica_sucesso():
    with patch('comandos.listar_dispositivos_spotify', return_value=['Dispositivo 1']), \
         patch('seu_modulo.sp.pause_playback') as mock_pause:
        
        pausar_musica()
        mock_pause.assert_called_once()  # Verifica se a função pause_playback foi chamada uma vez

def test_pausar_musica_erro():
    with patch('comandos.listar_dispositivos_spotify', return_value=['Dispositivo 1']), \
         patch('comandos.sp.pause_playback', side_effect=Exception("Erro ao pausar")):
        
        with pytest.raises(Exception) as excinfo:
            pausar_musica()
        assert str(excinfo.value) == "Erro ao pausar"  # Verifica se a exceção correta é levantada
