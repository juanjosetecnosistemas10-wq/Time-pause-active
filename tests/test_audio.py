import os
import tempfile
from pausa_activa.audio import AudioManager


def test_audio_manager_generar_wav() -> None:
    mgr = AudioManager()
    with tempfile.TemporaryDirectory() as d:
        path_rain = os.path.join(d, "rain.wav")
        path_nature = os.path.join(d, "nature.wav")
        
        # Test generating very short duration (1s) to keep tests fast
        mgr._generar_wav_lluvia(path_rain, duracion_seg=1)
        mgr._generar_wav_naturaleza(path_nature, duracion_seg=1)
        
        assert os.path.exists(path_rain)
        assert os.path.exists(path_nature)
        
        # Verify sizes are greater than 0
        assert os.path.getsize(path_rain) > 0
        assert os.path.getsize(path_nature) > 0
