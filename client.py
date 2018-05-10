import datetime
import re
import sys
import telethon
import time
from telethon import TelegramClient, events
from telethon.errors.rpc_error_list import UsernameNotOccupiedError, ApiIdInvalidError, PhoneNumberInvalidError
from telethon.tl.functions.channels import JoinChannelRequest, GetChannelsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel, UpdateNewChannelMessage, User, MessageService, Message

from threading import Thread
from queue import Empty
from packet import Packet
from channel_custom import ChannelCustom
import constants as cons
import logging


class Client(Thread):

	def __init__(self, config, queue_to_cli, queue_to_bot):
		Thread.__init__(self)
		self.config = config
		self.queue_to_cli = queue_to_cli
		self.queue_to_bot = queue_to_bot
		self.bot_token = None
		self.api_id = None
		self.api_hash = None
		self.phone = None
		self.user_id = None
		self.channels = None
		self.keywords = None
		self.client = None

	def run(self):
		def load_conf():
			print("Cargando conf cliente")
			conf_dict = self.config.conf_dict
			self.bot_token = conf_dict['bot_token']
			self.api_id = conf_dict['api_id']
			self.api_hash = conf_dict['api_hash']
			self.phone = conf_dict['phone']
			self.channels = conf_dict['channels']
			self.keywords = conf_dict['keywords']
			return True


		# Solicita al cliente que recargue la conf
		def reload_conf_req():
			load_conf()
			try:
				req = Packet(cons.RELOAD_CONF, None)
				self.queue_to_bot.put(req)

				# Espera bloqueante del cliente
				try:
					reply = self.queue_to_bot.get(True, 5)

					if reply.reply_code is False:
						print("Cli: reload_conf_req")

				except Empty:
					print("Cli: reload_conf_req")

			except Exception as e:
				print("Excepcion:", e)

		def queue_check():
			while True:
				try:
					req = self.queue_to_cli.get(block=True)
					print("Cli receive: ", req)

					if req.request_code == cons.ADD_CHANNEL:
						add_channel(req)
					elif req.request_code == cons.RELOAD_CONF:
						load_conf()


				except Empty:
					pass

		def bot_send_msg(text):
			packet = Packet(cons.SEND_MSG, text)
			self.queue_to_bot.put(packet)
			time.sleep(1)  # Evitar floodwait exception

		def channel_exists(id_channel):
			try:
				# channel = self.client(ResolveUsernameRequest(username=id_channel))
				tl_channel = self.client.get_entity(id_channel)
				return tl_channel
			except UsernameNotOccupiedError as e:
				print("check_channel: '" + id_channel + "' no existe")
				return None
			except Exception as e:
				print("Error channel_exists: ", e)
				return None

		def add_channel(req):
			# ID, alias o url

			tl_channel = channel_exists(req.request_data)

			if tl_channel is None:
				req.reply_code = False
				req.reply_data = "El canal no existe"
			elif type(tl_channel) == telethon.tl.types.User:
				req.reply_code = False
				req.reply_data = "El ID se corresponde al de un usuario. " \
				                 "Los chats de usuario no estan soportados"
			else:

				# Ya existe en la conf?
				exists = False
				for ch in self.channels:
					if ch.id == tl_channel.id:
						exists = True

				if exists:
					req.reply_code = False
					req.reply_data = "El canal ya estaba guardado"
				else:
					try:
						channel_info = self.client(GetChannelsRequest([tl_channel]))
						if channel_info.chats[0].left is True:
							join_result = self.client(JoinChannelRequest(tl_channel))
							req.reply_code = True
							req.reply_data = "Te has unido al canal: " + tl_channel.title
							self.queue_to_bot.put(req)

					except Exception as e:
						req.reply_code = False
						req.reply_data = "Error al unirse al canal " + tl_channel.title
						self.queue_to_bot.put(req)
						print(req.reply_data)
						print(e)
						return False

					channel_custom = ChannelCustom(tl_channel.id, tl_channel.access_hash, tl_channel.username,
					                               tl_channel.title)

					self.channels.append(channel_custom)
					success = self.config.save_var("Config", "channels", self.channels)

					if success is True:
						req.reply_code = True
						req.reply_data = "Se ha añadido el canal: " + tl_channel.title
						reload_conf_req()
					else:
						req.reply_code = False
						req.reply_data = "Error al guardar el fichero de conf"

			self.queue_to_bot.put(req)


		def filter_tl_update(update):
			#print("Cli tl update:", update)
			# UpdateNewChannelMessage(message=Message (out=False, mentioned=False, media_unread=False, silent=False, post=True, id=1052, from_id=None, to_id=PeerChannel(channel_id=1263221050), fwd_from=None, via_bot_id=None, reply_to_msg_id=None, date=datetime.utcfromtimestamp(1523628439), message='Fri Apr 13 18:07:17 2018 YES!', media=None, reply_markup=None, entities=[], views=1, edit_date=None, post_author=None, grouped_id=None), pts=1053, pts_count=1)

			if type(update) is not UpdateNewChannelMessage:
				return

			from_channel_id = update.message.to_id.channel_id
			message = update.message.message

			channel_match = False
			for ch in self.channels:
				if ch.id == from_channel_id:
					channel_match = True
					ch.last_msg = update.message.id
					self.config.save_var("Config", "channels", self.channels)
					break

			if channel_match:
				check_msg_match(message)

		def check_msg_match(msg):
			for keyword in self.keywords:

				pattern = re.compile(keyword, re.IGNORECASE)
				msg_match = pattern.search(msg)

				if msg_match:
					# Telegram BOT API message
					bot_send_msg(msg)
					print("Cli: message match -> send to bot ("+msg[0:10]+")")
					break



		#################################################
		#                 EJECUCION CLIENTE             #
		#################################################
		print("\n\n", __file__, ": ", time.strftime("%Y-%m-%d %H:%M"), "\n")
		print("Ejecutando Client")
		load_conf()


		# Conectamos la API cliente
		self.client = TelegramClient('client', self.api_id, self.api_hash, update_workers=1)
		self.client.connect()

		# Comprobamos si tenemos autorizacion o solicitamos el codigo a tl y al user
		try:
			if not self.client.is_user_authorized():
				self.client.send_code_request(self.phone)

				request = Packet(cons.ASK_TL_AUTH_CODE, None)
				self.queue_to_bot.put(request)

				try:
					req = self.queue_to_cli.get(block=True, timeout=cons.AUTH_CODE_TIMEOUT)
					if req.request_code is cons.ASK_TL_AUTH_CODE_REPLY:
						self.client.sign_in(phone=self.phone, code=req.request_data)

				except Empty:
					error = "Client: Codigo autorizacion telegram no recibido, terminando cliente"
					print("WARNING: " + error)
					bot_send_msg(error)
					sys.exit()

		except ApiIdInvalidError as err:
			print("WARNING Client: API_ID/API_HASH invalidas")
			print(err)
			bot_send_msg("Error de configuracion del cliente: API_ID/API_HASH invalidas."
			                                "\nRevisa la configuracion y vuelve a lanzar el cliente /client_launch")
			sys.exit()

		except PhoneNumberInvalidError as err:
			print("WARNING Client: Numero de telefono (Phone) invalido")
			print(err)
			bot_send_msg("Error de configuracion del cliente: Numero de telefono (Phone) invalido."
			                                "\nRevisa la configuracion y vuelve a lanzar el cliente /client_launch")
			sys.exit()

		except Exception as err:
			error = "Cliente: "+str(err)
			print("WARNING ", error, type(err))
			bot_send_msg(error)
			sys.exit()


		# Hacer consulta a tl para verificar inicio correcto
		try:
			if type(self.client.get_me()) is not User:
				raise Exception

			bot_send_msg("Cliente iniciado con éxito")

		except Exception as err:
			error = "Cliente: error al iniciar cliente.\n"+str(err)
			print("WARNING error al iniciar cliente.\n", error, type(err))
			bot_send_msg(error)
			sys.exit()


		# Comprobar que el cliente esta unido a los canales guardados
		for channel in self.channels:
			try:
				ch = InputPeerChannel(channel.id, channel.access_hash)
				self.client(JoinChannelRequest(ch))
			except Exception as e:
				print("Warning JoinChannelRequest:", e)
				bot_send_msg("Error al unirse al canal "+channel.title)


		# Revisar mensajes omitidos si la app ha estado apagada
		for ch in self.channels:

			print("Solicitando mensajes antiguos del canal", ch.title)
			print("Msg min_id: ", ch.last_msg)

			date_now = datetime.datetime.now()
			date_old = date_now - datetime.timedelta(hours=cons.OFFLINE_MAX_HOUR_RETRIEVE)
			try:
				query = self.client(GetHistoryRequest(
					peer=InputPeerChannel(ch.id, ch.access_hash),
					limit=cons.OFFLINE_MAX_MSG_RETRIEVE_PER_CHANNEL,  # Max number of msg get from channel
					offset_date=date_old,  # Only msgs in last 24h
					add_offset=0,
					offset_id=0,
					max_id=0,
					min_id=ch.last_msg,  # Only request msg no procesados
					hash=0
				))

				# Una vez tenemos los mensajes nuevos, analizarlos
				messages = query.messages
				for msg in messages:
					if type(msg) is Message:
						# print(msg)
						check_msg_match(msg.message)
					else:
						print("Warning Cli: unkown msg type", type(msg), msg)

				# Guardar el id del ultimo mensaje procesado
				if messages:
					ch.last_msg = messages[0].id
					self.config.save_var("Config", "channels", self.channels)
			except Exception as err:
				error = "Cliente: " + str(err)
				print("WARNING ", error, type(err))
				bot_send_msg(error)



		thread_queue = Thread(target=queue_check)
		thread_queue.daemon = True
		thread_queue.start()






		# Bucle polling updates telegram & threads queue
		while True:
			try:
				tl_update = self.client.updates.poll()
				filter_tl_update(tl_update)

			except KeyboardInterrupt:
				break
			except Exception as e:
				print("Error: ", e)

		self.client.disconnect()
