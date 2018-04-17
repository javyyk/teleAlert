CHANNEL_EXISTS = 500
DELETE_CHANNEL = 502
ADD_KEYWORD = 504
DELETE_KEYWORD = 506
RELOAD_CONF = 508
CLIENT_START = 510
CLIENT_STATUS = 512
ADD_CHANNEL = 514
SEND_MSG = 516
ASK_TL_AUTH_CODE = 518
ASK_TL_AUTH_CODE_REPLY = 519

# Tiempo de espera a que el usuario meta el codigo de verificacion de Telegram
AUTH_CODE_TIMEOUT = 120

# Nº max de mensajes anteriores/omitidos que se muestran al arrancar
OFFLINE_MAX_MSG_RETRIEVE_PER_CHANNEL = 10

# Antiguedad maxima de los mensajes anteriores/omitidos a mostrar en horas
OFFLINE_MAX_HOUR_RETRIEVE = 24

# Tiempo que el cliente esperara un update de Telegram en seg
CLIENT_TL_POLL_TIMEOUT = 2

# Tiempo que el bot esperara un msg de su cola en seg
BOT_QUEUE_POLL_TIMEOUT = 2

# Tiempo que el bot esperara un msg de su cola en seg
FATHER_QUEUE_POLL_TIMEOUT = 2

CONF_FILE_NAME = "config.ini"
BOT_TOKEN_DEFAULT = "EL_TOKEN_DE_TU_BOT"
