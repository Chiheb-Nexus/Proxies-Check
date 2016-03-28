
#
#!/usr/bin python3
import urllib.request as Request
import sqlite3
import os.path as Path

class ProxyHandlerStatus():
	"""
	Check IP Proxy status and check if a string is in the HTML output
	"""

	def run(self, url, proxy_ip_port, word):
		"""
		Main function
		"""
		error = "ERROR"
		try:
			print("[+] Setup proxy ...")
			self.setup(proxy_ip_port)
			print("+-> Setup done.")
		except Exception as e:
			#DEBUG
			print("x-> Setup Error", e)
			self.safe_exit()
		try:
			print("[+] Fetching url ...")
			html = self.fetch_url_with_proxy(url)
			print("[+] Testing the output ... ")
			return self.test_html_output(str(html), word)
		except Exception as e:
			#DEBUG
			print("x -> Printing Error", e)
			return error

	def test_html_output(self, html, word):
		"""
		In our database field will be 5 stats: 
		1- Not Present : Word not present in HTML output 
		2- Present : Word present in HTML output
		3- Timeout : Timeout Exception
		4- ERROR : There is another error (402 or 502 or else)
		"""
		if "ERROR" in html:
			return "Timeout"
		if word in html:
			print("+-> " + word +" is in the HTML output")
			return "Present"
		else:
			print("+-> " + word +" isn't in the HTML output")
			return "Not Present"

	def setup(self, proxy_ip_port):
		"""
		Setup proxy settings
		"""
		auth = Request.HTTPBasicAuthHandler()
		proxy_support = Request.ProxyHandler(proxy_ip_port)
		opener = Request.build_opener(proxy_support, auth, Request.CacheFTPHandler)
		Request.install_opener(opener)

	def fetch_url_with_proxy(self, url):
		"""
		In this part, i created a custom signal TimeoutException and assign a signal.
		If after 5s there isn't any response from the try ... except boucle 
		signal will throw an TimeoutException exception.
		"""
		import signal

		class TimeoutException(Exception):
			def __str__(self):
				print("x-> Can't reach the server in 5s ... Timeout")

		def timeouthandler(signum, frame):
			raise TimeoutException

		signal.signal(signal.SIGALRM, timeouthandler)
		signal.alarm(5)
		try:
			with Request.urlopen(url) as response:
				html = response.read()
			return html
		except TimeoutException:
			#DEBUG
			TimeoutException.__str__(self)
			return "ERROR"

	def check_db_exist(self):
		"""
		Check if the database exist or not.
		If db exist => Update 
		If db don't exist => Create 
		"""
		if Path.exists("proxies.db"):
			print("[+] Connection to database ...")
			connect_db = sqlite3.connect("proxies.db")
			print("+-> Connection successful.")
			return "exist", connect_db
		else:
			try:
				connect_db = sqlite3.connect("proxies.db")
				print("[+] Creation of database ...")
				connect_db.execute('''CREATE TABLE PROXY
					(ID INT PRIMARY KEY     NOT NULL,
						IP           TEXT    NOT NULL,
						PORT            TEXT     NOT NULL,
						STATUS        CHAR(50));''')
				print("+-> Database create successfully.")
				return "not exist", connect_db
			except Exception as e:
				#DEBUG
				print(e)
				import sys
				sys.exit(0)

	def create_db(self, connect_db, msg, status, i , ip, port):
		"""
		Updating || Creating database
		"""

		if msg == "exist":
			try:
				print("[+] Updating database ...")
				connect_db.execute("""UPDATE PROXY SET IP= ? WHERE ID= ? ;""", (ip, i))
				connect_db.execute("""UPDATE PROXY SET PORT= ? WHERE ID= ? ;""", (port, i))
				connect_db.execute("""UPDATE PROXY SET STATUS= ? WHERE ID= ? ;""", (status, i))
				connect_db.commit()
				print("+-> Update seccussful!")
				return i
			except Exception as e:
				#DEBUG
				print(e)
				pass
		if msg == "not exist":
			try:
				print("[+] Insert in new database ...")
				connect_db.execute("""INSERT INTO PROXY (ID,IP,PORT,STATUS)\
					VALUES (?, ? , ?, ?);""",(i, ip, port, status))

				connect_db.commit()
				print("+-> Insert seccussful!")
				return i
			except Exception as e:
				#DEBUG
				print(e)
				pass

	def exit_db(self, db):
		"""
		Safe exit database
		"""
		db.close()

### Test ###

if '__main__' == __name__:

	url = "http://www.internetbadguys.com/"
	#url = "http://www.bing.com"
	word_to_find = "OpenDNS"
	proxy_ip_port = [{'http':'http://54.183.178.195:8083'}, {'http':'http://61.174.13.12:80'},
	{'http':'http://187.161.104.187:54042'}, {'http':'http://46.118.24.107:80'}, {'http':'http://58.40.81.135:8118'}]
	index = 0

	proxyobj = ProxyHandlerStatus()

	db_exist, connect_db = proxyobj.check_db_exist()


	for proxy in proxy_ip_port:
		link = proxy["http"]
		print("------------------------------------------")

		print("[+] Testing proxy: ", link )
		status = proxyobj.run(url, proxy, word_to_find)

		ip = link.split("http://")[1]
		ip, port = ip.split(":")[0], ip.split(":")[1]
		try:
			index = int(proxyobj.create_db(connect_db, db_exist, status, index, ip, port))
			index+=1
		except Exception as e:
			#DEBUG
			print(e)
			pass

	print("-------------------------------------------")
	proxyobj.exit_db(connect_db)



