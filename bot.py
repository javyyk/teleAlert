import traceback
from ast import literal_eval as make_tuple
from queue import Empty
from threading import Thread

import re
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import constants as cons
from packet import Packet


class Bot(Thread):

	def __init__(self, config, queue_to_cli, queue_to_bot, queue_to_father):
		Thread.__init__(self)
		self.config = config
		self.queue_to_bot = queue_to_bot
		self.queue_to_cli = queue_to_cli
		self.queue_to_father = queue_to_father
		self.bot_token = None
		self.api_id = None
		self.api_hash = None
		self.user_id = None
		self.channels = None
		self.keywords = None
		self.msg_chat_id_fake = None

	def run(self):
		def load_conf():
			print("Cargando conf bot")
			conf_dict = self.config.conf_dict
			self.bot_token = conf_dict['bot_token']
			self.api_id = conf_dict['api_id']
			self.api_hash = conf_dict['api_hash']
			self.user_id = conf_dict['user_id']
			self.channels = conf_dict['channels']
			self.keywords = conf_dict['keywords']
			return True


		# Solicita al cliente que recargue la conf
		# TODO comentarios metodos
		def reload_conf_req():
			try:
				request = Packet(cons.RELOAD_CONF, None)
				self.queue_to_cli.put(request)

				# Espera bloqueante del cliente
				try:
					# TODO obsoleto
					reply = self.queue_to_bot.get(True, 5)

					if reply.reply_code is False:
						print("reload conf true")
					# Devolver motivo del error
				# bot.send_message(msg.chat.id, reply.reply_data)
				# bot.register_next_step_handler(msg, process_channel_id)

				except Empty:
					# bot.send_message(msg.chat.id, "El bot se ha cansado de esperar a Client")
					print("Bot: resp no recibida 1")

			except Exception as e:
				print("Excepcion:", e)
				bot.send_message(self.user_id, "Algo ha fallado...")

		# Verifica que solo el usuario autorizado accede al bot
		def check_user_auth(user_id):
			if self.user_id is None:
				# Guardar el id del usuario
				self.user_id = user_id
				success = self.config.save_var("Data", "user_id", self.user_id)
				if success:
					print("## user_id guardado ##")
					load_conf()
				else:
					print("oops! algo ha ido mal check_user()")

				return True
			else:
				# Verificar id usuario
				if self.user_id == user_id:
					return True
				else:
					print("Acceso no autorizado al bot")
					bot.send_message(user_id, "No estas autorizado a usar el bot")
					return False

		# Crear msg.chat.id para posteriores peticiones de datos
		def save_chat_id_fake(id):
			self.msg_chat_id_fake = type('message_tmp', (object,), {
				'chat': type('chat', (object,),{'id': id})(),
			    'procesar': False})()

		#################################################
		#                    EJECUCION BOT              #
		#################################################
		print("Ejecutando Bot")
		load_conf()

		bot = TeleBot(self.bot_token, threaded=True, skip_pending=True)


		if self.user_id:
			# bot.send_message(self.user_id, "Bot iniciado", disable_notification=True)
			save_chat_id_fake(self.user_id)




		@bot.message_handler(commands=['start'])
		def start(msg):
			if not check_user_auth(msg.chat.id):
				return

			save_chat_id_fake(msg.chat.id)

			username = msg.from_user.username
			bot.send_message(msg.chat.id, "Bienvenido a telegramo @" + username)
			bot.send_message(msg.chat.id, "En los siguientes pasos vamos a configurar la aplicacion.")
			bot.send_message(msg.chat.id, "Si algun parametro no se configura bien, puedes volver a hacerlo con:\n"
			                              "/set_api_id\n/set_api_hash\n/set_phone")
			bot.send_message(msg.chat.id, "Para ejecutar el cliente manualmente: /client_launch")


			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Introduce el API_ID:", reply_markup=markup)
			bot.register_next_step_handler(msg, process_api_id)

		def process_api_id(msg):
			api_id = msg.text

			self.config.save_var("Config", "api_id", api_id)

			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Ahora introduce el API_HASH:", reply_markup=markup)
			bot.register_next_step_handler(msg, process_api_hash)

		def process_api_hash(msg):
			api_hash = msg.text

			self.config.save_var("Config", "api_hash", api_hash)

			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Ahora introduce tu numero de telefono (+34 123 456 789): ", reply_markup=markup)
			bot.register_next_step_handler(msg, process_phone)

		def process_phone(msg):
			phone = msg.text
			self.config.save_var("Config", "phone", phone)
			bot.send_message(msg.chat.id, "Vamos a intentar lanzar el cliente con los datos facilitados...")
			request = Packet(cons.CLIENT_START, None)
			self.queue_to_father.put(request)



		@bot.message_handler(commands=['add_channel'])
		def add_channel(msg):
			if not check_user_auth(msg.chat.id):
				return

			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Para añadir un canal, introduce su id", reply_markup=markup)
			bot.register_next_step_handler(msg, process_add_channel_id)

		def process_add_channel_id(msg):
			id_channel = msg.text

			try:
				request = Packet(cons.ADD_CHANNEL, id_channel)
				self.queue_to_cli.put(request)

			except Exception as e:
				print("Excepcion 1:", e)
				print(traceback.format_exc())
				bot.send_message(msg.chat.id, "Algo ha fallado...")


		@bot.message_handler(commands=['delete_channel'])
		def delete_channel(msg):
			if not check_user_auth(msg.chat.id):
				return

			if len(self.channels) == 0:
				bot.send_message(msg.chat.id, "No hay canales guardados")
				return

			markup = InlineKeyboardMarkup()
			for channel in self.channels:
				markup.add(InlineKeyboardButton(channel.title, callback_data=str((
					cons.DELETE_CHANNEL, channel.id, channel.title))))

			bot.send_message(msg.chat.id, "Elige el canal a borrar", reply_markup=markup)

		@bot.message_handler(commands=['add_keyword'])
		def add_keyword(msg):
			if not check_user_auth(msg.chat.id):
				return

			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Para añadir una palabra clave, introducela", reply_markup=markup)
			bot.register_next_step_handler(msg, process_add_keyword)

		def process_add_keyword(msg):
			# TODO filtrar caracteres
			regex = re.compile(r"(;)+", re.IGNORECASE)
			keyword = re.sub(regex, '', msg.text)

			# Ya existe en la conf?
			exists = False
			for k in self.keywords:
				if k == keyword:
					exists = True

			if exists:
				bot.send_message(msg.chat.id, "La palabra clave ya estaba guardada")
			else:
				self.keywords.append(keyword)
				success = self.config.save_var("Config", "keywords", self.keywords)

				if success is True:
					bot.send_message(msg.chat.id, "Se ha añadido la palabra clave: " + keyword)
					load_conf()
					reload_conf_req()
				else:
					bot.send_message(msg.chat.id, "Error al guardar el fichero de conf")

		@bot.message_handler(commands=['delete_keyword'])
		def delete_keyword(msg):
			if not check_user_auth(msg.chat.id):
				return

			if len(self.keywords) == 0:
				bot.send_message(msg.chat.id, "No hay palabras clave guardadas")
				return

			markup = InlineKeyboardMarkup()
			for key in self.keywords:
				markup.add(InlineKeyboardButton(key, callback_data=str((
					cons.DELETE_KEYWORD, key))))

			bot.send_message(msg.chat.id, "Elige la palabra a borrar", reply_markup=markup)


		@bot.message_handler(commands=['set_api_id'])
		def set_api_id(msg):
			if not check_user_auth(msg.chat.id):
				return
			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Introduce el API_ID:", reply_markup=markup)
			bot.register_next_step_handler(msg, set_api_id_procesar)

		def set_api_id_procesar(msg):
			if not check_user_auth(msg.chat.id):
				return
			api_id = msg.text
			success = self.config.save_var("Config", "api_id", api_id)

			if not success:
				bot.send_message(msg.chat.id, "Error al guardar el parametro")


		@bot.message_handler(commands=['set_api_hash'])
		def set_api_hash(msg):
			if not check_user_auth(msg.chat.id):
				return

			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Introduce el API_HASH:", reply_markup=markup)
			bot.register_next_step_handler(msg, set_api_hash_procesar)

		def set_api_hash_procesar(msg):
			if not check_user_auth(msg.chat.id):
				return
			api_hash = msg.text
			success = self.config.save_var("Config", "api_hash", api_hash)

			if not success:
				bot.send_message(msg.chat.id, "Error al guardar el parametro")


		@bot.message_handler(commands=['set_phone'])
		def set_phone(msg):
			if not check_user_auth(msg.chat.id):
				return

			markup = types.ForceReply(selective=False)
			bot.send_message(msg.chat.id, "Introduce el numero de telefono (+34 123 456 789):", reply_markup=markup)
			bot.register_next_step_handler(msg, set_phone_procesar)

		def set_phone_procesar(msg):
			if not check_user_auth(msg.chat.id):
				return
			phone = msg.text
			success = self.config.save_var("Config", "phone", phone)

			if not success:
				bot.send_message(msg.chat.id, "Error al guardar el parametro")


		@bot.message_handler(commands=['client_launch'])
		def client_launch(msg):
			if not check_user_auth(msg.chat.id):
				return

			request = Packet(cons.CLIENT_START, None)
			self.queue_to_father.put(request)

		@bot.message_handler(commands=['client_status'])
		def client_status(msg):
			if not check_user_auth(msg.chat.id):
				return

			request = Packet(cons.CLIENT_STATUS, None)
			self.queue_to_father.put(request)




		# Maneja los clicks de botones
		@bot.callback_query_handler(func=lambda call: True)
		def callback(call):
			# print(call)
			chat_id = call.from_user.id
			if not check_user_auth(chat_id):
				return

			resp = make_tuple(call.data)
			code = resp[0]

			if code == cons.DELETE_CHANNEL:
				channel_id = resp[1]
				channel_title = resp[2]

				self.channels = [ch_conf for ch_conf in self.channels if ch_conf.id != channel_id]

				success = self.config.save_var("Config", "channels", self.channels)
				if success is True:
					bot.send_message(chat_id, channel_title + " borrado correctamente")
					load_conf()
					reload_conf_req()

				else:
					bot.send_message(chat_id, "Error al borrar el canal")

			elif code == cons.DELETE_KEYWORD:
				key = resp[1]

				self.keywords = [x for x in self.keywords if x != key]

				success = self.config.save_var("Config", "keywords", self.keywords)
				if success is True:
					bot.send_message(chat_id, key + ": borrada correctamente")
					load_conf()
					reload_conf_req()

				else:
					bot.send_message(chat_id, "Error al borrar la palabra")


		def add_channel(req):

			# Canal valido
			if req.reply_code is True:
				channel = req.reply_data

				# Ya existe en la conf?
				exists = False
				for ch in self.channels:
					if ch[0] == channel.id:
						exists = True

				if exists:
					bot.send_message(self.user_id, "El canal ya estaba guardado")
				else:
					channel_new = (channel.id, channel.title)
					self.channels.append(channel_new)
					success = self.config.save_var("Config", "channels", self.channels)
					if success is True:
						bot.send_message(self.user_id, "Se ha añadido el canal: " + channel.title)
						load_conf()
						reload_conf_req()
					else:
						bot.send_message(self.user_id, "Error al guardar el fichero de conf")
			# Canal invalido
			else:
				# Devolver motivo del error
				bot.send_message(self.user_id, req.reply_data)

		def ask_user_tl_code():
			markup = types.ForceReply(selective=False)
			bot.send_message(self.user_id, "Introduce el codigo de autenticacion recibido de "
			                               "telegram via sms/telegram app, sumandole 1 al número:", reply_markup=markup)
			bot.register_next_step_handler(self.msg_chat_id_fake, ask_user_tl_code_procesar)


		def ask_user_tl_code_procesar(msg):
			if not check_user_auth(msg.chat.id):
				return
			try:
				# Para evitar que tl nos invalide el codigo de autorizacion:
				code = int(msg.text) - 1
				req = Packet(cons.ASK_TL_AUTH_CODE_REPLY, code)
				self.queue_to_cli.put(req)
			except Exception:
				# TODO especificar except
				bot.send_message(self.user_id, "El codigo introducido es invalido")

		def queue_check():
			while True:
				try:
					req = self.queue_to_bot.get(block=True, timeout=cons.BOT_QUEUE_POLL_TIMEOUT)

					if req.request_code == cons.CHANNEL_EXISTS:
						add_channel(req)

					elif req.request_code == cons.RELOAD_CONF:
						load_conf()
						req.reply_code = True
						self.queue_to_cli.put(req)

					elif req.request_code == cons.ADD_CHANNEL:
						bot.send_message(self.user_id, req.reply_data)

					elif req.request_code == cons.SEND_MSG:
						if self.user_id is not None:
							bot.send_message(self.user_id, req.request_data)
						else:
							print("WARNING: Se ha intentado enviar msg al user sin setear user_id antes")

					elif req.request_code == cons.ASK_TL_AUTH_CODE:
						ask_user_tl_code()

					elif req.request_code == cons.CLIENT_STATUS:
						if req.reply_code is True:
							bot.send_message(self.user_id, "El cliente esta ejecutandose")
						else:
							bot.send_message(self.user_id, "El cliente esta detenido")

					else:
						print("WARNING Bot receives unkown code: ", req)

				except Empty:
					pass


		thread_queue = Thread(target=queue_check)
		thread_queue.daemon = True
		thread_queue.start()

		# Bucle polling updates telegram
		while True:
			try:
				#bot.polling(none_stop=True, interval=3, timeout=5)
				bot.polling()
			except Exception:
				print("Bot: error polling tl updates")
