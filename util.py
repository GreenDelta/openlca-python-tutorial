from org.openlca.core.database import Daos
import org.openlca.core.model as model

def insert(db, value):
    Daos.createBaseDao(db, value.getClass()).insert(value)

def update(db, value):
    return Daos.createBaseDao(db, value.getClass()).update(value)

def delete_all(db, clazz):
    dao = Daos.createBaseDao(db, clazz)
    dao.deleteAll()

def find(db, clazz, name):
    """ Find something by name"""
    dao = Daos.createBaseDao(db, clazz)
    for item in dao.getAll():
        if item.name == name:
            return item
    return None

def find_or_create(db, clazz, name, fn):
    obj = find(db, clazz, name)
    return obj if obj is not None else fn()

def create_flow(db, name, flow_property, 
                flow_type=model.FlowType.PRODUCT_FLOW):
    flow = find(db, model.Flow, name)
    if flow is not None:
        return flow
    flow = model.Flow()
    flow.flowType = flow_type
    flow.name = name
    flow.referenceFlowProperty = flow_property
    
    fp_factor = model.FlowPropertyFactor()
    fp_factor.flowProperty = flow_property
    fp_factor.conversionFactor = 1.0
    flow.flowPropertyFactors.add(fp_factor)
    insert(db, flow)
    return flow

def create_exchange(flow, amount=1.0, is_input=False):
    e = model.Exchange()
    e.input = is_input
    e.flow = flow
    e.unit = flow.referenceFlowProperty.unitGroup.referenceUnit
    e.amountValue = amount
    e.flowPropertyFactor = flow.getReferenceFactor()
    return e

