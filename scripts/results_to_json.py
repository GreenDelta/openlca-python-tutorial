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
MAX_COUNT = 25

# Impact analysis variable
IMPACT_CUTOFF = 0.2

try:
    # Calculation variables
    PRODUCT_SYSTEM = db.get(ProductSystem, 'f020f7ad-7ab8-4259-8b6f-f8fd1fe67814')
    METHOD = db.get(ImpactMethod, 'b06c6f15-21bc-4dad-a5a9-d399235a3b48')

    # Impact category for the Sankey diagram.
    IMPACT_CATEGORY = db.get(ImpactCategory, 'a2b9e7f7-acfb-4a53-9da6-aee10bf791a4')
except AttributeError as e:
    print("db is not define. Make sure the script is executed into openLCA 2.0 and that"
          "the database is open.")
    raise


def get_result():  # type: () -> Tuple[LcaResult, DqResults, CalculationSetup]
    setup = CalculationSetup.of(PRODUCT_SYSTEM).withImpactMethod(METHOD)

    calculator = SystemCalculator(db)

    result = calculator.calculate(setup)
    result_item_order = ResultItemOrder.of(result)
    dq_setup = DQSetup.of(setup)
    dq_result = DQResult.of(db, dq_setup, result.provider())

    return result, result_item_order, dq_result, setup


def get_impact_results(result, items, dq_result):
    # type: (LcaResult, ResultItemOrder, DqResults) -> List[str, Any]
    impact_results = []
    for impact in items.impacts():

        tech_flows = []

        for tech_flow in items.techFlows():
            if result.getDirectImpactOf(impact, tech_flow) > IMPACT_CUTOFF:
                process_descriptor = tech_flow.provider()
                process = db.get(Process, process_descriptor.id)
                data_quality = dq_result.get(impact, tech_flow)
                tech_flows.append({
                    'name': Labels.name(process_descriptor),
                    'category': Labels.category(process_descriptor),
                    'impact_result': result.getDirectImpactOf(impact, tech_flow),
                    'unit': impact.referenceUnit,
                    'validFrom': process.documentation.validFrom,
                    'validUntil': process.documentation.validUntil,
                    'data_quality': data_quality.tolist() if data_quality is not None else [],
                })

        envi_flows = []
        for envi_flow in items.enviFlows():
            if result.getFlowImpactOf(impact, envi_flow) > IMPACT_CUTOFF:
                data_quality = dq_result.get(envi_flow)

                envi_flows.append({
                    'name': Labels.name(envi_flow),
                    'category': Labels.category(envi_flow),
                    'impact_result': result.getFlowImpactOf(impact, envi_flow),
                    'unit': impact.referenceUnit,
                    'data_quality': data_quality.tolist() if data_quality is not None else [],
                })

        data_quality = dq_result.get(impact)
        impact_results.append({
            'name': Labels.name(impact),
            'category': Labels.category(impact),
            'impact_result': result.getTotalImpactValueOf(impact),
            'unit': impact.referenceUnit,
            'processes': tech_flows,
            'envi_flows': envi_flows,
            'cutoff': IMPACT_CUTOFF,
            'data_quality': data_quality.tolist() if data_quality is not None else [],
        })
    return impact_results


def get_sankey(result):  # type: (ResultProvider) -> List[str, Any]
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
    return {
        'aggregation_type': Labels.of(dq_result.setup.aggregationType),
        'rounding_method': "up" if dq_result.setup.ceiling else "half_up",
        'na_value_handling': Labels.of(dq_result.setup.naHandling),
    }


if __name__ == '__main__':
    print("Calculation...")
    result, result_item_order, dq_result, setup = get_result()

    data = {
        'impact_results': get_impact_results(result, result_item_order, dq_result),
        'dq_result_info': get_dq_result(dq_result),
        'sankey': get_sankey(result.provider()),
    }

    print("Saving the JSON...")
    with open(PATH + 'results.json', 'w') as outfile:
        json.dump(data, outfile)
    print("Done!")
