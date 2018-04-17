from channel_custom import ChannelCustom
import configparser  # config file manager
import os
import sys
from threading import Lock
import constants as cons


class BotTokenError(Exception):
	def __init__(self):
		pass


class ConfigManager:

	def __init__(self):
		path = os.path.dirname(os.path.abspath(__file__))
		self.conf_file = path + "/" + cons.CONF_FILE_NAME

		self.config = configparser.ConfigParser()

		self.conf_dict = None

	def save_var(self, section, name, value):

		if not self.config.has_section(section):
			self.config.add_section(section)

		try:
			if type(value) is list:

				# Para los channel -> lista[tupla1(), ...]
				if len(value) != 0 and type(value[0]) is ChannelCustom:
					lis = []
					for channel in value:
						lis.append(channel.to_save())
					list_str = ';'.join(lis)

				# Para las listas de str & int
				else:
					list_str = ';'.join(value)

				self.config[section][name] = list_str

			else:
				self.config[section][name] = str(value)

			with open(self.conf_file, 'w') as configfile:
				self.config.write(configfile)

			# Añadir al dicc en memoria
			par = {name: value}
			self.conf_dict.update(par)
			return True
		except Exception as e:
			print("Error al guardar la variable: "+name+" con valor: "+str(value))
			print(e)
			return False


	def load_var(self, section, name):
		self.config.read(self.conf_file)
		if self.config.has_option(section, name):
			return self.config.get(section, name)
		else:
			return None


	def load_config(self):
		lock = Lock()
		lock.acquire()
		try:
			print("Acquired config lock")
			self.config.read(self.conf_file)
			conf_dict = {}
			success = True

			# CONFIG SECTION
			if not self.config.has_section("Config"):
				self.config.add_section("Config")

			if not self.config.has_section("Data"):
				self.config.add_section("Data")



			# BOT_API_ID
			if self.config.has_option("Config", "bot_token"):
				if self.config.get('Config', "bot_token") == cons.BOT_TOKEN_DEFAULT:
					success = False
				else:
					par = {"bot_token": self.config.get('Config', "bot_token")}
					conf_dict.update(par)
			else:
				self.config['Config']["bot_token"] = cons.BOT_TOKEN_DEFAULT
				success = False

			# API_ID
			try:
				if not self.config.has_option("Config", "api_id"):
					raise Exception("Vacio")

				api_id = self.config.get('Config', "api_id")
				if api_id == "None" or api_id == "":
					raise Exception("Vacio")
				else:
					api_id = int(api_id)

			except Exception as e:
				print("Warning al cargar la configuracion 'api_id' (first run?)")
				self.config['Config']["api_id"] = "None"
				api_id = None

			# Añadir al diccionario
			par = {"api_id": api_id}
			conf_dict.update(par)


			# API_HASH
			if self.config.has_option("Config", "api_hash"):
				par = {"api_hash": self.config.get('Config', "api_hash")}
			else:
				par = {"api_hash": None}
				print("Warning: api_hash not found (first run?)")
			conf_dict.update(par)

			# PHONE
			if self.config.has_option("Config", "phone"):
				par = {"phone": self.config.get('Config', "phone")}
			else:
				par = {"phone": None}
				print("Warning: phone not found (first run?)")
			conf_dict.update(par)



			# CHANNELS
			try:
				if not self.config.has_option("Config", "channels"):
					raise Exception("Vacio")

				channels = self.config.get('Config', "channels")
				if channels == "None" or channels == "":
					raise Exception("Vacio")

				channels_str = channels.split(";")
				channels = []
				for ch_str in channels_str:
					props = ch_str.split(", ")
					channels.append(ChannelCustom(int(props[0]), int(props[1]), props[2], props[3], int(props[4])))

			except Exception as e:
				print("Warning al cargar la configuracion 'channels' (first run?)", e)
				self.config['Config']["channels"] = "None"
				channels = []

			# Añadir al diccionario
			par = {"channels": channels}
			conf_dict.update(par)



			# KEYWORDS
			try:
				if not self.config.has_option("Config", "keywords"):
					raise Exception("Vacio")

				keywords = self.config.get('Config', "keywords")
				if keywords == "None" or keywords == "":
					raise Exception("Vacio")

				keywords = keywords.split(";")
			except Exception as e:
				print("Warning al cargar la configuracion 'keywords' (first run?)")
				self.config['Config']["keywords"] = "None"
				keywords = []

			# Añadir al diccionario
			par = {"keywords": keywords}
			conf_dict.update(par)


			# USER_ID
			try:
				if not self.config.has_option("Data", "user_id"):
					raise Exception("Vacio")

				user_id = self.config.get('Data', "user_id")
				if user_id == "None" or keywords == "":
					raise Exception("Vacio")
				else:
					user_id = int(user_id)

			except Exception as e:
				print("Warning al cargar la configuracion 'user_id' (first run?)")
				self.config['Data']["user_id"] = "None"
				user_id = None

			# Añadir al diccionario
			par = {"user_id": user_id}
			conf_dict.update(par)


			# Error al cargar conf, escribir variables default y salir
			if success is False:
				with open(cons.CONF_FILE_NAME, 'w') as cfgfile:
					self.config.write(cfgfile)
				raise BotTokenError()
			else:
				print("Configuración cargada correctamente")
				print(conf_dict)
				with open(cons.CONF_FILE_NAME, 'w') as cfgfile:
					self.config.write(cfgfile)

			self.conf_dict = conf_dict

		except BotTokenError:
			print("\033[91mRevisa el fichero de configuracion: " + cons.CONF_FILE_NAME +
			        ", debes escribir el token de tu bot:"
			        "\n\tbot_token = "+cons.BOT_TOKEN_DEFAULT+"\033[0m")
			sys.exit(1)

		except Exception as error:
			print("Hay errores en el fichero de configuracion ", cons.CONF_FILE_NAME, ":")
			print("\033[91m", error, "\033[0m")
			#sys.exit(1)

		finally:
			print("Releasing config lock")
			lock.release()  # release lock, no matter what
