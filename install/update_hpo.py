#!/usr/bin/python
import sys
import core.model as Model
import json
from core.framework.common import remove_duplicates
import copy


# Prerequisites: Download HPO dumps (Done in makefile that call this script)
hpopath = sys.argv[1]
version = sys.argv[2]
#hpopath = "/var/regovar/databases/"
#version = "2018-03-09 09:06"

print (version)

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

# TOOLS
def escape(value):
    if type(value) is str:
        value = value.replace('%', '%%')
        value = value.replace("'", "''")
    return value


def append_qual(did, qual):
    if did not in p_data[pid]["meta"]["qualifiers"]:
            p_data[pid]["meta"]["qualifiers"][did] = [qual]
    elif qual not in p_data[pid]["meta"]["qualifiers"][did]:
        p_data[pid]["meta"]["qualifiers"][did].append(qual)






# STEP 1: Load HPO terms data from file
print('Step 1: parsing hpo.obo file. ', end='', flush=True)
data_pattern = {
    "id": -1, 
    "label":None, 
    "definition": None, 
    "synonym":[], 
    "parents": [], 
    "subs": [], 
    "diseases": [], 
    "genes": [], 
    "sub_total": -1,
    "subontology": "phenotypic",
    "meta": {"qualifiers": {}, "sources": []}
}

with open(obopath, "r") as f:
    current_id = None
    lines = f.readlines()
    for l in lines:
        if l.startswith("id: "):
            current_id = l[4:-1]
            if current_id not in p_data:
                p_data[current_id] = copy.deepcopy(data_pattern)
                p_data[current_id]["id"] = current_id
        elif l.startswith("name: "):
            p_data[current_id]["label"] = l[6:-1]
        elif l.startswith("def: "):
            p_data[current_id]["definition"] = l[6:l.rfind('"')]
        elif l.startswith("is_a: "):
            pid = l[6:16]
            if pid not in p_data:
                p_data[pid] = copy.deepcopy(data_pattern)
                p_data[pid]["id"] = pid
            p_data[pid]["subs"].append(current_id)
            p_data[current_id]["parents"].append(pid)
        elif l.startswith("synonym: "):
            p_data[current_id]["synonym"].append(l[10:l.rfind('"')])
print('Done')



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
        onset_id = ldata[7].strip()
        freq_id = ldata[8].strip()
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


        if qualifier != "" and qualifier != "NOT": append_qual(did, qualifier)
        if onset_id != "": append_qual(did, onset_id)
        if freq_id != "": append_qual(did, freq_id)
            
        if source_id != did and source_id != "":
            source_id = source_id.split(";")
            for s in source_id:
                p_data[pid]["meta"]["sources"] += s.split(",")
                d_data[did]["sources"] += s.split(",")
print('Done')






# STEP 3: diseases, genes and phenotypes associations
print('Step 3: parsing diseases/genes associations files.', end='', flush=True)
all_genes = []
with open(diseapath, "r") as f:
    lines = f.readlines()
    for l in lines:
        if l.startswith("#"): continue
        ldata = l.split("\t")
        pid = ldata[3].strip()
        did = ldata[0].strip()
        gene = ldata[1].strip()
        if gene not in all_genes: 
            all_genes.append(gene)
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
        gene = ldata[3].strip()
        if gene not in all_genes: 
            all_genes.append(gene)
        if pid in p_data:
            p_data[pid]["genes"].append(gene)


for pid in p_data:
    p_data[pid]["diseases"] = remove_duplicates(p_data[pid]["diseases"])
    p_data[pid]["genes"] = remove_duplicates(p_data[pid]["genes"])
    p_data[pid]["meta"]["sources"] = remove_duplicates(p_data[pid]["meta"]["sources"])
    p_data[pid]["diseases"].sort()
    p_data[pid]["genes"].sort()
    p_data[pid]["meta"]["sources"].sort()
for did in d_data:
    d_data[did]["phenotypes"] = remove_duplicates(d_data[did]["phenotypes"])
    d_data[did]["phenotypes_neg"] = remove_duplicates(d_data[did]["phenotypes_neg"])
    d_data[did]["genes"] = remove_duplicates(d_data[did]["genes"])
    d_data[did]["sources"] = remove_duplicates(d_data[did]["sources"])
    d_data[did]["phenotypes"].sort()
    d_data[did]["phenotypes_neg"].sort()
    d_data[did]["genes"].sort()
    d_data[did]["sources"].sort()
print('Done')




# STEP 4: Compute for each term the list of all its sublevels childs/diseases/genes
print('step 4: computing subontologies. ', end='', flush=True)


