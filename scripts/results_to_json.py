# coding: utf-8
# Tested with openLCA-2.0

""" Create and save a JSON file with the impact result and sankey graph parameters
of a specified product system.

   ┌───┐
   │ 1 │
   └───┘
    ▲ ▲
    │ │
  ┌─┘ └─┐
  │     │  
┌─┴─┐ ┌─┴─┐
│ 2 │ │ 3 │
└───┘ └───┘

The Sankey graph above is stored as follow:
"sankey": {
        "1": {
            "direct": float,
            "total": float,
            "name": string,
            "share": float,
            "providers": [2, 3]
        },
        "2": {
            ...
            "providers": []
        },
        "3": {
            ...
            "providers": []
        }
}

"""

import json

from java.util.function import Consumer

from org.openlca.app.util import Labels
from org.openlca.core.matrix.index import IndexConsumer

PATH = '/home/francois/openLCA-data-1.4/'

# Sankey diagram variables
SANKEY_CUTOFF = 0.0
MAX_COUNT = 5

# Impact analysis variable
IMPACT_CUTOFF = 0.2

try:
  # Calculation variables
  PRODUCT_SYSTEM = db.get(ProductSystem, 'ecafe549-a564-425b-9099-47a8a23926de')
  METHOD = db.get(ImpactMethod, 'b06c6f15-21bc-4dad-a5a9-d399235a3b48')

  # Impact category for the Sankey diagram.
  IMPACT_CATEGORY = db.get(ImpactCategory, 'a2b9e7f7-acfb-4a53-9da6-aee10bf791a4')
except AttributeError, e:
  print("db is not define. Make sure the script is executed into openLCA 2.0 and that"
        "the database is open.")
  raise


def get_result():  # type: () -> Tuple[LcaResult, DqResults, CalculationSetup]
  setup = CalculationSetup.of(PRODUCT_SYSTEM).withImpactMethod(METHOD)

  calculator = SystemCalculator(db)

  result = calculator.calculate(setup)
  result_item_order = ResultItemOrder.of(result)
  dq_setup = DQCalculationSetup.of(setup)
  dq_result = DQResult.of(db, dq_setup, result)

  return result, result_item_order, dq_result, setup


def get_impact_results(result, items, setup):
  # type: (LcaResult, ResultItemOrder, CalculationSetup) -> List[str, Any]
  results = Results.createFrom(db, setup, result)

  impact_results = []
  for impact in items.impacts():

    processes = []
    for process in items.processes():
      if result.getDirectImpactResult(process, impact) > IMPACT_CUTOFF:
        processes.append({
          'name': Labels.name(process),
          'category': Labels.category(process),
          'impact_result': result.getDirectImpactResult(process, impact),
          'unit': impact.referenceUnit,
        })

    flows = []

    if result.hasEnviFlows:
      class AddEnviFlowConsumer(IndexConsumer):
        def accept(self, index, envi_flow):  # type: (int, EnviFlow) -> None
          if result.getTotalFlowResult(envi_flow) > IMPACT_CUTOFF:
            flows.append({
              'name': Labels.name(envi_flow),
              'category': Labels.category(envi_flow),
              'impact_result': result.getTotalFlowResult(envi_flow),
              'unit': impact.referenceUnit,
              'timestamp': db.get(Flow, envi_flow.flow().id).lastChange,
            })
          return

      result.enviIndex().each(AddEnviFlowConsumer())

    impact_results.append({
      'name': Labels.name(impact),
      'category': Labels.category(impact),
      'impact_result': result.getTotalImpactResult(impact),
      'unit': impact.referenceUnit,
      'processes': processes,
      'envi_flows': flows,
      'cutoff': IMPACT_CUTOFF,
    })
  return impact_results


def get_sankey(result):  # type: (LcaResult) -> List[str, Any]
  impact_descriptor = Descriptor.of(IMPACT_CATEGORY)
  sankey = Sankey.of(impact_descriptor, result)
  sankey = sankey.withMinimumShare(SANKEY_CUTOFF).withMaximumNodeCount(MAX_COUNT).build()

  data = {}

  class AddNodeConsumer(Consumer):
    def accept(self, node):  # type: (Sankey.Node) -> None
      data[str(node.product.provider().id)] = {
        'name': Labels.name(node.product),
        'total': node.total,
        'direct': node.direct,
        'share': node.share,
        'providers': [n.product.provider().id for n in node.providers],
        'cutoff': SANKEY_CUTOFF,
      }
      return

  sankey.traverse(AddNodeConsumer())
  return data


def get_dq_result(dq_result):  # type: (DqResult) -> List[str, Any]
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
  print("Calculation...")
  result, result_item_order, dq_result, setup = get_result()

  data = {
    'impact_results': get_impact_results(result, result_item_order, setup),
    'dq_result': get_dq_result(dq_result),
    'sankey': get_sankey(result),
  }

  print("Saving the JSON...")
  with open(PATH + 'results.json', 'w') as outfile:
    json.dump(data, outfile)
  print("Done!")
