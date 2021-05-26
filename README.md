# Neossins
Neossins is an application based on TypeRef Hasher that belongs to G Data Cyberdefense and on GetNETGUIDs that belongs to Cylance. Only works with malware samples compiled in .NET.

This project aims to identify similarity between malware samples stored in the database. It is important to enrich the database with as many samples as possible to obtain better results.

Explanation: https://joseliyo-jstnk.medium.com/typeref-hasher-the-imphash-solution-for-samples-in-net-9aad14502bbf

TypeRef Hasher tool: hxxps://github.com/GDATASoftwareAG/TypeRefHasher
GetNETGUIDs tool: https://github.com/cylance/GetNETGUIDs

# Installation
This tool is developed in Python3.

I recommend creating a virtual environment with virtualenv to install the project dependencies and run it. However, it can be done as desired.
```
virtualenv <project_name>

source <project_name/bin/activate
```

The dependencies can be installed using the requirements file:
```
pip install -r requirements.txt
```

It is also necessary to download <code>trh</code> file -> Linux x64 (Standalone binary). It can be obtained from the following link: https://github.com/GDATASoftwareAG/TypeRefHasher/releases

# files
The files that you can find in the repository are the following:

<code>neossins.py</code> Contains all the application logic and is the file that will be executed to run the application.

<code>requirements.txt</code> Contains all the requirements for run the application.

<code>database_sqlite.py</code> Has the logic to connect to the database and perform queries.

<code>data.sqlite</code> Is the database with the relation malware_sha512, family name and TRH.

<code>config.ini</code> Contains information that can be modified for the logic of the application.

<code>Directory malware</code> Contains malware samples. DO NOT RUN IN UNCONTROLLED ENVIRONMENTS.

<code>save.py</code> Script for storing data in the database. It saves malware from config folder 'to_save_directory'


# Usage
1. Firs of all, change the configuration file information.

Example config.ini

```
[directory]
malware_directory = /opt/neossins/malware
trh_directory = /opt/trh/TypeRefHasher/trh
to_save_directory = /opt/neossins/to_save

[database]
database_directory = /opt/neossins/data.sqlite

[server]
ip = 0.0.0.0
```
1.1 Store malware samples that you want to check for similarity in .NET inside the directory configured in malware_directory.

1.2 Set the directory where you have stored trh

2. Once configured, just run the application and a web server will be built
```
python neossins.py
```
Open a web browser and go to http://<configured_ip>:8050/. 

3. if you want to store malware samples together with their HRT in the database, put the samples in the to_save directory and run the script with the -f parameter indicating the name of the family the samples belong to.
```
python save.py -f asyncrat
```
4. If you want to build graph only between samples in database

```
python neossins.py -d
```

# Examples
<h3>Scenario</h3>
Imagine you have to fulfill an intelligence requirement to identify if three samples have any similarity with those already stored in your organization.

Place the malware in the directory set in "malware_directory" within the configuration file.

Launch the application and check the similarities that the network shows if they exist.

Once finished, enrich the database with the three samples by placing them in the "to_save_directory" directory within the configuration file and launch the "save.py -f family_name" script to store them.

# Screenshots
![alt text](https://github.com/jstnk9/neossins/blob/main/images/graph.png?raw=true)

# Version
0.1 alfa version

# Thanks
Thanks to https://github.com/GDATASoftwareAG

