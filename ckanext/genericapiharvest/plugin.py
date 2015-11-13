import logging

import ckan.model           as model
import ckan.plugins         as p
import ckan.plugins.toolkit as tk
import ckan.logic           as logic

log = logging.getLogger(__name__)
assert not log.disabled

DATASET_TYPE_NAME = 'genericapiharvest'


class GenericapiHarvester(p.SingletonPlugin, tk.DefaultDatasetForm):
  
    p.implements(p.IConfigurable)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IDatasetForm)
    p.implements(p.IPackageController, inherit=True)
    p.implements(p.ITemplateHelpers)
   # p.implements(p.IFacets, inherit=True)
  

    ## IDatasetForm

    def is_fallback(self):
        return False

    def package_types(self):
        return [DATASET_TYPE_NAME]

    def package_form(self):
        return 'sources/new_source_form.html'

    def search_template(self):
        return 'sources/search.html'

    def read_template(self):
        return 'sources/read.html'

    def new_template(self):
        return 'sources/new.html'

    #def edit_template(self):
        #return 'source/edit.html'
  
    def setup_template_variables(self, context, data_dict):

        #p.toolkit.c.harvest_source = p.toolkit.c.pkg_dict

        p.toolkit.c.dataset_type = DATASET_TYPE_NAME
 
    def update_config(self, config):
        # check if new templates
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')
#        p.toolkit.add_resource('fanstatic_library', 'ckanext-harvest')
#        p.toolkit.add_resource('public/ckanext/harvest/javascript', 'harvest-extra-field')

     ## ITemplateHelpers

    def get_helpers(self):
        return {
                #'package_list_for_source': harvest_helpers.package_list_for_source,
                #'harvesters_info': harvest_helpers.harvesters_info,
                #'harvester_types': harvest_helpers.harvester_types,
                #'harvest_frequencies': harvest_helpers.harvest_frequencies,
                #'link_for_harvest_object': harvest_helpers.link_for_harvest_object,
                #'harvest_source_extra_fields': harvest_helpers.harvest_source_extra_fields,
                }

 
    ## IConfigurable interface ##

    def configure(self, config):
        ''' Apply configuration options to this plugin '''
        pass

    ## IPackageController

    def after_create(self, context, data_dict):
        if 'type' in data_dict and data_dict['type'] == DATASET_TYPE_NAME and not self.startup:
            log.info('GENERICAPIHarvest_form: Nothing important')

    def before_map(self, m):
        ''' Called before routes map is setup. '''
        controller = 'ckanext.genericapiharvest.controllers.package:CustomGenericapiHarvestController'
        m.connect('new_genericapi_harvester', '/' + DATASET_TYPE_NAME + '/generic',
            controller = controller, action = 'new_genericapi_harvester')

        #m.connect('/' + DATASET_TYPE_NAME + '/{controller}/{action}',
                            #controller = controller, action = 'read_data')


        m.connect('/' + DATASET_TYPE_NAME + '/{action}',
                controller=controller,
                  requirements=dict(action='|'.join([
                      'read_data',
                      'new_metadata',
                      'new_resource',
                      'history',
                      'read_ajax',
                      'history_ajax',
                      'follow',
                      'activity',
                      'unfollow',
                      'delete',
                      'api_data',
                  ])))


        return m
