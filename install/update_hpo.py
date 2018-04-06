#!/usr/bin/python

import sys
import core.model as Model


# Prerequisite: Download HPO data (Done in makefile that call this script)
filepath = sys.argv[1]


# Clear HPO tables
Model.execute("DELETE FROM hpo_term")


# Load HPO terms data
def escape(value):
    if type(value) is str:
        value = value.replace('%', '%%')
        value = value.replace("'", "''")
        # Workaround for some annotations that can crash the script
        value = value.replace('-:0', '-: 0')   # VEP aa_maf = "-:0.1254..." for weird raison: -:0 is interpreted as {0} by format method
    return value

result = []
links = {}
with open(filepath, "r") as f:
    current = None
    lines = f.readlines()
    for l in lines:
        if l.startswith("[Term]"):
            if current != None:
                result.append(current)
            current = {"id":None, "label":None, "definition": None, "synonym":[], "parent": None}
        elif l.startswith("id: "):
            current["id"] = l[4:-1]
        elif l.startswith("name: "):
            current["label"] = l[6:-1]
        elif l.startswith("def: "):
            current["definition"] = l[6:l.rfind('"')]
        elif l.startswith("is_a: "):
            pid = l[6:16]
            if pid in links:
                links[pid].append(current["id"])
            else:
                links[pid] = [current["id"]]
            current["parent"] =pid
        elif l.startswith("synonym: "):
            current["synonym"].append(l[10:l.rfind('"')])

# Process sql query
pattern = "('{}', '{}', '{}', {}, {}, {}), "
sql = "INSERT INTO hpo_term (hpo_id, label, definition, parent, childs, search) VALUES "
for t in result:
    id = t["id"]
    label = escape(t["label"])
    definition = escape(t["definition"])
    parent = "'{}'".format(t["parent"]) if t["parent"] is not None else "NULL"
    childs = "NULL"
    if id in links:
        childs = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in links[id]]))
    search = "NULL"
    if len(t["synonym"]) > 0:
        search = "'{}'".format(escape(' '.join(t["synonym"])))
    sql += pattern.format(id, label, definition, parent, childs, search)
sql = sql[:-2]
Model.execute(sql)




# Load HPO terms-gene-diseases relations
# Done in update_hpo.sql script call in the makefile that called this script
