from ckan.lib.base import BaseController, c
from ckan.controllers.package import PackageController
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model
from ckanext.harvestodm.logic.action.create import harvest_source_create
from ckan.logic import ValidationError
from ckan.lib.base import c

from ckan.model import Session, Package
from ckan.common import OrderedDict, _, json, request, c, g, response
import ckan.lib.navl.dictization_functions as dict_fns
from ckanext.genericapiharvest.plugin import DATASET_TYPE_NAME
from ckanext.harvestodm.plugin import _create_harvest_source_object
import json
import logging
#import SaveLabels
import uuid
#import AutoMetadataFinder
import pymongo
import bson
#import MetadataFinder
import sys
import ckan.plugins.toolkit as toolkit
#reload(sys)
#sys.setdefaultencoding("utf-8")
##---------------------------------------------
import configparser

##read from development.ini file all the required parameters
config = configparser.ConfigParser()
config.read('/var/local/ckan/default/pyenv/src/ckan/development.ini')
mongoclient=config['ckan:odm_extensions']['mongoclient']
mongoport=config['ckan:odm_extensions']['mongoport']


language_mappings={'English':'en','Bulgarian':'bg','Croatian':'hr','Czech':'cs',\
'Danish':'da','German':'de','Greek':'el','Spanish':'es','Estonian':'et','Finnish':'fi',\
'French':'fr','Hungarian':'hu','Italian':'it','Lithuanian':'lt','Latvian':'lv','Icelandic':'is',\
'Maltese':'mt','Dutch':'nl','Polish':'pl','Portuguese':'pt','Romanian':'ro','Slovak':'sk','Swedish':'sv','Ukrainian':'uk','Norwegian':'no'}
log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

get_action = logic.get_action
clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

client = pymongo.MongoClient(str(mongoclient), int(mongoport))

class CustomGenericapiHarvestController(PackageController):


    def __before__(self, action, **params):

        super(CustomGenericapiHarvestController, self).__before__(action, **params)

        c.dataset_type = DATASET_TYPE_NAME

    def new_genericapi_harvester(self):
        return render('generic.html')
        #return render(self._new_template(package_type),
                              #extra_vars={'stage': 'active'})
                          
    def read_data(self, data=None):
	  errors=""
	  data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.POST))))
	  save_action = request.params.get('save')
	  print(data)

	  cat_url=data['cat_url']
	  if cat_url=="":
		errors =errors+"Catalogue Url field should not be empty."+'\n'
	  if 'http' not in cat_url:
		errors =errors+"Invalid Catalogue Url."+'\n'
	  
	  datasets_list_url=data['datasets_list_url']
	  if datasets_list_url=="":
		errors =errors+"Datasets List Url field should not be empty."+'\n'
	  
	  dataset_url=data['dataset_url']
	  #if dataset_url=="":
		#errors =errors+"Dataset Url field should not be empty."+'\n'
		
	  datasets_list_identifier=data['datasets_list_identifier']
	  if datasets_list_identifier=="":
		errors =errors+"Datasets List Json Key field should not be empty."+'\n'

	  dataset_id=data['dataset_id']
	  if dataset_id=="":
		errors =errors+" Dataset Id Json Key field should not be empty."+'\n'

	  apikey=data['apikey']
	  print(apikey)

	  metadata_mappings=data['metadata_mappings']

	  
	  try:
		metadata_mappings=json.loads(metadata_mappings)
	  except:
		errors =errors+"Invalid Json!"+'\n'
	  
	  vars = {'data': data, 'errors': str(errors)}

	  catalogues_description=str(data['catalogues_description'])
	  catalogue_country=str(data['catalogue_country'])
	  catalogue_language=str(data['language'])
	  catalogue_title=str(data['catalogue_title'])
	  harvest_frequency=str(data['harvest_frequency'])
	  name=catalogue_title.replace('.','-').replace(' ','-').replace('_','-').replace('(','-').replace(')','-').replace('[','-').replace(']','-').replace(',','-').replace(':','-')
	  package_id=cat_url
	  config='{"read_only": true, "default_tags": [], "remote_groups": "only_local", "remote_orgs": "create", "default_extras": {"harvest_url": "{harvest_source_url}/dataset/{dataset_id}", "new_extra": "Test"}, "default_groups": ["french"], "user": "admin", "api_key": "<REMOTE_API_KEY>", "override_extras": true, "api_version": 1}'
	  config=json.loads(config)
	  dataset_dict = {
    		'name': str(name),
    		'id':str(uuid.uuid3(uuid.NAMESPACE_OID, str(cat_url))),
			'frequency':str(harvest_frequency),
			'url': str(cat_url),
			'title': str(catalogue_title),
			'package_id':str(package_id),
			'source_type':'genericapi',
			'notes':str(catalogues_description),
			'catalogue_country':str(catalogue_country),
			'language':str(catalogue_language),
			'catalogue_date_created':'',
			'catalogue_date_updated':'',
			'metadata_mappings':json.dumps(metadata_mappings),
			"datasets_list_url":str(datasets_list_url),
			"dataset_url":str(dataset_url),
			"datasets_list_identifier":str(datasets_list_identifier),
			"dataset_id":str(dataset_id),
			"apikey":str(apikey)
				}
	  print(dataset_dict)

	  #AddResourceToCkan.AddResourceToCkan(dataset_dict)
	  context = {'model': model, 'session': Session, 'user': u'admin','message': '','save': True}
	  try:
		harvest_source_create(context,dataset_dict)
	  except toolkit.ValidationError as ex:
		print(ex)
		vars = {'data': data, 'errors': str(ex)}
			  #return render('htmlharvest1.html', extra_vars=vars)
		return render('generic.html', extra_vars=vars)
	  dataset_dict.update({'config':str(metadata_mappings)})
	  return render('read.html', extra_vars=vars)

