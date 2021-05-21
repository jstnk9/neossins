"""
Script that take TypeRefHash for .NET files and Project GUID.
Author: Jose Luis Sanchez Martinez
Twitter: Joseliyo_Jstnk
Version: 0.1
trh: https://github.com/GDATASoftwareAG/TypeRefHasher
"""
import os, configparser, subprocess, hashlib, sqlite3
import database_sqlite
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import plotly.express as px
import getnetguids
from argparse import ArgumentParser
import itertools 

def main():
	# Default mode = trh hash 
	parser = ArgumentParser()
	parser.add_argument('mode', default="trh", nargs='?', type=str, metavar="mode",
                        help="trh or guid mode")
	parser.add_argument('-d', '--database', nargs='?', const='y', default='n', help="create graph from database objects")
	args = parser.parse_args()

	if args.mode != "trh" and args.mode != "guid":
		parser.print_help()
		exit()
	
	if args.database == 'y':
		process_data_db(args.mode)
	elif args.database == 'n':
		process_data(args.mode)
	else:
		parser.print_help()
		exit()
	

def process_data(mode):
	
	""" Take the directory and get all type ref hashes/guids from the files"""
	malpath = config["directory"]["malware_directory"] # Malware path

	for f in os.listdir(malpath):
		
		file_path = f"{malpath}{os.sep}{f}"
		if not os.path.isdir(file_path):
			data_dic = {}

			if mode == "guid":
				data_dic["guid"] = getnetguids.get_netguid(file_path)
			elif mode == "trh":
				trhpath = config["directory"]["trh_directory"] # TRH path
				output = subprocess.run(["%s"%(trhpath), file_path], capture_output=True)
				if output.stdout.decode("utf-8") != '':
					data_dic["trh_hash"] = output.stdout.decode("utf-8").rstrip()
				
			data_dic["sha256"] = hashlib.sha256(open(file_path,'rb').read()).hexdigest()
			data_dic["filename"] = f
			data_dic["filepath"] = file_path
			value_list.append(data_dic)			

	get_relations(mode)

def process_data_db(mode):

	conect = database_sqlite.create_connection()

	if mode == "guid":
		rows = database_sqlite.select_guid_all(conect)
		key_val = "guid"
	elif mode == "trh":
		rows = database_sqlite.select_trh_all(conect)
		key_val = "typeRefHash"

	for r in rows:
		d = {}
		d["sha256"] = f"{r[1]}"
		d[key_val] = f"{r[0]}"
		value_list.append(d)	

	for d in value_list:

		d_hash = '%s'%(d["sha256"])

		d["relations"] = []
		# paarent project guid
		d["relations"].append({'data': {'id': d[key_val], 'label': 'Project ' + d[key_val][0:4]}})

		d["relations"].append({'data': {'id': d_hash, 'label': d_hash[0:4], 'parent': d[key_val]}, 'classes': 'red'})

		for r in rows:
			r_hash = f"{r[1]}"
			r_val = f"{r[0]}"
			# avoid comparing with itself
			if d["sha256"] == r_hash:
				continue
			
			if d[key_val] == r_val:
				d["relations"].append({'data': {'id': r_hash, 'label': r_hash[0:4], 'parent': d[key_val]}, 'classes': 'red'})
				#d["relations"].append({'data': {'id': r_hash, 'label': r_hash[0:4]}, 'classes': 'red'})
				d["relations"].append({'data':{'source': d_hash, 'target': r_hash}})


	generate_structure_graph()



def get_relations(mode):
	""" get corresponding files from the database """
	conect = database_sqlite.create_connection()
	for d in value_list:
		d_hash = '%s'%(d["sha256"])
		if mode == "guid":
			rows = database_sqlite.select_guid(conect, d["guid"])
		elif mode == "trh":
			rows = database_sqlite.select_trh(conect, d["trh_hash"])
		

		d["relations"] = []
		d["relations"].append({'data': {'id': d_hash[0:4], 'label': d_hash[0:4]}, 'classes': 'red'})
		for r in rows:
			d["relations"].append({'data': {'id': '%s'%(r[0]), 'label': '%s'%(r[0])}, 'classes': 'pink'})
			d["relations"].append({'data': {'id': '%s'%(r[1]), 'label': '%s'%(r[1])}, 'classes': 'blue'})
			d["relations"].append({'data':{'source': '%s'%(r[0]), 'target': '%s'%(d["sha256"])}})
			d["relations"].append({'data':{'source': '%s'%(r[0]), 'target': '%s'%(r[1])}})
	generate_structure_graph()

def generate_structure_graph():
	# this method create the structure for the cytoscape library
	graph_list = []
	for d in value_list:
		for r in d["relations"]:
			graph_list.append(r)
	create_graph(graph_list)

def create_graph(gr):
	# Create the graph
	app.layout = html.Div([
    html.P("Neossins - TypeRefHash/GUID graph:"),
    cyto.Cytoscape(
        id='cytoscape-layout-2',
        elements=gr,
        #layout={'name': 'circle', 'radius': 500},
		layout = {'name':'cose', 'animate':'true'},
        style={'width': '100%', 'height': '1000px'},
		
        stylesheet=[
        # Group selectors
	        {
	            'selector': 'node',
	            'style': {
	                'content': 'data(label)'
	            }
	        },
	        {
	            'selector': '.red',
	            'style': {
	                'background-color': 'red',
	                'shape': 'rectangle'
	            }
	        },
	        {
	            'selector': '.pink',
	            'style': {
	                'background-color': '#dea4d4'
	            }
	        },
	        {
	            'selector': '.blue',
	            'style': {
	                'background-color': '#32CBDF'
	            }
	        }
	    ]
    )
])
	app.run_server(host='%s'%(config["server"]["ip"]),debug=True)

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read('config.ini')
	value_list = []
	app = dash.Dash(__name__)
	main()