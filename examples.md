## Examples

### Create a unit and unit group

```python
from org.openlca.core.database.derby import DerbyDatabase
from java.io import File
import org.openlca.core.model as model
from org.openlca.core.database import UnitGroupDao, FlowPropertyDao
from java.util import UUID

# path to our database
folder = 'C:/Users/Besitzer/openLCA-data-1.4/databases/example_db1'
db = DerbyDatabase(File(folder))

# unit and unit group
kg = model.Unit()
kg.name = 'kg'
kg.conversionFactor = 1.0

mass_units = model.UnitGroup()
mass_units.name = 'Units of mass'
mass_units.units.add(kg)
mass_units.referenceUnit = kg
mass_units.refId = UUID.randomUUID().toString()

# create a data access object and insert it in the database
dao = UnitGroupDao(db)
dao.insert(mass_units)
```

### Create a flow property

```python
mass = model.FlowProperty()
mass.name = 'Mass'
mass.unitGroup = mass_units
mass.flowPropertyType = model.FlowPropertyType.PHYSICAL
fpDao = FlowPropertyDao(db)
fpDao.insert(mass)
```

### Create a flow with category

```python
category = model.Category()
category.refId = UUID.randomUUID().toString();
category.name = 'products'
category.modelType = model.ModelType.FLOW
CategoryDao(db).insert(category)

flow = model.Flow()
flow.name = 'Steel'
flow.category = category
flow.referenceFlowProperty = mass

fp_factor = FlowPropertyFactor()
fp_factor.flowProperty = mass
fp_factor.conversionFactor = 1.0
flow.flowPropertyFactors.add(fp_factor)
FlowDao(db).insert(flow)
```

### Update a flow

```python
flow = util.find_or_create(db, model.Flow, 'Steel', create_flow)
flow.description = 'My first flow ' + str(Date())
flow = util.update(db, flow)
```


### Create generic database functions

```python
from org.openlca.core.database import Daos

def insert(db, value):
    Daos.createBaseDao(db, value.getClass()).insert(value)

def delete_all(db, clazz):
    dao = Daos.createBaseDao(db, clazz)
    dao.deleteAll()

def find(db, clazz, name):
    """ Find something by name"""
    dao = Daos.createBaseDao(db, clazz)
    for item in dao.getAll():
        if item.name == name:
            return item
```

### Create a process

```python
process = model.Process()
process.name = 'Steel production'

steel_output = model.Exchange()
steel_output.input = False
steel_output.flow = flow
steel_output.unit = kg
steel_output.amountValue = 1.0
steel_output.flowPropertyFactor = flow.getReferenceFactor()

process.exchanges.add(steel_output)
process.quantitativeReference = steel_output

util.insert(db, process)
```


### Update a process

```python
from org.openlca.core.database.derby import DerbyDatabase as Db
from java.io import File
from org.openlca.core.database import ProcessDao

if __name__ == '__main__':
    db_dir = File('C:/Users/Besitzer/openLCA-data-1.4/databases/openlca_lcia_methods_1_5_5')
    db = Db(db_dir)
    
    dao = ProcessDao(db)
    p = dao.getForName("p1")[0]
    p.description = 'Test 123'
    dao.update(p)
    
    db.close()
```

### Insert a new parameter
* create a parameter and insert it into a database

```python
from org.openlca.core.database.derby import DerbyDatabase
from org.openlca.core.model import Parameter, ParameterScope
from java.io import File
from org.openlca.core.database import ParameterDao

if __name__ == '__main__':
    param = Parameter()
    param.scope = ParameterScope.GLOBAL
    param.name = 'k_B'
    param.inputParameter = True
    param.value = 1.38064852e-23
    
    db_dir = File('C:/Users/Besitzer/openLCA-data-1.4/databases/ztest')
    db = DerbyDatabase(db_dir)
    dao = ParameterDao(db)
    dao.insert(param)
    db.close()
```


### Update a parameter

```python
from java.io import File
from org.openlca.core.database.derby import DerbyDatabase
from org.openlca.core.database import ParameterDao

if __name__ == '__main__':
    db_dir = File('C:/Users/Besitzer/openLCA-data-1.4/databases/ztest')
    db = DerbyDatabase(db_dir)
    dao = ParameterDao(db)
    param = dao.getForName('k_B')[0]
    param.value = 42.0    
    dao.update(param)
    db.close()
```


### Run a calculation
* connect to a database and load a product system
* load the optimized, native libraries
* calculate and print the result

