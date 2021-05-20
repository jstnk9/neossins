import configparser, sqlite3

config = configparser.ConfigParser()
config.read('config.ini')

def create_connection():
	""" create a database connection to the SQLite database
	    specified by the db_file
	:param db_file: database file
	:return: Connection object or None
	"""
	conn = None
	try:
		conn = sqlite3.connect(config["database"]["database_directory"])
	except Error as e:
		print(e)

	return conn

def select_trh(conn, search_key):
	# Get information when match trh
	cur = conn.cursor()
	cur.execute("SELECT sha256,detection FROM data WHERE typeRefHash =?", (search_key,))
	rows = cur.fetchall()

	return rows

def select_guid(conn, search_key):
	# Get information when match trh
	cur = conn.cursor()
	cur.execute("SELECT sha256,detection FROM data WHERE guid =?", (search_key,))
	rows = cur.fetchall()

	return rows