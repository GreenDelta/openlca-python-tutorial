from org.openlca.core.database.derby import DerbyDatabase
from java.io import File
import org.openlca.core.model as model
from org.openlca.core.database import UnitGroupDao, FlowPropertyDao, CategoryDao,\
    FlowDao, Daos, EntityCache
from java.util import UUID, Date
from org.openlca.core.model import FlowPropertyFactor

import util
from org.openlca.core.matrix import ProductSystemBuilder
from org.openlca.core.math import CalculationSetup, SystemCalculator
from org.openlca.eigen import NativeLibrary
from org.openlca.eigen.solvers import DenseSolver
from org.openlca.core.matrix.cache import MatrixCache
from org.openlca.core.results import FullResultProvider

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

param = util.find(db, model.Parameter, 'param')
if param is None:
    param = model.Parameter()
    param.name = 'param'
    param.scope = model.ParameterScope.GLOBAL
    param.inputParameter = True
    param.value = 42.0
    util.insert(db, param)

steel_production = util.find(db, model.Process, 'Steel production')
if steel_production is None:
    steel_production = model.Process()
    steel_production.name = 'Steel production'
    steel_output = util.create_exchange(steel, 1.0)
    steel_production.exchanges.add(steel_output)
    co2_output = util.create_exchange(co2, 42)
    co2_output.amountFormula = '0.5 * param'
    steel_production.exchanges.add(co2_output)
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

system = util.find(db, model.ProductSystem, 'My System')
if system is None:
    system = model.ProductSystem()
    system.name = 'My System'
    
    system.referenceProcess = manufacturing
    qref = manufacturing.quantitativeReference
    system.referenceExchange = qref
    system.targetAmount = 1000
    system.targetFlowPropertyFactor = qref.flowPropertyFactor
    system.targetUnit = qref.unit
    
    system.getProcesses().add(manufacturing.id)
    system.getProcesses().add(steel_production.id)
    
    link = model.ProcessLink()
    link.providerId = steel_production.id
    link.flowId = steel.id
    link.processId = manufacturing.id
    link.exchangeId = util.find_exchange(steel, manufacturing).id
    system.processLinks.add(link)
    
    util.insert(db, system)
    
    # you could also use the auto-complete function:
    # see: http://greendelta.github.io/olca-modules/olca-core/apidocs/index.html
    # build = ProductSystemBuilder(...)
    # ProductSystemBuilder.autoComplete(system)

NativeLibrary.loadFromDir(File('native_lib'))
solver = DenseSolver()
m_cache = MatrixCache.createEager(db)


redef = model.ParameterRedef()
redef.value = 10
redef.name = 'param'

setup = CalculationSetup(system)
setup.parameterRedefs.add(redef)

calculator = SystemCalculator(m_cache, solver)
result = calculator.calculateFull(setup)

e_cache = EntityCache.create(db)
result_provider = FullResultProvider(result, e_cache)

import csv

csv_file = open('result.csv', 'wb')
writer = csv.writer(csv_file)

for fd in result_provider.flowDescriptors:
    for pd in result_provider.processDescriptors:
        val = result_provider.getSingleFlowResult(pd, fd)
        writer.writerow([pd.name, fd.name, val.value])
        print pd.name, fd.name, val.value

import random
for i in range(1, 10):
    redef.value = 42 * random.random()
    result = calculator.calculateFull(setup)
    print result.totalFlowResults

csv_file.close()
db.close()

