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
from org.openlca.core.matrix import ProductSystemBuilder, LinkingConfig
from org.openlca.core.model import ProductSystem
from org.openlca.core.database import ImpactMethodDao, ProcessDao
from org.eclipse.swt.widgets import Display


def main():
    global db

    # select the processes
    processes = ModelSelectionDialog.multiSelect(ModelType.PROCESS)
    if processes is None or len(processes) == 0:
        print("No processes were selected")
        return
    print("Selected %i processes" % len(processes))

    # select the LCIA method
    method = ModelSelectionDialog.select(ModelType.IMPACT_METHOD)
    if method is None:
        print("No LCIA method was selected")
        return
    indicators = ImpactMethodDao(db).getCategoryDescriptors(method.id)
    print("Selected LCIA method '%s' with %i indicators" % 
            (method.name, len(indicators)))

    # select the CSV file where the results should be written to
    file = FileChooser.forExport('*.csv', 'export.csv')
    if file is None:
        print("No CSV file selected")
        return
    print("Selected CSV file: %s" % file.absolutePath)
    
    # init the CSV file, run calculations, and write results
    with open(file.getAbsolutePath(), 'wb') as csvfile:
        writer = csv.writer(csvfile)

        # write the indicators as column headers
        header = ['']
        for i in indicators:
            header.append('%s (%s)' % (i.name, i.referenceUnit))
        writer.writerow(header)

        # create and calculate the product systems
        for d in processes:
            print('Build product system for: %s' % d.name)
            process = ProcessDao(db).getForId(d.id)
            builder = ProductSystemBuilder(
                Cache.getMatrixCache(), LinkingConfig())
            system = builder.build(process)

            # run the calculation
            print('Calculate process: %s' % d.name)
            calculator = SystemCalculator(
                Cache.getMatrixCache(), App.getSolver())
            setup = CalculationSetup(
                CalculationType.SIMPLE_CALCULATION, system)
            setup.impactMethod = method
            result = calculator.calculateSimple(setup)

            # write results
            print('Write results for: %s' % d.name)
            row = [process.name]
            for i in indicators:
                value = result.getTotalImpactResult(i)
                row.append(value)
            writer.writerow(row)


if __name__ == "__main__":
    Display.getDefault().asyncExec(main)
```