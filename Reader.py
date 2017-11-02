# -*- coding: utf-8 -*-

class BinaryReader:

	def __init__(self,stream):

		self.stream = stream

	def read_uint32(self):

		return int.from_bytes(self.stream.read(4),'little')

	def read_uint16(self):

		return int.from_bytes(self.stream.read(2),'little')

	def read_int16(self):

		return int.from_bytes(self.stream.read(2),'little', signed=True)

	def read_byte(self):

		return int.from_bytes(self.stream.read(1),'little')

	def read_string(self,length):

		return self.stream.read(length).decode('utf-8')
		
	def read(self,bytes_number):

		return self.stream.read(bytes_number)