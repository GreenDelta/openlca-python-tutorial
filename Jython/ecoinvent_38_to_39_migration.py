#coding: utf-8
#Tested with openLCA 2.0.0

"""
Goal:
This script will convert all the foreground proccesses as well as the associated product systems that were imported from
an Ecoinvent3.8 database to an Ecoinvent3.9 database. You will be asked to select a json conversion file for the 
conversion process to work. This file should be given to you together with this script. For this script to work, please 
make sure that you do not save your foreground model in any of the folders that are native to the Ecoinvent database. 

Usage:
1. Export the product system of your foreground model as a json-ld file (suffix: '.zip') from your Ecoinvent 3.8 
   database
2. Import this json-ld product system file into your Ecoinvent3.9 database (Keep 'Never update a data set that already 
   exists' selected)
   HINT: Before running the script, I would recommend making a backup of your current Ecoinvent database!
3. Have this script open and click on the green play button on the top left of the screen to run script.
4. You will need to choose the a json conversion file that can be downloaded under this link: 
   https://share.greendelta.com/index.php/s/eqg54j6mlbUilqx. It is important that you choose the file appropriate for 
   your type of Ecoinvent database!
   HINT: If you do NOT recieve any information about updated or deleted providers within each foreground process, the 
   migration has not worked! If this happens, please check if you have used the correct mapping JSON file for your 
   Ecoinvent database type.
5. Before viewing the changes made to the database, close and reopen the database.

PLEASE NOTE: 
This script will only work when converting from Ecoinvent3.8 to Ecoinvent3.9!
For this script to work, please make sure that you do not save your foreground model in any of the folders that are 
native to the Ecoinvent database! 
Furthermore, this script will always recalculate all the product systems in the database as the processes contained 
within each product system will have changed.
This script only works with a fully linked product system. 
"""

import json

from org.openlca.app.components import FileChooser
from org.eclipse.jface.dialogs import MessageDialog


ECOINVENT_PARENT_CATEGORY_LIST = [
  'A:Agriculture, forestry and fishing',
  'B:Mining and quarrying',
  'C:Manufacturing',
  'D:Electricity, gas, steam and air conditioning supply',
  'E:Water supply; sewerage, waste management and remediation activities',
  'F:Construction',
  'G:Wholesale and retail trade; repair of motor vehicles and motorcycles',
  'H:Transportation and storage',
  'I:Accommodation and food service activities',
  'J:Information and communication',
  'M:Professional, scientific and technical activities',
  'N:Administrative and support service activities',
  'S:Other service activities',
  ]


def filter_processes():
  """This function will split the foreground and background processes in the database. For this function to work, none 
  of the foreground processes should be saved inside any of the original folders of the ecoinvent database. This 
  function returns a list, that contains all foreground processes."""
  
  foreground_process_category_list = []
  for process in db.getAll(Process):
    category = process.category
    if category is None:
      foreground_process_category_list.append(process)    
    
    else:
      path = category.toPath()
    
      if not any(elem in path for elem in ECOINVENT_PARENT_CATEGORY_LIST):
        foreground_process_category_list.append(process)
    
  return foreground_process_category_list
     

def migrate_providers_of_all_foreground_processes(mapping_dict):
  """This function exchanges all the providers of all the foreground processes inside the database if an analog exists 
  in the mapping dictionary which will be derived from an external json file."""
  
  foreground_processes = filter_processes()
  process_dao = ProcessDao(db)
  for foreground_process in foreground_processes:
    for exchange in foreground_process.exchanges:
      if exchange.defaultProviderId != 0:
        provider = db.get(Process, exchange.defaultProviderId)
        if provider.refId in mapping_dict:
          new_refId_info = mapping_dict[provider.refId]
          if new_refId_info is None or len(new_refId_info) == 0:
            MessageDialog.openError(
              None, "Error", "The input JSON does not contain the following process ID: " + provider.refId
              )
            return
          new_provider = db.get(Process, new_refId_info[0])
          exchange.defaultProviderId = new_provider.id
          print('Updated the provider for "%s" to "%s" (%s) in process "%s" (%s).' % (
            exchange.flow.name, new_provider.name, 
            new_provider.refId, 
            foreground_process.name, 
            foreground_process.refId
            ))
    process_dao.update(foreground_process)
  for process in db.getAll(Process):
    if process.refId in mapping_dict:
      old_ref_id = process.refId
      process_dao.delete(process)
      print('Deleted outdated Ecoinvent3.8 process "%s" (%s)' % (process.name, old_ref_id))
      
def update_product_system():
  """This function reevaluates the existing product systems inside the database."""
  
  product_system_dao = ProductSystemDao(db)
  DESCRIPTION_ADDITION = "\n\nThis product system was recalculated as it originates from Ecoinvent3.8!!!"
  for product_system in db.getAll(ProductSystem):
    p = product_system.referenceProcess
    config = LinkingConfig()\
      .providerLinking(ProviderLinking.PREFER_DEFAULTS)\
      .preferredType(ProcessType.UNIT_PROCESS)
    new_product_system = ProductSystemBuilder(MatrixCache.createLazy(db), config)\
      .build(p)

    new_product_system.name = product_system.name 
    new_product_system.refId = product_system.refId
    new_product_system.targetUnit = product_system.targetUnit
    new_product_system.targetAmount = product_system.targetAmount
    new_product_system.cutoff = product_system.cutoff 
    new_product_system.referenceExchange = product_system.referenceExchange 
    new_product_system.referenceProcess = product_system.referenceProcess 
    new_product_system.targetFlowPropertyFactor = product_system.targetFlowPropertyFactor
    if product_system.description == None:
      new_product_system.description = DESCRIPTION_ADDITION    
    elif not product_system.description.endswith(DESCRIPTION_ADDITION):
      new_product_system.description = product_system.description + DESCRIPTION_ADDITION
    else:
      new_product_system.description = product_system.description
    product_system_dao.insert(new_product_system)
    product_system_dao.delete(product_system)
   
    print('Updated the product system "%s" (%s)' % (product_system.name, product_system.refId))

def main():
  """Call a file chooser with which the above code will be initiated."""
  
  #select the json file
  file = FileChooser.open('*.json')
  if file is None:
      MessageDialog.openError(None, "Error", "You must select a json file")
      return 
  
  #open json file  
  with open(str(file), 'r') as read_file:
    mapping_obj = json.load(read_file)

  #check mapping file
  for val in mapping_obj.values():
    if not len(val) == 3: 
      MessageDialog.openError(None, "Error", "You must select the correct json file")
      return 

  #migrate all foreground process providers to ecoinvent3.9 providers
  migrate_providers_of_all_foreground_processes(mapping_obj)
   
  #update all product systems in the database 
  update_product_system()
    
if __name__=='__main__':
  App.runInUI("Migrating processes", main)
