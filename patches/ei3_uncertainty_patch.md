# Patch for ecoinvent 3.x uncertainty data in openLCA
The script below fixes the uncertainty data of an ecoinvent 3.x database in
openLCA as described in the 
[openLCA forum](http://forum.openlca.org/viewtopic.php?f=26&t=32357). It copies
the current `gsigma` value into the basic uncertainty field and calculates the
total uncertainty from the respective Pedigree matrix entry and the basic
uncertainty. To run the script, modify the database path in the `main` method
below and ensure that the database is closed.

**Before running this script you should backup your database.**

```python
import java.lang.Math as Math
from java.io import File

from org.openlca.core.database.derby import DerbyDatabase

# see https://www.ecoinvent.org/files/dataqualityguideline_ecoinvent_3_20130506.pdf
# pp. 77
factors = [
    [0.000, 0.0006, 0.002, 0.008, 0.04],    # Reliability
    [0.000, 0.0001, 0.0006, 0.002, 0.008],  # Completeness
    [0.000, 0.0002, 0.002, 0.008, 0.04],    # Temporal correlation
    [0.000, 2.5e-5, 0.0001, 0.0006, 0.002], # Geographical correlation
    [0.000, 0.0006, 0.008, 0.04, 0.12]      # Further technological correlation
]


def main():
    # change the path to the database here; note that the database
    # has to be closed in openLCA
    db_path = 'C:/Users/Besitzer/openLCA-data-1.4/databases/ecoinvent_3_3_apos_gdfix'
    db = DerbyDatabase(File(db_path))
    update_exchanges(db)
    db.close()


def gsd2var(gsd):
    sigma = Math.log(gsd)
    var = Math.pow(sigma, 2)
    return var


def var2gsd(var):
    sigma = Math.sqrt(var)
    gsd = Math.exp(sigma)
    return gsd


def total_gsd(entry, basic_gsd):
    """ Calculates the total uncertainty from the given Pedigree 
        matrix entry and basic uncertainty """
    e = entry.strip()
    scores = e[1:len(e)-1].split(';')
    var_sum = gsd2var(basic_gsd)
    for i in range(0, len(scores)):
        if i >= len(factors):
            print('Invalid entry %s' % entry)
            break
        row = factors[i]
        s = scores[i].strip()
        if s == 'n.a.':
            continue
        try:
            idx = int(s) - 1
            if idx >= len(row):
                print('Invalid entry %s' % entry)
                break
            var_sum += row[idx]
        except e:
            print('Invalid entry %s' % entry)
            break
    return var2gsd(var_sum)


def update_exchanges(db):
    con = db.createConnection()
    con.setAutoCommit(False)
    stmt = con.createStatement()
    stmt.setCursorName('E_UPDATE')
    query = """ SELECT distribution_type, parameter2_value, dq_entry
                FROM tbl_exchanges FOR UPDATE OF parameter2_value,
                base_uncertainty """
    cursor = stmt.executeQuery(query)
    update_stmt = """ UPDATE tbl_exchanges SET parameter2_value = ?, 
                      base_uncertainty = ?  WHERE CURRENT OF E_UPDATE """
    update = con.prepareStatement(update_stmt)
    i = 0
    while cursor.next():
        distribution_type = cursor.getInt(1)
        basic_gsd = cursor.getDouble(2)
        dq_entry = cursor.getString(3)
        if distribution_type != 1 or dq_entry is None:
            continue
        total = total_gsd(dq_entry, basic_gsd)
        update.setDouble(1, total)
        update.setDouble(2, basic_gsd)
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