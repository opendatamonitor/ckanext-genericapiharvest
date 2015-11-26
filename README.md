ckanext-genericapiharvest
==========================

A harvester to allow CKAN directories to keep in sync with catalogues that provide the data via an API service.

In order to use this tool, you need to have the CKAN harvester extension (https://github.com/okfn/ckanext-harvest)
installed and loaded for your CKAN instance.
Tested with CKAN v2.2 (http://docs.ckan.org/en/ckan-2.2/).

General
--------
The plugin uses the mongo DB as metadata repository and developed as part of the ODM project (www.opendatamonitor.eu).


Building
---------

To build and use this plugin, simply:

    git clone https://github.com/opendatamonitor/ckanext-genericapiharvest.git
    cd ckanext-genericapiharvest
    pip install -r requirements.txt
    python setup.py develop

Then you will need to update your CKAN configuration to include the new harvester.  This will mean adding the
ckanext-genericapiharvest plugin as a plugin, e.g.

    ckan.plugins = genericapi_harvester genericapiharvest

Also you need to add the odm_extension settings to the development.ini file in your ckan folder.  

    [ckan:odm_extensions]
    mongoclient=localhost
    mongoport=27017
    log_path=/var/local/ckan/default/pyenv/src/

Using
---------

After setting this up, you should be able to go to:
    http://localhost:5000/harvest

Select Register a new Catalogue

Select the GENERICAPI radiobutton

In case that you don't have the ckanext-htmlharvest extension installed (https://github.com/opendatamonitor/ckanext-htmlharvest)

Then go to:

    http://localhost:5000/genericapiharvest/generic



Licence
---------

This work implements the ckanext-harvest template (https://github.com/ckan/ckanext-harvest) and thus 
licensed under the GNU Affero General Public License (AGPL) v3.0 (http://www.fsf.org/licensing/licenses/agpl-3.0.html).
