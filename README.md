# ⏱ Pausas Activas

Timer de escritorio para pausas activas, con ventana emergente de ejercicios.

## Requisitos

- Python 3.8 o superior (tkinter incluido por defecto en Windows)

## Ejecutar directamente

```bash
python pausa_activa.py
```

## Empaquetar como .exe para Windows

1. Instala PyInstaller:
```bash
pip install pyinstaller
```

2. Genera el ejecutable:
```bash
pyinstaller --onefile --windowed --name "PausasActivas" pausa_activa.py
```

3. Encuentra tu `.exe` en la carpeta `dist/`

### Opciones adicionales (icono personalizado)
```bash
pyinstaller --onefile --windowed --icon=icono.ico --name "PausasActivas" pausa_activa.py
```

## Funcionalidades

- **Ventana principal** siempre visible: muestra la cuenta regresiva hasta la próxima pausa
- **Ventana emergente**: al llegar la pausa, muestra un ejercicio aleatorio con temporizador
- **8 ejercicios incluidos**: cuello, hombros, espalda, ojos, manos, sentadillas, respiración, caminar
- **Configuración guardada**: los ajustes se guardan en `config.json` junto al ejecutable
- **Botón "Pausa ya"**: activa una pausa inmediata
- **Botón Pausar/Reanudar**: congela el contador temporalmente

## Configuración

Desde la app (botón ⚙):
| Campo | Descripción | Por defecto |
|---|---|---|
| Intervalo | Minutos entre pausas | 45 min |
| Duración pausa | Cuánto dura cada pausa | 5 min |
| Hora inicio | No molesta antes de esta hora | 08:00 |
| Hora fin | No molesta después de esta hora | 18:00 |

## Autoarranque con Windows

Para que inicie con Windows, crea un acceso directo del `.exe` y colócalo en:
```
C:\Users\TU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```
