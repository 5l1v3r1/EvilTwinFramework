import os
from plugin import AirHostPlugin
from subprocess import Popen


"""
Needs a lot of TODO
was first meant for EAP hashes
now realize it is better for captive portal prints
"""
class CredentialPrinter(AirHostPlugin):

	def __init__(self):
		super(CredentialPrinter, self).__init__("credentialprinter")
		self.log_folder = self.config["log_folder"]
		self.log_file_name = self.config["log_file_name"]
		self.credential_printer_process = None

	def post_start(self):
		hash_log_file = "{folder}{name}{id}.log".format(folder = self.log_folder,
														name = self.log_file_name,
														id = len(os.listdir(self.log_folder)))
		open(hash_log_file, "a").close()
		self.credential_printer_process = Popen(("tail -F " + hash_log_file).split())

	def restore(self):
		self.credential_printer_process.send_signal(9)
