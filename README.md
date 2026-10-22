# Game Manager

Una sola biblioteca para todos tus juegos de PC: **Steam, Epic Games, EA App, GOG, Xbox** y juegos sueltos de cualquier carpeta. App de escritorio para Windows hecha en Python.

<!-- Capturas: agregar en docs/screenshots/ y referenciarlas acá -->

## Funciones

- Detecta los juegos instalados de cada tienda leyendo sus datos locales (registro de Windows, manifiestos y carpetas de instalación).
- Importa la biblioteca completa de Steam iniciando sesión con Steam (OpenID, sin API key; el perfil debe ser público).
- Escanea carpetas propias y elige el ejecutable principal de cada juego.
- Busca las tapas automáticamente (CDN de Steam, API pública de GOG, catálogo local de EA y, como respaldo, el mismo juego en la tienda de Steam) y las guarda en caché.
- Lanza cada juego por su tienda cuando corresponde (por ejemplo `steam://` para que Steam maneje DRM y guardado en la nube).
- Búsqueda, filtros por tienda, tema claro/oscuro, español e inglés.
- Se minimiza a la bandeja del sistema, puede iniciar con Windows y avisa cuando hay una versión nueva en GitHub.

## Instalación

Descargá `GameManager_Setup_x.y.z.exe` desde [Releases](https://github.com/Souto751/game-manager/releases) y ejecutalo. Se instala para tu usuario (en `%LOCALAPPDATA%\Programs\Game Manager`), sin pedir permisos de administrador.

Tus datos (biblioteca, cuentas vinculadas, configuración y tapas) se guardan en `%APPDATA%\GameManager`: actualizar o desinstalar la app no los borra.

> **Si tenías la 1.0.0:** la biblioteca se copia sola a la nueva ubicación la primera vez que abrís la 1.1. La versión vieja (instalada en *Archivos de programa*) se puede desinstalar desde *Configuración → Aplicaciones*.

## Ejecutar desde el código

Requiere Python 3.10+ en Windows.

```bash
pip install -r requirements.txt
python main.py
```

## Compilar el instalador

```bash
build.bat
```

Genera `dist\GameManager\GameManager.exe` con PyInstaller y luego `installer_output\GameManager_Setup_<versión>.exe` (instalador propio en `installer_src/`, sin herramientas externas). También hay un script de Inno Setup (`installer.iss`) como alternativa.

La versión se define en un solo lugar: `version.py`.

## Estructura

| Carpeta | Qué contiene |
| --- | --- |
| `core/` | Lógica: biblioteca, lectores de cada tienda, tapas, rutas de datos, actualizaciones, bandeja |
| `ui/` | Interfaz con CustomTkinter: ventana principal, tarjetas, diálogos, textos ES/EN |
| `installer_src/` | Instalador gráfico autoextraíble |
| `assets/` | Ícono de la app |

## Cómo lo construí

Lo desarrollé con IA como copiloto: definí qué tiendas soportar y cómo debía comportarse la app, la IA implementó los lectores y la interfaz, y yo lo probé con mis propias bibliotecas, encontré los errores y decidí qué entraba en cada versión.

## Cambios

### 1.1.0
- Los datos pasan a `%APPDATA%\GameManager` (antes fallaba al guardar si la app estaba en *Archivos de programa*) con migración automática.
- Instalador por usuario, sin administrador. Ya no borra carpetas ajenas ni los datos al actualizar, y avisa si la app está abierta.
- Corregido: las tarjetas quedaban ocultas al cambiar de filtro después de hacer scroll.
- Corregido: los errores al detectar juegos dejaban el botón trabado en "Detectando…".
- Filtro de Xbox, tapas de GOG, tapas de Epic/EA que persisten entre sesiones y tapas sin deformar.
- Tapas para Epic, EA, GOG, Xbox y juegos propios buscando el mismo juego en la tienda de Steam (las APIs de Epic y Origin ya no responden).
- Ya no se importan herramientas que no son juegos (Steamworks Common Redistributables, EA Desktop, runtimes de Steam/Proton) y se quitan de bibliotecas existentes.
- Nuevo diseño de tarjetas: tapa de borde a borde con degradado, menú de opciones (abrir ubicación, quitar), placeholders mientras carga y carga mucho más rápida en bibliotecas grandes.
- Escaneo de carpetas tolerante a carpetas sin permisos; nombres con mayúsculas respetadas.
- Descarga de tapas limitada (mejor rendimiento con bibliotecas grandes) y actualizaciones de la interfaz siempre desde el hilo principal.
- El inicio de sesión de Steam se verifica con Steam.
- Ícono propio.

## Licencia

[MIT](LICENSE)
