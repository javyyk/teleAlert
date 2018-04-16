class Packet:

	def __init__(self, request_code, request_data):
		self.request_code = request_code
		self.request_data = request_data
		self.reply_code = None
		self.reply_data = None


	def __repr__(self):
		return "Rq Code: {0}, Rq Data: {1},\n Rly Code: {2}, Rly Data: {3}"\
			.format(self.request_code, self.request_data, self.reply_code, self.reply_data)
