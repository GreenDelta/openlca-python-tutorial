# Waste flows in ecoinvent 3.x
openLCA 2.x will support the downstream modelling of waste flows. The script
below changes an ecoinvent 3.x database so that it supports this way to model
waste flows. In ecoinvent 3.3, waste flows are intermediate exchanges with a
negative amount and an opposite direction than the real flow (waste treatment
processes have waste as outputs and waste producing processes as inputs).

Thus, this script first identifies possible waste flows as product flows that
have only negative values in the inputs and outputs. It then changes the flow
types of these flows and the flow directions and amount values in the exchanges
accordingly.

**Note that you should backup your database before running this script and that**
**existing product systems are not updated (which leads to wrong results when**
**they use waste flows).**

The script uses SQL with [updatable cursors](https://db.apache.org/derby/docs/10.0/manuals/develop/develop66.html)
which is a feature of Derby with which it is possible to iterate over a table and
update the rows simultaneously. This should make the script really fast.


```python
from java.util import HashSet, HashMap
from java.io import File

from org.openlca.core.database import NativeSql
from org.openlca.core.database.derby import DerbyDatabase


def main():
    # change the path to the database here; note that the database
    # has to be closed in openLCA
    db_path = 'C:/Users/Besitzer/openLCA-data-1.4/databases/ecoinvent_3_3_apos_waste'
    db = DerbyDatabase(File(db_path))
    # get the IDs of all product flows
    product_ids = get_product_ids(db)
    # identify the possible waste flows in the products
    waste_ids = waste_candidates(db, product_ids)
    # update the flow types
    update_flow_types(db, waste_ids)
    # update the exchanges
    update_exchanges(db, waste_ids)
    db.close()


def get_product_ids(db):
    sql = "SELECT id FROM tbl_flows WHERE flow_type = 'PRODUCT_FLOW'"
    ids = HashSet()
    def fn(record):
        ids.add(record.getLong(1))
        return True
    NativeSql.on(db).query(sql, fn)
    print('%i product flows in database' % ids.size())
    return ids


def waste_candidates(db, product_ids):
    sql = 'SELECT f_flow, resulting_amount_value FROM tbl_exchanges'
    all_negs = HashMap()
    def fn(record):
        flow_id = record.getLong(1)
        amount = record.getDouble(2)
        if flow_id not in product_ids:
            return True
        val = all_negs.get(flow_id)
        if val is None or val == True:
            all_negs.put(flow_id, amount < 0)
        return True
    NativeSql.on(db).query(sql, fn)
    ids = HashSet()
    for flow_id in all_negs:
        if all_negs[flow_id] == True:
            ids.add(flow_id)
    print('%i possible waste flows found' % ids.size())
    return ids
    

def update_flow_types(db, waste_ids):
    con = db.createConnection()
    con.setAutoCommit(False)
    stmt = con.createStatement()
    stmt.setCursorName('TYPE_UPDATE')
    query = 'SELECT id FROM tbl_flows FOR UPDATE OF flow_type'
    cursor = stmt.executeQuery(query)
    update_stmt = """ UPDATE tbl_flows SET flow_type = 'WASTE_FLOW' 
                      WHERE CURRENT OF TYPE_UPDATE """
    update = con.prepareStatement(update_stmt)
    i = 0
    while cursor.next():
        flow_id = cursor.getLong(1)
        if flow_id not in waste_ids:
            continue
        update.executeUpdate()
        i += 1
    cursor.close()
    stmt.close()
    update.close()
    con.commit()
    con.close()
    print('%i flows changed to waste flows' % i)


def update_exchanges(db, waste_ids):
    con = db.createConnection()
    con.setAutoCommit(False)
    stmt = con.createStatement()
    stmt.setCursorName('E_UPDATE')
    query = """ SELECT f_flow, is_input, resulting_amount_value
                FROM tbl_exchanges FOR UPDATE OF 
                is_input, resulting_amount_value """
    cursor = stmt.executeQuery(query)
    update_stmt = """ UPDATE tbl_exchanges SET IS_INPUT = ?, 
                      RESULTING_AMOUNT_VALUE = ?  WHERE CURRENT
                      OF E_UPDATE """
    update = con.prepareStatement(update_stmt)
    i = 0
    while cursor.next():
        flow_id = cursor.getLong(1)
        if flow_id not in waste_ids:
            continue
        is_input = cursor.getBoolean(2)
        value = cursor.getDouble(3)
        update.setBoolean(1, not is_input)
        update.setDouble(2, -value)
        update.executeUpdate()
        i += 1
    cursor.close()
    stmt.close()
    update.close()
    con.commit()
    con.close()
    print('%i exchanges updated' % i)


if __name__ == '__main__':
    main()

``` 
