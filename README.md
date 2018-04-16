# teleAlert
Aplicación capaz de conectarse a una cuenta de Telegram, leer los mensajes que lleguen y notificar los más relevantes al usuario, omitiendo el resto.

Para ello se configurará el uso de una cuenta personal de Telegram, junto a unos canales a monitorizar y unas palabras clave a buscar dentro de los mensajes.

Esta app especialmente útil cuando estamos en canales con muchos mensajes diarios, de los cuáles solos nos interesen algunos, como canales de noticias, ofertas…etc. Nos permite silenciar los canales en nuestro cliente personal y dejar que el bot nos avise cuando haya algo relevante en el canal.


## 1. Metodología
Dado los objetivos anteriores, se han buscado librerías que cumplan con los objetivos y faciliten el desarrollo de la aplicación, encontrado las siguientes:
* **[Telethon](https://github.com/LonamiWebs/Telethon):** 
Librería desarrollada en Python 3 que implementa la [API cliente oficial](https://core.telegram.org/api#telegram-api) de Telegram.
Nos permitirá conectarnos a Telegram y gestionar todas las funciones del servicio de mensajería.

* **[pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI):**
Librería desarrollada en Python que implementa la [API oficial de Bots](https://core.telegram.org/bots/api) de Telegram 
Facilitará interactuar con la aplicación de manera semi-gráfica, facilitando la labor de configuración y control de esta. 

Dados los requisitos, necesitamos al menos dos procesos residentes, uno para la API cliente y otro para la API del Bot, a partir de ahora llamados cliente y bot.
Dichos procesos deberán responder en tiempo real a las peticiones del servicio Telegram, ya sea procesar la llegada de mensajes nuevos o atender una orden del usuario vía bot.

Una vez planteados los dos puntos anteriores, surge la necesidad de implementar una comunicación bot-cliente, que permita el paso de datos de uno a otro, como por ejemplo el cambio de parámetros que afecten al cliente, vía bot.

Para poder implementar esto, las clases cliente y bot serán hilos de una clase padre que se encargara de crearlos, comunicarlos y controlarlos.

Otro punto a tener en cuenta del diseño es la gestión persistente de la configuración; queremos que los parámetros y datos de uso de la aplicación se guarden en un fichero, modificable de forma transparente mediante la interfaz visual y el propio cliente.

Para ello crearemos una clase encargada de leer y guardar los parámetros en un fichero de texto visualmente legible.

## 2. Estructura y módulos
Descripción de los diferentes módulos en los que se divide el programa: 

**bot.py:**
Contendrá en un hilo el objeto de la API Bot, atenderá en tiempo real las peticiones que le lleguen a este, vía Telegram. Implementará los comandos de los que dispondrá y se comunicará con el cliente y el padre vía una cola de Python, principalmente recibirá mensajes de estos para enviárselos al usuario. La comunicación con el cliente se realizará en un sub hilo de la clase.

**channel_custom.py:**
Clase almacén para los canales de Telegram, almacenara de cada uno: id, access_hash, username, title y last_msg

**client.py:**
Ejecutará en un hilo el api cliente, obteniendo los parámetros necesarios para su funcionamiento de la clase config_manager, conectándose al servidor y recibiendo en tiempo real las actualizaciones de Telegram, filtrando los mensajes importantes.
También recibirá del bot una orden de recarga de la configuración, cuando el usuario modifique algún parámetro.

**config_manager.py:**
Lee el fichero de configuración predeterminado y guarda los parámetros en un diccionario de variables. Si el fichero de configuración no existe, o falta en él algún parámetro vital, los creará.
También provee un método para guardar variables cuando se solicite.

**constants.py:**
Fichero con las constantes que usará el programa, como los códigos de comunicación entre hilos.

**main.py:**
Invoca al config_manager, le ordena cargar la configuración. Crea las colas de cada hilo, crea los hilos y los ejecuta pasándoles la clase config_manager y las colas.
Después monitoriza el estado de los hilos y atiende peticiones del bot mediante su cola.

**packet.py:**
Clase almacén para la comunicación de los hilos mediante las colas. Contiene request_code (código/constante de la petición), request_data, reply_code(True/False) y reply_data.

## 3. Instalación & requisitos
Requisitos: 
* Python >= 3 instalado junto con pip()
* Cuenta de Telegram

Ejecutar en el terminal de Python:
* `$ pip install telethon`
* `$ pip install pyTelegramBotAPI`



1. Abrir un cliente de Telegram (móvil, pc o web), hablar a **[@BotFather](https://telegram.me/BotFather)**:

   1. Escribirle al bot `/start` y luego `/newbot`

   2. Ahora escribir el nombre del bot, NO debe empezar por ‘tele’ y debe acabar en ‘bot’, ni ser demasiado largo. **Recuerda este nombre**, porque con el podras encontrarlo luego

   3. Una vez hecho esto, nos dará el **token del bot** (un código de letras y números bastante largo), recordar que esta aquí para más adelante.

   4. Podemos configurar algunas opciones del bot creado con @BotFather, para ello: `/mybots`, pulsar el botón con el nombre de nuestro bot y luego pulsar en `“Edit Bot”`

   5. Nos aparecerán botones para cambiar nombre, descripción, imagen…Pulsamos `“Edit Commands”`

   6. Nos pedirá que introduzcamos la lista de comandos: 

      Los comandos que pongamos aquí aparecerán luego en un desplegable cuando interactuemos con el bot. No es obligatorio pero si recomendable.

      Por defecto nuestro bot tiene implementados los siguientes comandos (pegar párrafo en @BotFather):

      ````add_channel - Añadir un canal
      delete_channel - Borrar un canal
      add_keyword - Añadir una palabra clave
      delete_keyword - Borrar una palabra clave
      set_api_id - Introduce el api_id del cliente
      set_api_hash - Introduce el api_hash del cliente
      set_phone - Introduce el nº de tlf de la cuenta
      client_launch - Inicia el cliente
      client_status - Comprueba el estado del cliente

   7. Con esto hemos acabado con @BotFather

2. Abrimos el fichero de configuración, `config.ini` y editamos la línea:
   `bot_token = EL_TOKEN_DE_TU_BOT`
   Reemplazamos EL_TOKEN_DE_TU_BOT por el token que nos dio antes @BotFather, sin comillas, lo pegamos tal cual, algo parecido a esto:

   ![IMAGEN](https://github.com/darkvier/teleAlert/raw/master/imgs/Conf_mini.png)

3. Ahora ejecutamos el script main.py
   `python main.py`

## 4. Configuración

Una vez tenemos el bot configurado y ejecutándose, proseguimos la configuración desde la interfaz de este. 

Para ello abrimos un cliente de Telegram: móvil, pc o web y buscamos a nuestro recién creado bot, por ejemplo @NombreDeNuestroBot, abrimos una conversación y le damos a iniciar.
Debería indicarnos los siguientes pasos para configurar la aplicación:


1. Visitar https://my.telegram.org/auth
   1. Introducir el numero de teléfono y luego el código de verificación recibido en vuestro Telegram

2. Ir a [“API development tools”](https://my.telegram.org/apps):
   1. Ahí escribimos el titulo de nuestra “app cliente” (nos inventamos uno) , un nombre corto y le damos a guardar. Estos valores no tienen relevancia.

3. Cogemos el App `api_id` y el App `api_hash` y se lo damos al bot según nos lo pida

4. Después introducirnos nuestro `número de teléfono`, en formato +34 123 456 789

5. Ahora, al ser la primera vez que se ejecuta el cliente, Telegram nos enviara un código de verificación, debemos introducirlo en el bot **sumándole 1 al valor de ese código**.

6. Una vez hecho esto, si todo ha ido bien el cliente se ha iniciado y el bot nos lo notificara. Si no, nos mostrara un mensaje con el error.

   ![](https://raw.githubusercontent.com/darkvier/teleAlert/master/imgs/3.png)