```python
from java.io import File
from org.openlca.core.database.derby import DerbyDatabase
from org.openlca.core.database import ProductSystemDao, EntityCache
from org.openlca.core.matrix.cache import MatrixCache
from org.openlca.eigen import NativeLibrary
from org.openlca.eigen.solvers import DenseSolver
from org.openlca.core.math import CalculationSetup, SystemCalculator
from org.openlca.core.results import ContributionResultProvider

if __name__ == '__main__':
    # load the product system
    db_dir = File('C:/Users/Besitzer/openLCA-data-1.4/databases/ei_3_3_apos_dbv4')
    db = DerbyDatabase(db_dir)
    dao = ProductSystemDao(db)
    system = dao.getForName('rice production')[0]
    
    # caches, native lib., solver
    m_cache = MatrixCache.createLazy(db)
    e_cache = EntityCache.create(db)
    NativeLibrary.loadFromDir(File('../native'))
    solver = DenseSolver()
    
    # calculation
    setup = CalculationSetup(system)
    calculator = SystemCalculator(m_cache, solver)
    result = calculator.calculateContributions(setup)
    provider = ContributionResultProvider(result, e_cache)
    
    for flow in provider.flowDescriptors:
        print flow.getName(), provider.getTotalFlowResult(flow).value
    
    db.close()
```

### Using the formula interpreter

```python
from org.openlca.expressions import FormulaInterpreter

if __name__ == '__main__':
    fi = FormulaInterpreter()
    gs = fi.getGlobalScope()
    gs.bind('a', '1+1')
    ls = fi.createScope(1)
    print ls.eval('2*a')
```

### Get weighting results

```python
from java.io import File
from org.openlca.core.database.derby import DerbyDatabase
from org.openlca.core.database import ProductSystemDao, EntityCache,\
    ImpactMethodDao, NwSetDao
from org.openlca.core.matrix.cache import MatrixCache
from org.openlca.eigen import NativeLibrary
from org.openlca.eigen.solvers import DenseSolver
from org.openlca.core.math import CalculationSetup, SystemCalculator
from org.openlca.core.model.descriptors import Descriptors
from org.openlca.core.results import ContributionResultProvider
from org.openlca.core.matrix import NwSetTable


if __name__ == '__main__':
    # load the product system
    db_dir = File('C:/Users/Besitzer/openLCA-data-1.4/databases/openlca_lcia_methods_1_5_5')
    db = DerbyDatabase(db_dir)
    dao = ProductSystemDao(db)
    system = dao.getForName('s1')[0]
    
    # caches, native lib., solver
    m_cache = MatrixCache.createLazy(db)
    e_cache = EntityCache.create(db)
    NativeLibrary.loadFromDir(File('../native'))
    solver = DenseSolver()
    
    # calculation
    setup = CalculationSetup(system)
    setup.withCosts = True
    method_dao = ImpactMethodDao(db)
    setup.impactMethod = Descriptors.toDescriptor(method_dao.getForName('eco-indicator 99 (E)')[0])
    nwset_dao = NwSetDao(db)
    setup.nwSet = Descriptors.toDescriptor(nwset_dao.getForName('Europe EI 99 E/E [person/year]')[0])
    calculator = SystemCalculator(m_cache, solver)
    result = calculator.calculateContributions(setup)
    provider = ContributionResultProvider(result, e_cache)
    
    for i in provider.getTotalImpactResults():
        if i.value != 0:
            print i.impactCategory.name, i.value
    
    # weighting
    nw_table = NwSetTable.build(db, setup.nwSet.id)    
    weighted = nw_table.applyWeighting(provider.getTotalImpactResults())
    for i in weighted:
        if i.value != 0:
            print i.impactCategory.name, i.value
    
    print provider.totalCostResult
    db.close()
    
```

### Using the sequential solver

```python
import org.openlca.core.math.CalculationSetup as Setup
import org.openlca.app.db.Cache as Cache
import org.openlca.core.math.SystemCalculator as Calculator
import org.openlca.core.results.ContributionResultProvider as Provider
import org.openlca.app.results.ResultEditorInput as EditorInput
import org.openlca.eigen.solvers.SequentialSolver as Solver
import org.openlca.app.util.Editors as Editors

solver = Solver(1e-12, 1000000)
solver.setBreak(0, 1)
system = olca.getSystem('preparation')
setup = Setup(system)
calculator = Calculator(Cache.getMatrixCache(), solver)
result = calculator.calculateContributions(setup)
provider = Provider(result, Cache.getEntityCache())
input = EditorInput.create(setup, provider)
Editors.open(input, "QuickResultEditor")

for i in solver.iterations:
  print i
```

