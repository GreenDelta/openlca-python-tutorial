from org.openlca.core.database.derby import DerbyDatabase
from java.io import File
import org.openlca.core.model as model
from org.openlca.core.database import UnitGroupDao, FlowPropertyDao, CategoryDao,\
    FlowDao, Daos
from java.util import UUID, Date
from org.openlca.core.model import FlowPropertyFactor

import util

folder = 'C:/Users/Besitzer/openLCA-data-1.4/databases/example_db1'
db = DerbyDatabase(File(folder))

mass = util.find(db, model.FlowProperty, 'Mass')
if mass is None:
    
    kg = model.Unit()
    kg.name = 'kg'
    kg.conversionFactor = 1.0
    
    mass_units = model.UnitGroup()
    mass_units.name = 'Units of mass'
    mass_units.units.add(kg)
    mass_units.referenceUnit = kg
    mass_units.refId = UUID.randomUUID().toString()
    dao = UnitGroupDao(db)
    dao.insert(mass_units)
    
    mass = model.FlowProperty()
    mass.name = 'Mass'
    mass.unitGroup = mass_units
    mass.flowPropertyType = model.FlowPropertyType.PHYSICAL
    fpDao = FlowPropertyDao(db)
    fpDao.insert(mass)

#util.insert(db, flow)
#util.delete_all(db, model.Flow)
#util.delete_all(db, model.Category)

steel = util.create_flow(db, 'Steel', mass)
co2 = util.create_flow(db, 'CO2', mass, 
                       flow_type=model.FlowType.ELEMENTARY_FLOW)

steel_production = util.find(db, model.Process, 'Steel production')
if steel_production is None:
    steel_production = model.Process()
    steel_production.name = 'Steel production'
    steel_output = util.create_exchange(steel, 1.0)
    steel_production.exchanges.add(steel_output)
    steel_production.exchanges.add(util.create_exchange(co2, 42))
    steel_production.quantitativeReference = steel_output
    util.insert(db, steel_production)

product = util.create_flow(db, 'Product', mass)
manufacturing = util.find(db, model.Process, 'Manufacturing')
if manufacturing is None:
    manufacturing = model.Process()
    manufacturing.name = 'Manufacturing'
    product_output = util.create_exchange(product, 1.0)
    manufacturing.exchanges.add(product_output)
    manufacturing.quantitativeReference = product_output
    steel_input = util.create_exchange(steel, 0.5, is_input=True)
    steel_input.defaultProviderId = steel_production.id
    manufacturing.exchanges.add(steel_input)
    util.insert(db, manufacturing)

db.close()

