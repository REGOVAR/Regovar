#!/usr/bin/python
import sys
import core.model as Model
import json
from core.framework.common import remove_duplicates


# Prerequisites: Download HPO dumps (Done in makefile that call this script)
hpopath = sys.argv[1]
version = sys.argv[2]
#hpopath = "/var/regovar/databases/"
#version = "2018-03-09 09:06"

# create path to hpo files to import
obopath = hpopath + "hpo.obo"
annotpath = hpopath + "hpo_annotation.txt"
nannotpath = hpopath + "hpo_annotation_neg.txt"
diseapath = hpopath + "hpo_disease.txt"
phenopath = hpopath + "hpo_phenotype.txt"


# Clear HPO tables
print('Clear database: ', end='', flush=True)
Model.execute("DELETE FROM hpo_phenotype")
Model.execute("DELETE FROM hpo_disease")
print('Done')



# temp dict that store direct child relation between a term and all its childs
p_data = {}  # phenotype oriented data
d_data = {}  # disease oriented data


def escape(value):
    if type(value) is str:
        value = value.replace('%', '%%')
        value = value.replace("'", "''")
    return value




# STEP 1: Load HPO terms data from file
print('Step 1: parsing hpo.obo file. ', end='', flush=True)
meta_pattern = {"qualifiers": {}, "sources": []}
with open(obopath, "r") as f:
    current_id = None
    lines = f.readlines()
    for l in lines:
        if l.startswith("id: "):
            current_id = l[4:-1]
            p_data[current_id] = {"id": current_id, "label":None, "definition": None, "synonym":[], "parent": None, "subs": [], "diseases": [], "genes": [], "sub_total": -1}
        elif l.startswith("name: "):
            p_data[current_id]["label"] = l[6:-1]
        elif l.startswith("def: "):
            p_data[current_id]["definition"] = l[6:l.rfind('"')]
        elif l.startswith("is_a: "):
            pid = l[6:16]
            if pid in p_data:
                p_data[pid]["subs"].append(current_id)
            else:
                p_data[pid] = {"id": pid, "label":None, "definition": None, "synonym":[], "parent": None, "subs": [current_id], "diseases": [], "genes": [], "sub_total": -1}
            p_data[current_id]["parent"] = pid
        elif l.startswith("synonym: "):
            p_data[current_id]["synonym"].append(l[10:l.rfind('"')])
print('Done')


# finds roots sections
meta_pattern = {"sections": {f:[] for f in p_data["HP:0000001"]["subs"]}}


# STEP 2: Load diseases entries
print('Step 2: parsing diseases annotations files. ', end='', flush=True)
with open(annotpath, "r") as f:
    lines = f.readlines()
    for l in lines:
        if l.startswith("#"): continue
        ldata = l.split("\t")
        db = ldata[0].strip()
        db_id = ldata[1].strip()
        label = ldata[2].strip()
        qualifier = ldata[3].strip()
        pid = ldata[4].strip()
        source_id = ldata[5].strip()
        #onset_id = ldata[7].strip()  # Not used
        #freq_id = ldata[8].strip()  # Not used
        #aspect = ldata[10].strip()  # Not used
        synonyms = ldata[11].strip()
        
        
        if pid not in p_data:
            print("WARNING: unknow pid... skipped: " + pid)
            continue
        
        did = "{}:{}".format(db, db_id)
        p_data[pid]["diseases"].append(did)
        
        if did not in d_data:
            d_data[did] = {"label": label, "search": synonyms, "phenotypes":[], "phenotypes_neg": [], "genes": [], "sources": []}
            
        if qualifier == "NOT":
            d_data[did]["phenotypes_neg"].append(pid)
        else:
            d_data[did]["phenotypes"].append(pid)
        if qualifier != "":
            p_data[pid]["meta"]["qualifiers"][did] = qualifier
            
        if source_id != did:
            p_data[pid]["meta"]["sources"].append(source_id)
            d_data[did]["sources"].append(source_id)
print('Done')






# STEP 3: diseases, genes and phenotypes associations
print('Step 3: ', end='', flush=True)
with open(diseapath, "r") as f:
    lines = f.readlines()
    for l in lines:
        if l.startswith("#"): continue
        ldata = l.split("\t")
        pid = ldata[3].strip()
        did = ldata[0].strip()
        gene = ldata[1].strip()
        if pid in p_data:
            p_data[pid]["diseases"].append(did)
            p_data[pid]["genes"].append(gene)
        if did in d_data:
            d_data[did]["phenotypes"].append(pid)
            d_data[did]["genes"].append(gene)
        else:
            d_data[did] = {"phenotypes":[pid], "genes": [gene]}

with open(phenopath, "r") as f:
    lines = f.readlines()
    for l in lines:
        if l.startswith("#"): continue
        ldata = l.split("\t")
        pid = ldata[0].strip()
        if pid in p_data:
            p_data[pid]["genes"].append(ldata[3].strip())


for pid in p_data:
    p_data[pid]["diseases"] = remove_duplicates(p_data[pid]["diseases"])
    p_data[pid]["genes"] = remove_duplicates(p_data[pid]["genes"])
    p_data[pid]["diseases"].sort()
    p_data[pid]["genes"].sort()
