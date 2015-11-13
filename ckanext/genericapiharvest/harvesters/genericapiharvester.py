import urllib2

from ckan.lib.base import c
from ckan import model
from ckan.model import Session, Package
from ckan.logic import ValidationError, NotFound, get_action
from ckan.lib.helpers import json

from ckanext.harvestodm.model import HarvestJob, HarvestObject, HarvestGatherError, \
                                    HarvestObjectError
import pymongo
import logging
import configparser
log = logging.getLogger(__name__)
from base import HarvesterBase
import datetime



##read from development.ini file all the required parameters
config = configparser.ConfigParser()
config.read('/var/local/ckan/default/pyenv/src/ckan/development.ini')
log_path=config['ckan:odm_extensions']['log_path']
html_harvester_log_file_path=str(log_path)+'ckanext-htmlharvest/ckanext/htmlharvest/harvesters/html1.log'
mongoclient=config['ckan:odm_extensions']['mongoclient']
mongoport=config['ckan:odm_extensions']['mongoport']

text_file = open(str(html_harvester_log_file_path), "a")
client = pymongo.MongoClient(str(mongoclient), int(mongoport))

db=client.odm
custom_db=db.odm
db_fetch_temp=db.fetch_temp
db_jobs=db.jobs
class GENERICAPIHarvester(HarvesterBase):
    '''
    A Harvester for HTML-based instances
    '''
    config = None

    api_version = 2

    def _get_rest_api_offset(self):
        return '/api/%d/rest' % self.api_version

    def _get_search_api_offset(self):
        return '/api/%d/search' % self.api_version

    def _get_content(self, url):
        http_request = urllib2.Request(
            url = url,
        )

        api_key = self.config.get('api_key',None)
        if api_key:
            http_request.add_header('Authorization',api_key)
        http_response = urllib2.urlopen(http_request)

        return http_response.read()

    def _get_group(self, base_url, group_name):
        url = base_url + self._get_rest_api_offset() + '/group/' + group_name
        try:
            content = self._get_content(url)
            return json.loads(content)
        except Exception, e:
            raise e

    def _set_config(self,config_str):
        if config_str:
            self.config = json.loads(config_str)
            if 'api_version' in self.config:
                self.api_version = int(self.config['api_version'])

            log.debug('Using config: %r', self.config)
        else:
            self.config = {}

    def info(self):
        return {
            'name': 'genericapi',
            'title': 'Generic Api',
            'description': 'Harvests remote generic api instances',
            'form_config_interface':'Text'
        }

    def validate_config(self,config):
        if not config:
            return config

        try:
            config_obj = json.loads(config)

            if 'api_version' in config_obj:
                try:
                    int(config_obj['api_version'])
                except ValueError:
                    raise ValueError('api_version must be an integer')

            if 'default_tags' in config_obj:
                if not isinstance(config_obj['default_tags'],list):
                    raise ValueError('default_tags must be a list')

            if 'default_groups' in config_obj:
                if not isinstance(config_obj['default_groups'],list):
                    raise ValueError('default_groups must be a list')

                # Check if default groups exist
                context = {'model':model,'user':c.user}
                for group_name in config_obj['default_groups']:
                    try:
                        group = get_action('group_show')(context,{'id':group_name})
                    except NotFound,e:
                        raise ValueError('Default group not found')

            if 'default_extras' in config_obj:
                if not isinstance(config_obj['default_extras'],dict):
                    raise ValueError('default_extras must be a dictionary')

            if 'user' in config_obj:
                # Check if user exists
                context = {'model':model,'user':c.user}
                try:
                    user = get_action('user_show')(context,{'id':config_obj.get('user')})
                except NotFound,e:
                    raise ValueError('User not found')

            for key in ('read_only','force_all'):
                if key in config_obj:
                    if not isinstance(config_obj[key],bool):
                        raise ValueError('%s must be boolean' % key)

        except ValueError,e:
            raise e

        return config


    def gather_stage(self,harvest_job):
        log.debug('In CustomHarvester  gather_stage (%s)' % harvest_job.source.url)
        get_all_packages = True
        db=client.odm
        db_jobs=db.jobs
        config=db_jobs.find_one({"cat_url":harvest_job.source.url})
        datasets_list_url=config['datasets_list_url']
        datasets_list_identifier=config['datasets_list_identifier']
        dataset_id=config['dataset_id']
        api_key=config['apikey']
        if "data.norge.no" in harvest_job.source.url.rstrip('/'):
        	many_datasets_list=['/api/dcat/data.json?page=1','/api/dcat/data.json?page=2','/api/dcat/data.json?page=3','/api/dcat/data.json?page=4']
        else:
        	many_datasets_list.append(datasets_list_url) 

        j=0
        all_datasets=[]
        while j<len(many_datasets_list): 
			url=harvest_job.source.url.rstrip('/')+many_datasets_list[j].replace('{api}',api_key)
			print(url)
			result=urllib2.urlopen(url)
			try:
				  datasets=json.load(result)
				  if datasets_list_identifier!="":
					datasets=datasets[datasets_list_identifier]
			except:
				  try:
					headers = {'Accept':'application/json'}
					r=urllib2.Request(url,headers=headers)
					datasets=t=json.loads(urllib2.urlopen(r).read())
					if datasets_list_identifier!="":
					  datasets=datasets[datasets_list_identifier]
				  except:
					result=urllib2.urlopen(url)
					read=result.read()
					read=read.replace("null(","datasets=").rstrip(')')
					exec(read)
			count=0
			while count<len(datasets):
				all_datasets.append(datasets[count])
				count+=1
			datasets[:]=[]
			j+=1
	 
        
        i=0
        package_ids=[]	
        while i<len(all_datasets):
		  package_ids.append(all_datasets[i][dataset_id])
		  i+=1

        #print('****package ids****')
        #print(package_ids)
        #print(len(package_ids))
        
        ###load existing datasets names and ids from mongoDb
        datasets=list(custom_db.find({'catalogue_url':harvest_job.source.url}))
        datasets_ids=[]
        datasets_names=[]
        j=0
        while j<len(datasets):
		  datasets_ids.append(datasets[j]['id'])
		  j+=1

        
        
        ###check for deleted datasets that exist in mongo
        count_pkg_ids=0
        while count_pkg_ids<len(package_ids):
		  temp_pckg_id=package_ids[count_pkg_ids]
		  if temp_pckg_id in datasets_ids:
			datasets_ids.remove(temp_pckg_id)
		  count_pkg_ids+=1
        if len(datasets_ids)>0:
		j=0
		while j<len(datasets_ids):
		  i=0
		  while i<len(datasets):
			if datasets_ids[j] in datasets[i]['id']:
			  document=datasets[i]
			  document.update({"deleted_dataset":True})
			  custom_db.save(document)
			i+=1
		  j+=1

        try:
            object_ids = []
            if len(package_ids):
                for package_id in package_ids:
                      obj = HarvestObject(guid = package_id, job = harvest_job)
                      obj.save()
                      object_ids.append(obj.id)

                return object_ids

            else:
                self._save_gather_error('No packages received for URL: %s' % url,
                    harvest_job)
                return None
        except Exception, e:
            self._save_gather_error('%r'%e.message,harvest_job)


    def fetch_stage(self,harvest_object):

        '''
        Fetches the list of datasets from the catalog
        '''
        log.debug('In CustomHarvester fetch_stage')

        self._set_config(harvest_object.job.source.config)
        db=client.odm
        db_jobs=db.jobs
        config=db_jobs.find_one({"cat_url":harvest_object.source.url})
        api_key=config['apikey']
        dataset_url=config['dataset_url']
        metadata_mappings=json.loads(config['metadata_mappings'])
        if "data.norge.no" in harvest_object.source.url.rstrip('/'):
        	many_datasets_list=['/api/dcat/data.json?page=1','/api/dcat/data.json?page=2','/api/dcat/data.json?page=3','/api/dcat/data.json?page=4']
        else:
        	many_datasets_list.append(datasets_list_url) 
        
        
        if dataset_url!="":
		  fetch_url=harvest_object.source.url.rstrip('/')+dataset_url.replace("{api}",api_key).replace("{id}", harvest_object.guid)
		  #print(fetch_url)
        else:
		  fetch_url=""
        
        dataset={}
        features=[]
        
        if fetch_url!="":  
		  result=urllib2.urlopen(fetch_url)
		  try:
			try:
			  dataset=json.load(result)
			except:
			  try:
				headers = {'Accept':'application/json'}
				r=urllib2.Request(fetch_url,headers=headers)
				dataset=json.loads(urllib2.urlopen(r).read())
			  except:
				result=urllib2.urlopen(fetch_url)
				read=result.read()
				read=read.replace("null(","dataset=").rstrip(')')
				exec(read)
			#print(dataset)
		  except Exception, e:
			  log.exception('Could not load ' + fetch_url)
			  self._save_gather_error('%r'%e.message,harvest_object)
        
        ##case that api do not return json per dataset but all as a list
        else:
		  #print(harvest_object.guid)
		  datasets_list_url=config['datasets_list_url']
		  datasets_list_identifier=config['datasets_list_identifier']
		  api_key=config['apikey']     
		  dataset_id=config['dataset_id']
		  j=0
		  while j<len(many_datasets_list):
			  url=harvest_object.job.source.url.rstrip('/')+many_datasets_list[j].replace('{api}',api_key)
			  result=urllib2.urlopen(url)

			  datasets=json.load(result)
			  if datasets_list_identifier!="":
				datasets=datasets[datasets_list_identifier]
			  i=0
			  while i<len(datasets):
				if datasets[i][dataset_id]==harvest_object.guid:
				  dataset=datasets[i]
				i+=1
			  j+=1		  	
        


        content={}
        db_jobs=db.jobs
        base_url = harvest_object.source.url
        #print(base_url)
        
        ## get language info from mongo
        language=""
        try:
          doc=db_jobs.find_one({"cat_url":str(base_url)})
          language=doc['language']
        except:
          pass


        ##basic fields
        notes=metadata_mappings['notes']
        title=metadata_mappings['title']
        id1=metadata_mappings['id']
        name=metadata_mappings['name']
        license=metadata_mappings['license']
        tags=metadata_mappings['tags']
        author_email=metadata_mappings['author_email']
        if '->' in author_email:
		  author_email=author_email.split('->')
		  author_email=author_email[0]
        author=metadata_mappings['author']
        if '->' in author:
		  author=author.split('->')
		  author=author[0]
        maintainer=metadata_mappings['maintainer']
        maintainer_email=metadata_mappings['maintainer_email']
        ##extras
        date_updated=metadata_mappings['date_updated']
        date_released=metadata_mappings['date_released']
        country=metadata_mappings['country']
        category=metadata_mappings['category']
        update_frequency=metadata_mappings['update_frequency']
        state=metadata_mappings['state']
        temporal_coverage=metadata_mappings['temporal_coverage']
        city=metadata_mappings['city']
        ##resources
        resources=metadata_mappings['resources']
        resources_url=metadata_mappings['resources_url']
        resources_size=metadata_mappings['resources_size']
        resources_mimetype=metadata_mappings['resources_mimetype']
        resources_format=metadata_mappings['resources_format']





	## transform custom scheme to ckan scheme:
        if len(dataset.keys())>1:
		  if author in dataset.keys() and author!="":
			if '->' not in metadata_mappings['author']:
			  content.update({"author":dataset[author]})
			else:
			  author=metadata_mappings['author'].split('->')
			  content.update({"author":dataset[author[0]][author[1]]})
		  if notes in dataset.keys() and notes!="":
			content.update({"notes":dataset[notes]})
		  if title in dataset.keys() and title!="":
			content.update({"title":dataset[title]})
		  if title=="" and name!="":
			content.update({"title":dataset[name]})
		  if name in dataset.keys() and name!="":
			content.update({"name":dataset[name]})
		  if license in dataset.keys() and license!="":
			content.update({"license_id":dataset[license]})
		  if tags in dataset.keys() and tags!="":
			content.update({"tags":dataset[tags]})
		  if author_email in dataset.keys() and author_email!="":
			if '->' not in metadata_mappings['author_email']:
			  content.update({"author_email":dataset[author_email]})
			else:
			  author_email=metadata_mappings['author_email'].split('->')
			  content.update({"author_email":dataset[author_email[0]][author_email[1]]})
		  if maintainer in dataset.keys() and maintainer!="":
			content.update({"maintainer":dataset[maintainer]})
		  if maintainer_email in dataset.keys() and maintainer_email!="":
			content.update({"maintainer_email":dataset[maintainer_email]})


          	  ##extras
		  extras={}
		  if date_updated in dataset.keys() and date_updated!="":
			extras.update({"date_updated":dataset[date_updated]})
		  if date_released in dataset.keys() and date_released!="":
			extras.update({"date_released":dataset[date_released]})
		  if country in dataset.keys() and country!="":
			extras.update({"country":dataset[country]})
		  if category in dataset.keys() and category!="":
			extras.update({"category":dataset[category]})
		  if update_frequency in dataset.keys() and update_frequency!="":
			extras.update({"update_frequency":dataset[update_frequency]})
		  if state in dataset.keys() and state!="":
			extras.update({"state":dataset[state]})
		  if temporal_coverage in dataset.keys() and temporal_coverage!="":
			extras.update({"temporal_coverage":dataset[temporal_coverage]})
		  if city in dataset.keys() and city!="":
			extras.update({"city":dataset[city]})
		  extras.update({"language":language})
		  content.update({"extras":extras})
		  
		  if fetch_url=="" and "http" in harvest_object.guid:
			content.update({"url":harvest_object.guid})
		  else:
			content.update({"url":fetch_url})
		  content.update({'id':harvest_object.guid})
		  
		  ##resources
		  final_resources=[]
		  if resources in dataset.keys() and resources!="":
			resources_list=dataset[resources]
		  else:
			resources_list=[]

		  if len(resources_list)>0:
			i=0
			while i<len(resources_list):
			  resource={}
			  if resources_url in resources_list[i].keys() and resources_url!="":
				resource.update({"url":resources_list[i][resources_url]})
				#final_resources.append(resource)
				if resources_size in resources_list[i].keys() and resources_size!="":
				  resource.update({"size":resources_list[i][resources_size]})
				#final_resources.append(resource)
				if resources_mimetype in resources_list[i].keys() and resources_mimetype!="":
				  resource.update({"mimetype":resources_list[i][resources_mimetype]})
				#final_resources.append(resource)
				if resources_format in resources_list[i].keys() and resources_format!="":
				  resource.update({"format":resources_list[i][resources_format]})
			  if len(resource.keys())>0:
				final_resources.append(resource)
			  i+=1
		
		  content.update({"resources":final_resources})
	#print(content)	  
        harvest_object.content = json.dumps(content)
        harvest_object.save()


        return True

    def import_stage(self,harvest_object):
        '''
        Imports each dataset from custom, into the CKAN server
        '''
        log.debug('In CustomHarvester import_stage')
        print('In CustomoftHarvester import_stage')
        if not harvest_object:
            log.error('No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id,
                    harvest_object, 'Import')
            return False

        self._set_config(harvest_object.job.source.config)


        package_dict = json.loads(harvest_object.content)
     
        
        log.debug(harvest_object.job.source.config)
        try:
            #log.debug(harvest_object.content)


            package_dict.update({"catalogue_url":str(harvest_object.source.url)})
            package_dict.update({"platform":"genericapi"})
            package_dict.update({"name":package_dict['id'].lower().strip()})
           

            mainurl=str(harvest_object.source.url)
            #if package_dict['id'] not in ids:
            document=custom_db.find_one({"catalogue_url":harvest_object.source.url,'id':package_dict['id']})
            if document==None:
                  metadata_created=datetime.datetime.now()
                  package_dict.update({"metadata_created":str(metadata_created)})
                  custom_db.save(package_dict)
                  log.info('Metadata saved succesfully to MongoDb.')
                  fetch_document=db_fetch_temp.find_one()
		  if fetch_document==None:
			fetch_document={}
			fetch_document.update({"cat_url":mainurl})
			fetch_document.update({"new":1})
			fetch_document.update({"updated":0})
			db_fetch_temp.save(fetch_document)
		  else:
			if mainurl==fetch_document['cat_url']:
			  new_count=fetch_document['new']
			  new_count+=1
			  fetch_document.update({"new":new_count})
			  db_fetch_temp.save(fetch_document)
			else:
			  last_cat_url=fetch_document['cat_url']
			  doc=db_jobs.find_one({'cat_url':fetch_document['cat_url']})
			  if 'new' in fetch_document.keys():
				new=fetch_document['new']
				if 'new' in doc.keys():
				  last_new=doc['new']
				  doc.update({"last_new":last_new})
				doc.update({"new":new})
				db_jobs.save(doc)
			  if 'updated' in fetch_document.keys():
				updated=fetch_document['updated']
				if 'updated' in doc.keys():
				  last_updated=doc['updated']
				  doc.update({"last_updated":last_updated})
				doc.update({"updated":updated})
				db_jobs.save(doc)
			  fetch_document.update({"cat_url":mainurl})
			  fetch_document.update({"new":1})
			  fetch_document.update({"updated":0})
			  db_fetch_temp.save(fetch_document)
            else:
                  met_created=document['metadata_created']
                  if 'copied' in document.keys():
                      package_dict.update({'copied':document['copied']})
                  package_dict.update({'metadata_created':met_created})
                  package_dict.update({'metadata_updated':str(datetime.datetime.now())})
                  package_dict.update({'updated_dataset':True})
                  existing_dataset=custom_db.find_one({"id":package_dict['id'],"catalogue_url":mainurl})
                  objectid=existing_dataset['_id']
                  package_dict.update({'_id':objectid})
                  custom_db.save(package_dict)
                  log.info('Metadata updated succesfully to MongoDb.')
                  fetch_document=db_fetch_temp.find_one()
		  if fetch_document==None:
			fetch_document={}
			fetch_document.update({"cat_url":mainurl})
			fetch_document.update({"updated":1})
			fetch_document.update({"new":0})
			db_fetch_temp.save(fetch_document)
		  else:
			if mainurl==fetch_document['cat_url']:
			  updated_count=fetch_document['updated']
			  updated_count+=1
			  fetch_document.update({"updated":updated_count})
			  db_fetch_temp.save(fetch_document)
			else:
			  last_cat_url=fetch_document['cat_url']
			  doc=db_jobs.find_one({'cat_url':fetch_document['cat_url']})
			  if 'new' in fetch_document.keys():
				new=fetch_document['new']
				if 'new' in doc.keys():
				  last_new=doc['new']
				  doc.update({"last_new":last_new})
				doc.update({"new":new})
				db_jobs.save(doc)
			  if 'updated' in fetch_document.keys():
				updated=fetch_document['updated']
				if 'updated' in doc.keys():
				  last_updated=doc['updated']
				  doc.update({"last_updated":last_updated})
				doc.update({"updated":updated})
				db_jobs.save(doc)
			  fetch_document.update({"cat_url":mainurl})
			  fetch_document.update({"updated":1})
			  fetch_document.update({"new":0})
			  db_fetch_temp.save(fetch_document)	



            # Set default tags if needed
            default_tags = self.config.get('default_tags',[])
            if default_tags:
                if not 'tags' in package_dict:
                    package_dict['tags'] = []
                package_dict['tags'].extend([t for t in default_tags if t not in package_dict['tags']])


            # Set default groups if needed
            default_groups = self.config.get('default_groups',[])
            if default_groups:
                if not 'groups' in package_dict:
                    package_dict['groups'] = []
                package_dict['groups'].extend([g for g in default_groups if g not in package_dict['groups']])

            log.debug(package_dict)

            result = self._create_or_update_package(package_dict,harvest_object)
            #log.debug(result)

            if result and self.config.get('read_only',False) == True:
                package = model.Package.get(package_dict['id'])

                # Clear default permissions
                model.clear_user_roles(package)

                # Setup harvest user as admin
                user_name = self.config.get('user',u'harvest')
                user = model.User.get(user_name)
                pkg_role = model.PackageRole(package=package, user=user, role=model.Role.ADMIN)

                # Other users can only read
                for user_name in (u'visitor',u'logged_in'):
                    user = model.User.get(user_name)
                    pkg_role = model.PackageRole(package=package, user=user, role=model.Role.READER)
            return True



        except ValidationError,e:
            self._save_object_error('Invalid package with GUID %s: %r' % (harvest_object.guid, e.error_dict),
                    harvest_object, 'Import')
            print('ValidationError')
        except Exception, e:
            self._save_object_error('%r'%e,harvest_object,'Import')
            print('Exception')

