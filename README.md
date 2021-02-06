# Neossins
Neossins is an application based on TypeRef Hasher that belongs to G Data Cyberdefense. Only works with malware samples compiled in .NET.

Explanation: http://myblog


TypeRef Hasher tool: hxxps://github.com/GDATASoftwareAG/TypeRefHasher

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

It is also necessary to install TRH. It can be obtained from the following link: https://github.com/GDATASoftwareAG/TypeRefHasher/releases

# files
The files that you can find in the repository are the following:

<code>neossins.py</code> Contains all the application logic and is the file that will be executed to run the application.

<code>requirements.txt</code> Contains all the requirements for run the application.

<code>database_sqlite.py</code> Has the logic to connect to the database and perform queries.

<code>data.sqlite</code> Is the database with the relation malware_sha512, family name and TRH.

<code>config.ini</code> Contains information that can be modified for the logic of the application.

<code>Directory malware</code> Contains malware samples. DO NOT RUN IN UNCONTROLLED ENVIRONMENTS.

<code>Directory add_data<code> Has a script for storing data in the database.


# Usage
1. Firs of all, change the configuration file information.

Example config.ini

```
[directory]
malware_directory = /opt/neossins/malware
trh_directory = /opt/trh/TypeRefHasher/trh

[database]
database_directory = /opt/neossins/data.sqlite

[save]
csv_file = /opt/neossins/add_data.csv

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

# Examples
<h3>Scenario</h3>


# Screenshots

# Version
0.1 alfa version

# Thanks
Thanks to https://github.com/GDATASoftwareAG and https://github.com/secana/

