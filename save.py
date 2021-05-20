import os, configparser, subprocess, hashlib, argparse, sqlite3, pathlib
import getnetguids
"""
store all the malware samples you want to introduce in the database
in the directory indicated in the configuration file "to_save_directory".
Then run this script with the -f parameter followed by the name of the malware family the malware samples belong to.

example: python save.py -f asyncrat
"""

def main():
	get_info()

def get_info():
	""" Get information from files to save"""
	tosavepath = config["directory"]["to_save_directory"] # Malware path
	trhpath = config["directory"]["trh_directory"] # TRH path

	for f in os.listdir(tosavepath):
		file_path = f"{tosavepath}{os.sep}{f}"

		if not os.path.isdir(file_path):
			output = subprocess.run(["%s"%(trhpath), file_path], capture_output=True)

			if output.stdout.decode("utf-8") != '':
				data_dic = {}
				data_dic["trh_hash"] = output.stdout.decode("utf-8").rstrip()
				data_dic["guid"] = getnetguids.get_netguid(file_path)
				data_dic["sha256"] = hashlib.sha256(open(file_path,'rb').read()).hexdigest()
				data_dic["detection"] = args.family
				conect = create_connection()
				save_data(conect, data_dic)
				conect.commit()

def create_connection():
	conn = None
	try:
		conn = sqlite3.connect(config["database"]["database_directory"])
	except Error as e:
		print(e)

	return conn

def save_data(conn, d):
	""" Save data into the database"""
	cur = conn.cursor()
	try:
		cur.execute("INSERT INTO data(sha256,detection,typeRefHash, guid) VALUES (?, ?, ?, ?)", (d["sha256"], d["detection"].lower(), d["trh_hash"], d["guid"]))
	except Error as e:
		print(e)
	return cur

if __name__ == '__main__':
	
	config = configparser.ConfigParser()
	config.read('config.ini')
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--family', help='Name of the malware family that all samples in the to_save directory belong to', required=True)
	args = parser.parse_args()
	main()
