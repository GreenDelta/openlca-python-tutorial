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