subontologies = {
    "HP:0000005": "inheritance",
    "HP:0000118": "phenotypic",
    "HP:0012823": "clinical",
    "HP:0031797": "clinical",
    "HP:0040279": "frequency"
}

def get_sublevel_data(hpo_id, subontology):
    result = { "sub_total": 0, "sub_genes": [], "sub_diseases": [], "genes_score":0, "diseases_score":0}
    if hpo_id not in p_data: 
        print ("Link to an unknown id: " + hpo_id)
        return None
        
    # Escape if already done
    if p_data[hpo_id]["sub_total"] != -1 :
        return p_data[hpo_id]

    # Compute parent subontology
    if hpo_id in subontologies: subontology = subontologies[hpo_id]
    p_data[hpo_id]["subontology"] = subontology

    # Compute data for current entry
    result["sub_total"] = len(p_data[hpo_id]["subs"])
    result["sub_genes"] = p_data[hpo_id]["genes"]
    result["sub_diseases"] = p_data[hpo_id]["diseases"]

    # Adding data from childs
    for cid in p_data[hpo_id]["subs"]:
        cres = get_sublevel_data(cid, subontology)
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

# recursive call for each subonthologies
for pid in p_data["HP:0000001"]["subs"]:
    get_sublevel_data(pid, "")
# call again on all phenotypes for which one that have not been 
for pid in p_data:
    get_sublevel_data(pid, "phenotypic")

p_data["HP:0000001"].update({ "sub_total": 0, "sub_genes": [], "sub_diseases": [], "genes_score":0, "diseases_score":0})

print('Done')


# STEP 5: Process sql query
print('step 5: Populating database. ', end='', flush=True)
genes_total = len(all_genes)
diseases_total = len(d_data)
pattern = "('{}', '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, '{}', '{}'), "
sql = "INSERT INTO hpo_phenotype (hpo_id, label, definition, parents, childs, search, genes, diseases, genes_score, diseases_score, allsubs_genes, allsubs_diseases, subontology, meta) VALUES "
for pid in p_data:
    label = escape(p_data[pid]["label"])
    definition = escape(p_data[pid]["definition"])
    parents = "NULL"
    if len(p_data[pid]["parents"]) > 0:
        parents = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["parents"]]))
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
    genes_score = len(p_data[pid]["genes"]) / genes_total
    diseases_score = len(p_data[pid]["genes"]) / genes_total
    as_g = "NULL"
    if len(p_data[pid]["sub_genes"]) > 0:
        as_g = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["sub_genes"]]))
    as_d = "NULL"
    if len(p_data[pid]["sub_diseases"]) > 0:
        as_d = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in p_data[pid]["sub_diseases"]]))
    subontology = p_data[pid]["subontology"]
    meta = p_data[pid]["meta"]
    meta.update({"all_childs_count": p_data[pid]["sub_total"]})
    meta = escape(json.dumps(meta))
    sql += pattern.format(pid, label, definition, parents, childs, search, genes, diseases, genes_score, diseases_score, as_g, as_d, subontology, meta)
sql = sql[:-2]
Model.execute(sql)


pattern = "('{}', '{}', '{}', {}, {}, {}, '{}'), "
sql = "INSERT INTO hpo_disease (hpo_id, label, search, genes, phenotypes, phenotypes_neg, sources) VALUES "
for did in d_data:
    label = escape(d_data[did]["label"])
    search = label + " " + escape(d_data[did]["search"])
    genes = "NULL"
    if len(d_data[did]["genes"]) > 0:
        genes = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in d_data[did]["genes"]]))
    phenotypes = "NULL"
    if len(d_data[did]["phenotypes"]) > 0:
        phenotypes = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in d_data[did]["phenotypes"]]))
    phenotypes_neg = "NULL"
    if len(d_data[did]["phenotypes_neg"]) > 0:
        phenotypes_neg = "ARRAY[{}]".format(",".join(["'{}'".format(l) for l in d_data[did]["phenotypes_neg"]]))
    sources = escape(json.dumps(d_data[did]["sources"]))
    sql += pattern.format(did, label, search, genes, phenotypes, phenotypes_neg, sources)
sql = sql[:-2]
Model.execute(sql)
print('Done')


Model.execute("DELETE FROM parameter WHERE key='hpo_version'")
Model.execute("INSERT INTO parameter (key, value, description) VALUES ('hpo_version', '{}', 'Version of the HPO database dumps used');".format(escape(version)))
# Load HPO terms-gene-diseases relations
# Done in update_hpo.sql script call in the makefile that called this script
