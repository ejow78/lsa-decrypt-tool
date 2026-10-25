# LSA Decryption Tool — Manual de Uso

Herramienta para desencriptar, editar, balancear, cambiar sonidos y renombrar autos de **Assetto Corsa**.

---

## 1. Cómo abrir y desencriptar un auto
Tenés dos formas de cargar un auto:
1. **Arrastrar y soltar (lo más rápido):** Abrí `LSA Decryption Tool.exe` y arrastrá el archivo `data.acd` (o la carpeta entera del auto) directamente adentro del cuadro central de la ventana.
   - Al soltarlo, la herramienta **desencripta automáticamente** todos los archivos dentro de la carpeta `data/` del auto y crea una copia de seguridad (`data.acd.bak`).
2. **Con los botones superiores:** Tocá **Buscar Carpeta...** o **Buscar data.acd...**, elegí el auto y presioná **Desencriptar data.acd**.

> **Nota importante sobre Assetto Corsa:** El juego siempre lee el archivo `data.acd` si está presente en la carpeta del auto. Por eso, cada vez que termines de hacer cambios en los archivos de `data/`, debés empaquetarlos de nuevo en `data.acd`.

---

## 2. Diferencia entre los botones de guardado y empaquetado

En la barra superior tenés dos botones parecidos que cumplen funciones distintas:

* **Guardar y Re-empaquetar (Recomendado si editás adentro del programa):**
  Hace todo en **1 solo paso**: primero guarda en la carpeta `data/` el texto del archivo `.ini` o `.lut` que estés editando en el panel derecho de la herramienta, y enseguida vuelve a encriptar toda la carpeta `data/` adentro de `data.acd`.
* **Empaquetar data.acd (Para cuando editás afuera con Bloc de Notas / VS Code):**
  Toma los archivos tal como están guardados en ese momento dentro de la carpeta `data/` en el disco y los empaqueta en `data.acd` (no guarda cambios sin guardar del cuadro de texto de la derecha).
* **Guardar Backup:**
  Crea una carpeta `backup_data/` dentro del auto con una copia intacta de `data.acd` y de toda la carpeta `data/` por si querés volver atrás en cualquier momento.

---

## 3. Guía de las 3 Pestañas

### Pestaña 1: Archivos y Editor
* **Lista izquierda (`Archivos en data/`):** Buscá cualquier archivo (ej. `car.ini`, `engine.ini`, `aero.ini`, `tyres.ini`, `torque.lut`) y hacele clic para abrirlo.
* **Panel derecho (`Editor Rapido`):** Mientras no haya ningún archivo seleccionado, el cuadro está bloqueado para evitar escrituras accidentales. Al seleccionar un archivo de la izquierda se habilita la edición.
* Cuando termines de modificar un valor, tocá **Guardar y Re-empaquetar** arriba.

### Pestaña 2: Balance
Ideal para nivelar el rendimiento entre distintos autos sin tener que calcular curvas a mano:
* **Respaldo de Seguridad (arriba):** Tocá **Guardar Backup de Fisicas** antes de tocar nada. Si algo no te gusta cómo quedó en pista, tocás **Restaurar Backup de Fisicas** y vuelve todo al estado original.
* **Balance de Motor y Peso (izquierda):**
  - Te muestra arriba cuántos **Nm de Torque** y **CV / kW de Potencia Máxima** tiene el auto actualmente.
  - Podés cambiar el **Peso Total (kg)**, poner directamente la **Potencia Máxima deseada en CV** (el programa reescala toda la curva `torque.lut` / `force.lut` automáticamente), cambiar el **Limitador de RPM** y la **Presión del Turbo (bar)**.
  - Dejá marcada la opción *"Si cambio las RPM, reescalar curvas y relacion final"* para que al bajar o subir las RPM no se corte el sonido del motor ni fallen las luces del volante.
  - Tocá **Aplicar Balance y Re-empaquetar**.
* **Sistema Híbrido / ERS (derecha — para Hypercars LMH / LMDh):**
  - Permite cambiar el **Modo Activo** (ej. `MEDIUM`), el **Torque Eléctrico Máximo (Nm)**, la **Recarga en frenada**, el **Tiempo de descarga por vuelta** y el rango de velocidades (`km/h`) en el que empuja el motor eléctrico (ej. `190` a `325 km/h`).
  - **Botón "Instalar Hibrido Hypercar WEC (Modo MEDIUM)":** Si tenés un Hypercar sin sistema híbrido o con un híbrido mal configurado, este botón le instala un sistema híbrido WEC completo y balanceado en modo `MEDIUM` adaptado automáticamente a las RPM de tu auto.

### Pestaña 3: Sonido y Renombrar Auto
* **Cambiar Sonido del Auto (Sound Swapper — izquierda):**
  1. Con tu auto cargado arriba, tocá **Buscar Auto...** (o **Buscar .bank...**) en la sección de *Auto Donante* y elegí el auto del cual querés copiar el sonido.
  2. Tocá **Aplicar Sonido del Donante al Auto Actual**.
  3. El programa guarda un backup de tu sonido original en `sfx_backup/`, copia el `.bank` nuevo con el nombre de tu auto y adapta automáticamente todas las rutas internas del archivo `GUIDs.txt`.
  4. Si querés volver al sonido viejo, tocá **Restaurar Sonido Original (desde sfx_backup)**.
* **Renombrar Carpeta de Auto (derecha):**
  - En Assetto Corsa, si le cambiás el nombre a la carpeta de un auto desde Windows, el `data.acd` y el sonido dejan de andar porque la clave de encriptación se calcula con el nombre de la carpeta.
  - Escribí el **Nuevo nombre** en este panel y tocá **Renombrar Auto y Re-empaquetar data.acd**: el programa renombra la carpeta, adapta el `.bank` y el `GUIDs.txt` al nombre nuevo, y vuelve a encriptar el `data.acd` con la clave nueva.

---
*Ante cualquier duda o error, contactar en Discord: **lancool***
