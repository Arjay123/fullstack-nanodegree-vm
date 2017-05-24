## item-catalog

A website that allows users to perform CRUD operations on a SQLite database using Python with Flask and SQLAlchemy.

## Install

This repo comes with a vagrant file that should be used to install the VM for the application to run in. To install the VM, navigate into the /vagrant directory and use the command:
>vagrant up

Once installation is complete use the command:
>vagrant ssh

to navigate into the VM. Use the command:
>logout

once in the VM to exit the VM

From inside the vm use the command:
>cd \vagrant/catalog

and then use the command:
>python database_init.py

to initialize the database with sample data.
Additionally you can use the create_db() function in database_setup.py.

In order to use Google and Facebook's OAuth system's you will need to register your own application on their developer pages and create two .json files with the client secrets.

Google - client_secrets.json https://developers.google.com/identity/protocols/OAuth2WebServer#enable-apis
{
    "web": {
        "client_id": "XXXXXXX",
        "project_id": "XXXXXXX",
        "auth_uri": "XXXXXXX",
        "token_uri": "XXXXXXX",
        "auth_provider_x509_cert_url": "XXXXXXX",
        "client_secret": "XXXXXXX",
        "redirect_uris": [
            "XXXXXXX"
        ],
        "javascript_origins": [
            "XXXXXXX",
            "XXXXXXX"
        ]
    }
}

Facebook - 'fb_client_secrets.json' 
https://developers.facebook.com/docs/facebook-login/web
{"web":{
    "client_id": "XXXXXXXXXX",
    "client_secret": "XXXXXXXXXXX"
}}


## Usage

Once all above requirements are met, you may test the database by running the database_test.py script.

To start the application, run the project.py script
>python project.py
