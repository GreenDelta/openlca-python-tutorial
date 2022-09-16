# coding: utf-8
# Tested with openLCA-2.0

""" Create and save a JSON file with the impact result and sankey graph parameters
of a specified product system. """

import json

from java.util.function import Consumer

from org.openlca.app.util import Labels

PATH = '/home/francois/openLCA-data-1.4/'

try:
  # Calculation variables
  PRODUCT_SYSTEM = db.get(ProductSystem, '10dad282-0bfa-4207-9278-943e4caa51f5')
  METHOD = db.get(ImpactMethod, 'b06c6f15-21bc-4dad-a5a9-d399235a3b48')

  # Sankey diagram variables
  CUTOFF = 0.0
  MAX_COUNT = 5
  IMPACT_CATEGORY = db.get(ImpactCategory, 'a2b9e7f7-acfb-4a53-9da6-aee10bf791a4')
except AttributeError, e:
  print("db is not define. Make sure the script is executed into openLCA 2.0 and that"
        "the database is open.")
  raise


def get_result():  # type: () -> Tuple[LcaResult, DqResults, CalculationSetup]
  setup = CalculationSetup.of(PRODUCT_SYSTEM).withImpactMethod(METHOD)
  calculator = SystemCalculator(db)

  result = calculator.calculate(setup)
  dq_setup = DQCalculationSetup.of(setup)
  dq_result = DQResult.of(db, dq_setup, result)

  return result, dq_result, setup


def get_impact_results(result, setup):  # type: (LcaResult, CalculationSetup) -> List[str, Any]
  results = Results.createFrom(db, setup, result)
  impact_results = []
  for impact in results.impactResults:
    impact_results.append({
      'name': Labels.name(impact.indicator),
      'amount': impact.amount,
      'unit': None if impact.indicator is None else impact.indicator.referenceUnit,
    })
  return impact_results


def get_sankey(result):  # type: (LcaResult) -> List[str, Any]
  impact_descriptor = Descriptor.of(IMPACT_CATEGORY)
  sankey = Sankey.of(impact_descriptor, result)
  sankey = sankey.withMinimumShare(CUTOFF).withMaximumNodeCount(MAX_COUNT).build()

  data = {}

  class AddNodeConsumer(Consumer):
    def accept(self, node):  # type: (Sankey.Node) -> None
      data[str(node.product.provider().id)] = {
        'name': Labels.name(node.product),
        'total': node.total,
        'direct': node.direct,
        'share': node.share,
        'providers': [n.product.provider().id for n in node.providers],
      }
      return
  sankey.traverse(AddNodeConsumer())
  return data

def get_dq_result(dq_result): # type: (DqResult) -> List[str, Any]
  # TODO: There is an issue with DQ calculation as dq_result.setup.processSystem are null here.
  data = {
    'process_system': dq_result.setup.processSystem,
    'exchange_system': dq_result.setup.exchangeSystem,
    'aggregation_type': Labels.of(dq_result.setup.aggregationType),
    'rounding_method': "up" if dq_result.setup.ceiling else "half_up",
    'na_value_handling': Labels.of(dq_result.setup.naHandling),
  }
  
  return data
  
  
if __name__ == '__main__':
  result, dq_result, setup = get_result()

  data = {
    'impact_results': get_impact_results(result, setup),
    'dq_result': get_dq_result(dq_result),
    'sankey': get_sankey(result),
  }

  with open(PATH + 'results.json', 'w') as outfile:
    json.dump(data, outfile)

