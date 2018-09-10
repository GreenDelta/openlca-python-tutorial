## Working with product systems
The script below explains how to create a product system, and shows how to
calculate, export LCIA results as csv, and delete it again finally. For
selecting the reference process and the LCIA method, a dialogue pops up. 


```python
import csv
from org.openlca.app import App
from org.openlca.app.components import FileChooser, ModelSelectionDialog
from org.openlca.app.db import Cache
from org.openlca.core.math import CalculationSetup, CalculationType, SystemCalculator
from org.openlca.core.matrix import ProductSystemBuilder
from org.openlca.core.model import ModelType, ProductSystem
from org.openlca.core.model.descriptors import Descriptors
from org.openlca.core.database import ImpactMethodDao, ProcessDao, ProductSystemDao
from org.openlca.core.results import ContributionResultProvider
from org.eclipse.swt.widgets import Display
from java.lang import Long
from java.util import UUID

processDao = ProcessDao(db)
systemDao = ProductSystemDao(db)
methodDao = ImpactMethodDao(db)

def createProductSystem(process):
    system = ProductSystem()
    system.setRefId(UUID.randomUUID().toString())
    system.setName(process.getName())
    system.processes.add(Long(process.getId()))
    system.referenceProcess = process
    qRef = process.getQuantitativeReference()
    system.referenceExchange = qRef
    system.targetFlowPropertyFactor = qRef.flowPropertyFactor
    system.targetUnit = qRef.unit
    system.targetAmount = qRef.amount
    return systemDao.insert(system)

def buildProductSystem(system):
    builder = ProductSystemBuilder(Cache.getMatrixCache())
    return builder.autoComplete(system)

def calculate(system, method):
    calculator = SystemCalculator(Cache.getMatrixCache(), App.getSolver())
    setup = CalculationSetup(CalculationType.SIMPLE_CALCULATION, system)
    setup.impactMethod = Descriptors.toDescriptor(method)
    result = calculator.calculateContributions(setup)
    return ContributionResultProvider(result, Cache.getEntityCache())

def writeCategories(method, writer): 
    row = ['']
    for category in method.impactCategories:
       row.append(category.getName())
    writer.writerow(row)

def export(system, method, result, writer):
    row = [system.getName()]
    for category in method.impactCategories:
       value = result.getTotalImpactResult(Descriptors.toDescriptor(category)).value
       row.append(value)
    writer.writerow(row)

def run(process, method, writer):
    system = createProductSystem(process)
    system = buildProductSystem(system)
    result = calculate(system, method)
    export(system, method, result, writer)
    systemDao.delete(system)

def main():
    processes = ModelSelectionDialog.multiSelect(ModelType.PROCESS)
    if processes is None or len(processes) is 0:
        return
    methodDescriptor = ModelSelectionDialog.select(ModelType.IMPACT_METHOD)
    if methodDescriptor is None:
        return
    file = FileChooser.forExport('*.csv', 'export.csv')
    if file is None:
        return
    method = methodDao.getForId(methodDescriptor.getId())
    with open(file.getAbsolutePath(), 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writeCategories(method, writer)
        for descriptor in processes:
            process = processDao.getForId(descriptor.getId())
            run(process, method, writer)

Display.getDefault().asyncExec(main)
```