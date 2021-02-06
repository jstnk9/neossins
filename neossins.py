"""
Script that take TypeRefHash for .NET files.
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


def main():
	get_trh()

def get_trh():
	""" Take the directory and get all type ref hashes from the files"""
	malpath = config["directory"]["malware_directory"] # Malware path
	trhpath = config["directory"]["trh_directory"] # TRH path

	for f in os.listdir(malpath):
		output = subprocess.run(["%s"%(trhpath), "%s/%s"%(malpath,f)], capture_output=True)

		if output.stdout.decode("utf-8") != '':
			data_dic = {}
			data_dic["trh_hash"] = output.stdout.decode("utf-8").rstrip()
			data_dic["sha256"] = hashlib.sha256(open('%s/%s'%(malpath,f),'rb').read()).hexdigest()
			data_dic["filename"] = f
			data_dic["filepath"] = "%s/%s"%(malpath,f)
			trhlist.append(data_dic)			
	get_relations()

def get_relations():
	""" get files from the database with the same trh"""
	conect = database_sqlite.create_connection()
	for d in trhlist:
		rows = database_sqlite.select_trh(conect, d["trh_hash"])
		d["relations"] = []
		d["relations"].append({'data': {'id': '%s'%(d["sha256"]), 'label': '%s'%(d["sha256"])}, 'classes': 'red'})
		for r in rows:
			d["relations"].append({'data': {'id': '%s'%(r[0]), 'label': '%s'%(r[0])}, 'classes': 'pink'})
			d["relations"].append({'data': {'id': '%s'%(r[1]), 'label': '%s'%(r[1])}, 'classes': 'blue'})
			d["relations"].append({'data':{'source': '%s'%(r[0]), 'target': '%s'%(d["sha256"])}})
			d["relations"].append({'data':{'source': '%s'%(r[0]), 'target': '%s'%(r[1])}})

	generate_structure_graph()

def generate_structure_graph():
	# this method create the structure for the cytoscape library
	graph_list = []
	for d in trhlist:
		for r in d["relations"]:
			graph_list.append(r)
	create_graph(graph_list)

def create_graph(gr):
	# Create the graph
	app.layout = html.Div([
    html.P("Neossins - TypeRefHash graph:"),
    cyto.Cytoscape(
        id='cytoscape-layout-2',
        elements=gr,
        layout={'name': 'random'},
        style={'width': '1500px', 'height': '1900px'},
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
	trhlist = []
	app = dash.Dash(__name__)
	main()