### Using SQL

```python
from org.openlca.core.database.derby import DerbyDatabase
from java.io import File
from org.openlca.core.database import NativeSql

folder = 'C:/Users/Besitzer/openLCA-data-1.4/databases/example_db1'
db = DerbyDatabase(File(folder))

query = 'select * from tbl_unit_groups'

def fn(r):
    print r.getString('REF_ID')
    return True

# see http://greendelta.github.io/olca-modules/olca-core/apidocs/org/openlca/core/database/NativeSql.html
NativeSql.on(db).query(query, fn)
```

### Create a location with KML data
The example below creates a location with [KML](https://developers.google.com/kml/documentation/kmlreference)
data and stores it in the database. 

```python
import org.openlca.util.BinUtils as BinUtils
import org.openlca.core.database.LocationDao as Dao

loc = Location()
loc.name = 'Points'
loc.code = 'POINTS'

kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <MultiGeometry>
      <Point>
        <coordinates>5.0,7.5</coordinates>
      </Point>
      <Point>
        <coordinates>5.0,2.5</coordinates>
      </Point>
      <Point>
        <coordinates>15.0,5.0</coordinates>
      </Point>
    </MultiGeometry>
  </Placemark>
</kml>
'''.strip()

loc.kmz = BinUtils.zip(kml)
dao = Dao(db)
dao.insert(loc)
```

### Export used elementary flows to a CSV file
The following script exports the elementary flows that are used in processes
of the currently activated databases into a CSV file.

```python
import csv
from org.openlca.core.database import FlowDao, NativeSql
from org.openlca.util import Categories


# set the path to the resulting CSV file here
CSV_FILE = 'C:/Users/ms/Desktop/used_elem_flows.csv'

def main():
    global db

    # collect the IDs of the used elementary flows
    # via an SQL query
    ids = set()
    sql = '''
    SELECT DISTINCT f.id FROM tbl_flows f
      INNER JOIN tbl_exchanges e ON f.id = e.f_flow
      WHERE f.flow_type = 'ELEMENTARY_FLOW'
    '''

    def collect_ids(r):
        ids.add(r.getLong(1))
        return True

    NativeSql.on(db).query(sql, collect_ids)

    # load the flows and write them to a CSV file
    flows = FlowDao(db).getForIds(ids)
    with open(CSV_FILE, 'wb') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow([
            'Ref. ID', 'Name', 'Category', 'Ref. Flow property', 'Ref. Unit'
        ])

        for flow in flows:
            writer.writerow([
                flow.refId,
                flow.name,
                '/'.join(Categories.path(flow.category)),
                flow.referenceFlowProperty.name,
                flow.referenceFlowProperty.unitGroup.referenceUnit.name
            ])

if __name__ == '__main__':
    main()
```

### Calculate a product system with many different parameter values that are read from a csv file, and store the results in Excel
This script uses the IPC server of openLCA for connecting via Python to openLCA. 

It calculates all product systems existing in the selected database with an LCIA method
from this database that is identified by name. The calculations are done for all parameter sets in the csv file. 

To use it, adapt the LCIA method name and the paths to the csv file and to the Excel file. Create the csv file with UUID of parameter, name of parameter, then the parameter values in different columns, one per set. You can also extend the number of parameters sets (in the script and, correspondingly, in the csv file). Then, start the IPC server in openLCA with port 8080. Execute the script in an external Python IDE such as PyCharm or similar.

```python
import csv
import os
import sys

import olca
import pandas
import arrow as ar


def main():

    # the Excel files with the results are written to the `output` folder
    if not os.path.exists('output'):
        os.makedirs('output')

    start = ar.now()
    # make sure that you started an IPC server with the specific database in
    # openLCA (Window > Developer Tools > IPC Server)
    client = olca.Client(8080)

    # first we read the parameter sets; they are stored in a data frame where
    # each column is a different parameter set
	# 1st column: parameter UUID
	# 2nd column: parameter name
	# last column: process name, for documentation
    parameters = read_parameters(
        'relative/path/to/csvfile.csv')

    # we prepare a calculation setup for the given LCIA method and reuse it
    # for the different product systems in the database
    calculation_setup = prepare_setup(client, 'The Name of the LCIA method')

    # we run a calculation for each combination of parameter set and product
    # system that is in the database
    for system in client.get_descriptors(olca.ProductSystem):
        print('Run calculations for product system %s (%s)' %
              (system.name, system.id))
        calculation_setup.product_system = system
        for parameter_set in range(0, parameters.shape[1]):
            set_parameters(calculation_setup, parameters, parameter_set)

            try:
                calc_start = ar.now()
                print('  . run calculation for parameter set %i' % parameter_set)
                result = client.calculate(calculation_setup)
                print('  . calculation finished in', ar.now() - calc_start)

                # we store the Excel file under
                # `output/<system id>_<parameter set>.xlsx`
                excel_file = 'output/%s_%d.xlsx' % (system.id, parameter_set)
                export_and_dispose(client, result, excel_file)

            except Exception as e:
                print('  . calculation failed: %s' % e)

    print('All done; total runtime', ar.now() - start)


def read_parameters(file_path: 'file\path') -> pandas.DataFrame:
    """ Read the given parameter table into a pandas data frame where the
        parameter names are mapped to the index.
	    assumption: not more than 5 sets - if there are more, the row index and the csv file can be changed
    """
    index = []
    data = []
    with open(file_path, 'r', encoding='cp1252') as stream:
        reader = csv.reader(stream, delimiter=';')
        rows = []
        for row in reader:
            index.append(row[1])
            data.append([float(x) for x in row[2:7]])
        return pandas.DataFrame(data=data, index=index)


def prepare_setup(client: olca.Client, method_name: str) -> olca.CalculationSetup:
    """ Prepare the calculation setup with the LCIA method with the given name.
        Note that this is just an example. You can of course get a method by
        ID, calculate a system with all LCIA methods in the database etc.
    """
    method = client.find(olca.ImpactMethod, method_name)
    if method is None:
        sys.exit('Could not find LCIA method %s' % method_name)
    setup = olca.CalculationSetup()
    # currently, simple calculation, contribution analysis, and upstream
    # analysis are supported
    setup.calculation_type = olca.CalculationType.CONTRIBUTION_ANALYSIS
    setup.impact_method = method
    # amount is the amount of the functional unit (fu) of the system that
    # should be used in the calculation; unit, flow property, etc. of the fu
    # can be also defined; by default openLCA will take the settings of the
    # reference flow of the product system
    setup.amount = 1.0
    return setup


def set_parameters(setup: olca.CalculationSetup, parameters: pandas.DataFrame,
                   parameter_set: int):
    """ Set the parameters of the given parameter set (which is the
        corresponding column in the data frame) to the calculation setup.
    """
    # for each parameter in the parameter set we add a parameter
    # redefinition in the calculation setup which will set the parameter
    # value for the respective parameter just for the calculation (without
    # needing to modify the database)
    setup.parameter_redefs = []
    for param in parameters.index:
        redef = olca.ParameterRedef()
        redef.name = param
        redef.value = parameters.ix[param, parameter_set]
        setup.parameter_redefs.append(redef)


def export_and_dispose(client: olca.Client, result: olca.SimpleResult, path: str):
    """ Export the given result to Excel and dispose it after the Export
        finished.
    """
    try:
        print('  . export result to', path)
        start = ar.now()
        client.excel_export(result, path)
        time = ar.now() - start
        print('  . export finished after', time)
        print('  . dispose result')
        client.dispose(result)
        print('  . done')
    except Exception as e:
        print('ERROR: Excel export or dispose of %s failed' % path)


if __name__ == '__main__':
    main()
```

The csv file can look as follows, one line per parameter:

484895ce-a443-4cc4-8864-a10a407e93aa;para1;0.014652146;0.014718301;0.017931926;0.020983646;0.020427708;;;processname 1
8fc4c8a5-8e98-46b7-9a21-d1d8481e5aa4;para2;0.030556766;0.034429313;0.044245529;0.047132534;0.049762465;;;processname 2
66a0200f-ce81-494c-8131-1aee0c0a59f2;NP3;0.016611061;0.010960006;0.005260319;0.002222134;0.00099458;;;processname 3
410ed118-4201-47d3-88bd-da6af3bfd555;NP4;0;0.00017588;0.000994777;0.001486167;0.001806687;;;processname 4
247b42d0-9715-465f-9500-61fc51bbfe84;NP4;0.015608129;0.018301197;0.017860159;0.016049407;0.015421637;;;processname 5
f90551c7-3c92-474f-9d10-03562ed8c8ae;NP5;0.008727944;0.010233887;0.009987262;0.008974703;0.008623659;;;processname 6
19063103-a7b5-4f61-9a3a-c3ec44133c67;NP6;0.005293286;0.006206604;0.006057032;0.005442939;0.00523004;;;processname 7