for did in d_data:
    d_data[did]["phenotypes"] = remove_duplicates(d_data[did]["phenotypes"])
    d_data[did]["genes"] = remove_duplicates(d_data[did]["genes"])
    d_data[did]["phenotypes"].sort()
    d_data[did]["genes"].sort()
print('Done')




# STEP 4: Compute for each term the list of all its sublevels childs/diseases/genes
print('step 4: ', end='', flush=True)




def get_sublevel_data(hpo_id, root_id, root_path):
    result = { "sub_total": 0, "sub_genes": [], "sub_diseases": [], "meta": meta_pattern, "genes_score":0, "diseases_score":0}
    if hpo_id not in p_data: 
        print ("Link to an unknown id: " + hpo_id)
        return None

    # Compute parent path
    if hpo_id != "HP:0000001":
        meta = p_data[hpo_id]["meta"] if "meta" in p_data[hpo_id] else meta_pattern
        if root_id in meta["sections"] and hpo_id not in meta["sections"][root_id] and root_id != hpo_id:
            root_path.append(hpo_id)
            meta["sections"][root_id] = root_path
        p_data[hpo_id]["meta"] = meta
        
    # Escape if already done
    if p_data[hpo_id]["sub_total"] != -1 :
        return p_data[hpo_id]

    # Compute data for current entry
    result["sub_total"] = len(p_data[hpo_id]["subs"])
    result["sub_genes"] = p_data[hpo_id]["genes"]
    result["sub_diseases"] = p_data[hpo_id]["diseases"]

    # Adding data from childs
    for cid in p_data[hpo_id]["subs"]:
        cres = get_sublevel_data(cid, root_id, root_path)
        if cres:
            result["sub_total"] += cres["sub_total"]
            result["sub_genes"] += cres["sub_genes"]
            result["sub_diseases"] += cres["sub_diseases"]

    # clean data
    result["sub_genes"] = remove_duplicates(result["sub_genes"])
    result["sub_diseases"] = remove_duplicates(result["sub_diseases"])
    result["sub_genes"].sort()
    result["sub_diseases"].sort()
    p_data[hpo_id].update(result)
    return result

# recursive call for each section
for f in p_data["HP:0000001"]["subs"]:
    get_sublevel_data(pid, pid, [])

for pid in p_data:
    get_sublevel_data(pid, pid, [])
print('Done')


# "Disable" terchnical's root hpo entry to avoid to retrieve it when searching phenotype via disease or gene
p_data["HP:0000001"]["sub_genes"] = []
p_data["HP:0000001"]["sub_diseases"] = []
p_data["HP:0000001"]["meta"] = {}

# STEP 4: Process sql query
print('step 4: ', end='', flush=True)
pattern = "('{}', '{}', '{}', {}, {}, {}, {}, {}, {}, {}, '{}'), "
sql = "INSERT INTO hpo_phenotype (hpo_id, label, definition, parent, childs, search, genes, diseases, allsubs_genes, allsubs_diseases, meta) VALUES "
for pid in p_data:
    label = escape(p_data[pid]["label"])
    definition = escape(p_data[pid]["definition"])
    parent = "'{}'".format(p_data[pid]["parent"]) if p_data[pid]["parent"] is not None else "NULL"
    childs = "NULL"
    if len(p_data[pid]["subs"]) > 0:
        childs = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["subs"]]))
    search = "NULL"
    if len(p_data[pid]["synonym"]) > 0:
        search = "'{}'".format(escape(' '.join(p_data[pid]["synonym"])))
    genes = "NULL"
    if len(p_data[pid]["genes"]) > 0:
        genes = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["genes"]]))
    diseases = "NULL"
    if len(p_data[pid]["diseases"]) > 0:
        diseases = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["diseases"]]))
    as_g = "NULL"
    if len(p_data[pid]["sub_genes"]) > 0:
        as_g = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["sub_genes"]]))
    as_d = "NULL"
    if len(p_data[pid]["sub_diseases"]) > 0:
        as_d = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["sub_diseases"]]))
    meta = p_data[pid]["meta"]
    meta.update({"all_childs_count": p_data[pid]["sub_total"]})
    meta = escape(json.dumps(meta))
    sql += pattern.format(pid, label, definition, parent, childs, search, genes, diseases, as_g, as_d, meta)
sql = sql[:-2]
Model.execute(sql)


pattern = "('{}', '{}', '{}', {}, {}, {}), "
sql = "INSERT INTO hpo_disease (hpo_id, label, definition, search, genes, phenotypes) VALUES "
for did in d_data:
    label = "" # escape(d_data[did]["label"])
    definition = "" # escape(d_data[did]["definition"])
    search = "NULL" # label " " + definition
    genes = "NULL"
    if len(d_data[did]["genes"]) > 0:
        genes = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in d_data[did]["genes"]]))
    phenotypes = "NULL"
    if len(d_data[did]["phenotypes"]) > 0:
        phenotypes = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in d_data[did]["phenotypes"]]))
    sql += pattern.format(did, label, definition, search, genes, phenotypes)
sql = sql[:-2]
Model.execute(sql)
print('Done')


# Load HPO terms-gene-diseases relations
# Done in update_hpo.sql script call in the makefile that called this script
