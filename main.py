from queue import Empty
import sys
from packet import Packet
import constants as cons
import time
from queue import Queue
from bot import Bot
from client import Client
from config_manager import ConfigManager


class Father:

	def __init__(self):
		self.queue_to_cli = Queue()
		self.queue_to_bot = Queue()
		self.queue_to_father = Queue()
		self.config = ConfigManager()
		self.cli = Client(self.config, self.queue_to_cli, self.queue_to_bot)
		self.bot = Bot(self.config, self.queue_to_cli, self.queue_to_bot, self.queue_to_father)
		self.bot_token = None
		self.api_id = None
		self.api_hash = None
		self.phone = None

	def run(self):
		def load_conf():
			print("Cargando conf father")
			conf_dict = self.config.conf_dict
			self.bot_token = conf_dict['bot_token']
			self.api_id = conf_dict['api_id']
			self.api_hash = conf_dict['api_hash']
			self.phone = conf_dict['phone']
			return True

		def queue_check():
			try:
				req = self.queue_to_father.get(True, cons.FATHER_QUEUE_POLL_TIMEOUT)
				print("Father receive: ", req)

				if req.request_code == cons.CLIENT_START:
					self.cli = Client(self.config, self.queue_to_cli, self.queue_to_bot)
					self.cli.start()
				elif req.request_code == cons.RELOAD_CONF:
					load_conf()
				elif req.request_code == cons.CLIENT_STATUS:
					req.reply_code = self.cli.is_alive()
					self.queue_to_bot.put(req)
				else:
					print("WARNING Father receives unkown code: ", req)
			except Empty:
				pass

		def threads_status():
			# is_cli_alive = self.cli.is_alive()
			is_bot_alive = self.bot.is_alive()
			# print("Cli: ", is_cli_alive, " Bot: ", is_bot_alive)

			# if is_cli_alive is False:
				# self.cli = Client(self.config, self.queue_to_cli, self.queue_to_bot)
				# self.cli.start()

			if is_bot_alive is False:
				self.bot = Bot(self.config, self.queue_to_cli, self.queue_to_bot, self.queue_to_father)
				self.bot.start()

		def client_launch():
			if self.api_id is None or self.api_hash is None or self.phone is None:
				error = "Hay parametros del cliente no configurados, revisalos:\nAPI_ID: "+str(self.api_id)\
				        +"\nAPI_HASH: "+str(self.api_hash)+"\nPhone: "+str(self.phone)\
						+"\nUsa /set_api_id, /set_api_hash o /set_phone y luego /client_launch"
				print(error)
				packet = Packet(cons.SEND_MSG, error)
				self.queue_to_bot.put(packet)
			elif self.cli.is_alive() is True:
				packet = Packet(cons.SEND_MSG, "El cliente YA estaba ejecutandose")
				self.queue_to_bot.put(packet)
			else:
				self.cli.start()


		#####################################################
		if __name__ == "__main__":
			print("Ejecutando Padre")
			self.config.load_config()
			load_conf()

			# Iniciar Bot & Client
			self.bot.start()
			client_launch()

			# Comunicacion & estados de hilos
			while True:
				queue_check()
				threads_status()


father = Father()
father.run()
