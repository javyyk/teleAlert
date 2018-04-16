import re


class ChannelCustom:

	def __init__(self, id=-1, access_hash=-1, username=None, title=None, last_msg=-1):
		self.id = id
		self.access_hash = access_hash
		self.username = username
		self.title = title
		self.last_msg = last_msg

	"""def id(self, channel_id):
		self.id = int(channel_id)

	def hash(self, hash):
		self.hash = hash

	def last_msg(self, last_msg):
		self.id = int(last_msg)"""

	def __str__(self):
		sb = []
		for key in self.__dict__:
			sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))
		str = ', '.join(sb)
		str = "("+str + ")"

		regex = re.compile(r"(\\|\"|,|\'|;)+", re.IGNORECASE)
		str = re.sub(regex, '', str)
		#str = ''.join([i if ord(i) < 128 else '' for i in str])

		return str

	def __repr__(self):
		return self.__str__()

	def to_save(self):
		regex = re.compile(r"(\\|\"|,|\'|;)+", re.IGNORECASE)
		username = re.sub(regex, '', self.username)
		#username = ''.join([i if ord(i) < 128 else '' for i in username])
		title = re.sub(regex, '', self.title)
		title = ''.join([i if ord(i) < 128 else '' for i in title])

		fields = [str(self.id), str(self.access_hash), username, title, str(self.last_msg)]
		fields_str = ', '.join(fields)
		return fields_str
