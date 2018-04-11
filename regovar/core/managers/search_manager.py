#!env/python3
# coding: utf-8
import ipdb

import os
import json
import datetime
import uuid
import psycopg2
import hashlib
import asyncio
import re
from sqlalchemy import or_, func



from config import *
from core.framework.common import *
from core.model import *







# =====================================================================================================================
# TOOLS
# =====================================================================================================================
def get_cached_pubmed(ids, headers={}):
    """
        Dedicated get_cached method for pubmed because api allow to retrieve several id in one query.
    """
    query = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&rettype=abstract&id={0}"
    result = {}
    to_request = []
    # Get data related to id from cache
    for pid in ids:
        res = get_cache("pubmed_" + pid)
        if res is None:
            to_request.append(pid)
        else:
            result[pid] = res
    # for ids which didn't had cached data: retrieved it from pubmed website
    if len(to_request) > 0:
        query_result = requests.get(query.format(",".join(to_request)), headers=headers)
        if query_result.ok:
            try:
                query_result = json.loads(query_result.content.decode())
                for key, data in query_result["result"].items():
                    if key == "uids": continue
                    set_cache("pubmed_" + key, data)
                    result[key] = data
            except Exception as ex:
                raise RegovarException("Unable to cache result of the query: " + query.format(",".join(to_request)), ex)

    res = []
    for pid in ids:
        if pid in result:
            res.append(result[pid])
        else:
            war("Pubmed get cached : Requested article ({0}) have not been retrieved".format(pid))
    return res





# =====================================================================================================================
# Search MANAGER
# =====================================================================================================================


class SearchManager:
    def __init__(self):
        pass






    def search(self, search_query):
        """ 
            Search provided query in following "objects" : 
                - variant :   ILIKE "chr:pos ref>alt" || "chr:pos_start-pos_end" || "chr:pos~delta " || "chr:pos"
                - project :   ILIKE "%name%"
                - analysis :  ILIKE "%name%"
                - sample :    ILIKE "%name%"
                - subject :   ILIKE "%firstname|lastname|identifiant%"
                - file :      ILIKE "%name%"
                - gene :      ILIKE "%name%"
                - phenotype : ILIKE "%name%" | "HP:id" 
                - disease :   ILIKE "%name%" | "OMIM:id" | "ORPHA:id"
                - user :      ILIKE "%login|firstname|lastname%"
                - pipeline :  ILIKE "%name%"
                - panel :     ILIKE "%name%"
            Return list of matching results
        """       
        variant_res = self.search_variant(search_query)
        project_res = self.search_project(search_query)
        analysis_res = self.search_analysis(search_query)
        sample_res = self.search_sample(search_query)
        subject_res = self.search_subject(search_query)
        file_res = self.search_file(search_query)
        gene_res = self.search_gene(search_query)
        phenotype_res = self.search_phenotype(search_query)
        disease_res = self.search_disease(search_query)
        user_res = self.search_user(search_query)
        pipeline_res = self.search_pipeline(search_query)
        panel_res = self.search_panel(search_query)
        
        result = { 
            "total_result": len(variant_res) + len(project_res) + len(analysis_res) + len(sample_res) + len(subject_res) + len(file_res) + len(gene_res) + len(phenotype_res) + len(disease_res) + len(user_res) + len(pipeline_res) + len(panel_res), 
            "variant":   variant_res,
            "project":   project_res,
            "analysis":  analysis_res,
            "sample":    sample_res,
            "subject":   subject_res,
            "file":      file_res,
            "gene":      gene_res,
            "phenotype": phenotype_res,
            "disease":   disease_res,
            "user":      user_res,
            "pipeline":  pipeline_res,
            "panel":     panel_res
        }
        return result


    

    def search_variant(self, search):
        """
            Return variant that match the search query
        """
        result = self.search_variant_pattern_1(search)
        if len(result) == 0:
            result = self.search_variant_pattern_2(search)
        if len(result) == 0:
            result = self.search_variant_pattern_3(search)
        if len(result) == 0:
            result = self.search_variant_pattern_4(search)
        return result

    def search_variant_pattern_1(self, search):
        from core.core import core
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+) ([a,c,g,t]*)>([a,c,g,t]*)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm = res[1]
            pos  = int(res[2])-1
            ref  = res[3].upper()
            alt  = res[4].upper()
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos={} AND ref='{}' AND alt='{}'"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos, ref, alt)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, pos+1, ref, alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result
    
    def search_variant_pattern_2(self, search):
        from core.core import core
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+)-([0-9]+)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm = res[1]
            pos1  = int(res[2])-1
            pos2  = int(res[3])-1
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos>={} AND pos<={}"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos1, pos2)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, row.pos+1, row.ref, row.alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result

    def search_variant_pattern_3(self, search):
        from core.core import core
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+)~([0-9]+)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm  = res[1]
            pos   = int(res[2])-1 
            delta = int(res[3])
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos>={} AND pos<={}"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos-delta, pos+delta)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, row.pos+1, row.ref, row.alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result

    def search_variant_pattern_4(self, search):
        from core.core import core
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm  = res[1]
            pos   = int(res[2])-1
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos={}"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, row.pos+1, row.ref, row.alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result



    def search_project(self, search):
        """
            Return projects that match the search query
        """
        result = Session().query(Project).filter(Project.name.ilike("%{0}%".format(search))).all()
        for p in result: p.init(0)
        return [p.to_json() for p in result]
    


    def search_analysis(self, search):
        """
            Return analyses that match the search query
        """
        result = Session().query(Analysis).filter(Analysis.name.ilike("%{0}%".format(search))).all()
        for res in result: res.init(1)
        fields = Analysis.public_fields + ["project"]
        return [r.to_json(fields) for r in result]
    


    def search_sample(self, search):
        """
            Return samples that match the search query
        """
        result = Session().query(Sample).filter(Sample.name.ilike("%{0}%".format(search))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_subject(self, search):
        """
            Return subjects that match the search query
        """
        result = Session().query(Subject).filter(or_(Subject.identifier.ilike("%{0}%".format(search)), Subject.firstname.ilike("%{0}%".format(search)), Subject.lastname.ilike("%{0}%".format(search)))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_file(self, search):
        """
            Return files that match the search query
        """
        result = Session().query(File).filter(File.name.ilike("%{0}%".format(search))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_gene(self, search):
        """
            Return gene that match the search query
        """
        # TODO: cache
        result = []
        query = "http://rest.genenames.org/search/{}".format(search)
        data = get_cached_url(query, "hgnc_", headers={"Accept": "application/json"})
        
        if data:
            i = 0
            for row in data["response"]["docs"]:
                result.append({"id": row["hgnc_id"], "symbol": row["symbol"]})
                i +=1
                if i == 100: break;
        return result
    


    def search_phenotype(self, search):
        """
            Return phenotype that match the search query
        """
        from core.core import core
        if search.startswith("HP:"):
            return core.phenotypes.get(search)
        else:
            return core.phenotypes.search(search.lower())
    
    

    def search_disease(self, search):
        """
            Return disease that match the search query
        """
        from core.core import core
        if search.startswith("OMIM:") or search.startswith("ORPHA:"):
            return core.phenotypes.get(search)
        # TODO: search disease by name (need to integrate OMIM/ORPHA public data (id<->title) into Regovar database)
        #else:
            #return core.phenotypes.search_disease(query.lower())
        return []
    
    
    
    def search_user(self, search):
        """
            Return user that match the search query
        """
        result = Session().query(User).filter(or_(User.login.ilike("%{0}%".format(search)), User.firstname.ilike("%{0}%".format(search)), User.lastname.ilike("%{0}%".format(search)))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]



    def search_pipeline(self, search):
        """
            Return pipeline that match the search query
        """
        result = Session().query(Pipeline).filter(Pipeline.name.ilike("%{0}%".format(search))).all()
        for p in result: p.init(0)
        return [p.to_json() for p in result]



    def search_panel(self, search):
        """
            Return panel that match the search query
        """
        result = Session().query(Panel).filter(or_(Panel.name.ilike("%{0}%".format(search)), Panel.description.ilike("%{0}%".format(search)), Panel.owner.ilike("%{0}%".format(search)))).all()
        for r in result: r.init()
        return [r.to_json() for r in result]



    def fetch_variant(self, reference_id, variant_id, analysis_id=None):
        """
            return all data available about a variant
        """
        db_suffix = execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first().table_suffix 
        from core.core import core
        ref_name = core.annotations.ref_list[int(reference_id)]
        # query = "SELECT _var.bin as vbin, _var.chr as vchr, _var.pos as vpos, _var.ref as vref, _var.alt as valt, dbnfsp_variant.* FROM (SELECT bin, chr, pos, ref, alt FROM variant_{} WHERE id={}) AS _var LEFT JOIN dbnfsp_variant ON _var.bin=dbnfsp_variant.bin_hg19 AND _var.chr=dbnfsp_variant.chr_hg19 AND _var.pos=dbnfsp_variant.pos_hg19 AND _var.ref=dbnfsp_variant.ref AND _var.alt=dbnfsp_variant.alt"
        query = "SELECT _var.bin as vbin, _var.chr as vchr, _var.pos as vpos, _var.ref as vref, _var.alt as valt, rg.name2 as genename, _var.sample_list, _var.regovar_score, _var.regovar_score_meta FROM (SELECT bin, chr, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{0} WHERE id={1}) AS _var LEFT JOIN refgene_{0} rg ON rg.chr=_var.chr AND rg.trxrange @> _var.pos"
        variant = execute(query.format(db_suffix, variant_id)).first()
        if variant:
            chrm = CHR_DB_MAP[variant.vchr]
            pos = variant.vpos + 1  # return result as 1-based coord
            ref = variant.vref
            alt = variant.valt
            gene = variant.genename
            result = {
                "id": variant_id,
                "reference_id": reference_id,
                "reference": ref_name,
                "chr": chrm,
                "pos": pos,
                "ref": ref,
                "alt": alt,
                "genename" : gene if gene else "",
                "annotations": {},
                "online_tools_variant": [
                    {"name" : "Marrvel", "url"  : "http://marrvel.org/search/variant/{0}:{1}%20{2}%3E{3}".format(variant.vchr, pos, ref, "")},
                    {"name" : "Varsome", "url"  : "https://varsome.com/variant/{0}/chr{1}-{2}-{3}".format(ref_name, chrm, pos, ref)}
                ],
                "stats": {
                    "sample_list" : variant.sample_list,
                    "regovar_score": variant.regovar_score,
                    "regovar_score_meta" : variant.regovar_score_meta
                },
                "online_tools_gene": [],
                "diseases": [],
                "phenotypes": []}
            # TODO: retrieve variant stats
            if gene:
                result.update({"online_tools_gene": [
                    {"name" : "Cosmic",      "url"  : "http://cancer.sanger.ac.uk/cosmic/gene/overview?ln={0}".format(gene)},
                    {"name" : "Decipher",    "url"  : "https://decipher.sanger.ac.uk/search?q={0}".format(gene)},
                    {"name" : "Genatlas",    "url"  : "http://genatlas.medecine.univ-paris5.fr/fiche.php?symbol={0}".format(gene)},
                    {"name" : "Genecards",   "url"  : "http://www.genecards.org/cgi-bin/carddisp.pl?gene={0}".format(gene)},
                    {"name" : "Genetest",    "url"  : "https://www.genetests.org/genes/?gene={0}".format(gene)},
                    {"name" : "Gopubmed",    "url"  : "http://www.gopubmed.org/search?t=hgnc&q={0}".format(gene)},
                    {"name" : "H_invdb",     "url"  : "http://biodb.jp/hfs.cgi?db1=HUGO&type=GENE_SYMBOL&db2=Locusview&id={0}".format(gene)},
                    {"name" : "Hgnc",        "url"  : "http://www.genenames.org/cgi-bin/gene_symbol_report?match={0}".format(gene)},
                    {"name" : "Kegg_patway", "url"  : "http://www.kegg.jp/kegg-bin/search_pathway_text?map=map&keyword={0}&mode=1&viewImage=true".format(gene)},
                    {"name" : "Nih_ghr",     "url"  : "https://ghr.nlm.nih.gov/gene/{0}".format(gene)}
                    ]})
                # Get phenotype associated to the gene
                hpo_data = core.phenotypes.get(gene)
                if hpo_data: result.update(hpo_data)

                gene_data = self.fetch_gene(gene)
                if gene_data: result.update({"gene":gene_data})
                
            if analysis_id is not None:
                result.update({"analysis": {"id": analysis_id}})
            return result 
        return None


    def fetch_gene(self, genename, ref_id=None):
        # Get gene common information
        from core.core import core
        query = "http://rest.genenames.org/fetch/symbol/{}".format(genename)
        data = get_cached_url(query, "hgnc_", headers={"Accept": "application/json"})
        if data and 'response' in data and 'docs' in data['response'] and len(data['response']['docs']) > 0:
            pubmed= None
            phenotype = None
            data = data['response']['docs'][0]

            # Get omim data
            omim = data["omim_id"][0] if "omim_id" in data and len(data["omim_id"]) > 0 else None
            if omim:
                omim = get_cached_url("https://api.omim.org/api/entry?mimNumber={}&include=all".format(omim), "omim_",  headers={"Accept": "application/json", "apiKey": OMIM_API_KEY})
                omim = omim["omim"]["entryList"][0]["entry"]
                # Get allelic variant
                variants = []
                if "allelicVariantList" in omim and len(omim["allelicVariantList"]) > 0:
                    variants = [r["allelicVariant"] for r in omim["allelicVariantList"]]
                    data.update({"omim_variants": variants})
                # Get phenotype
                if "geneMap" in omim and "phenotypeMapList" in omim["geneMap"] and len(omim["geneMap"]["phenotypeMapList"]) > 0:
                    phenotype = []
                    phenotype = [t["reference"] for t in omim["referenceList"]]
                    data["phenotype"] = phenotype

                
            # Get pubmed data
            pubmed = []
            # TODO : do it with all default pubmed term set for the current profile
            query = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=100&term=(%22{0}%22%5BAll%20Terms%5D)"
            pdata = get_cached_url(query.format(genename), "pubmed_")
            if int(pdata["esearchresult"]["count"]) > 0:
                pids = [id for id in pdata["esearchresult"]["idlist"]]
                cache_result = get_cached_pubmed(pids)
                for pdata in cache_result:
                    pubmed.append({
                        "authors": [auth["name"] for auth in pdata["authors"]],
                        "title": pdata["title"],
                        "source": pdata["source"] + ", " + pdata["pubdate"],
                        "fulljournalname" : pdata["fulljournalname"],
                        "id": pdata["uid"],
                        "articleUrl":"https://academic.oup.com/hmg/article-lookup/doi/10.1093/hmg/ddl084",
                    })
            data["pubmed"] = pubmed
            
            # get refgene data
            query = "SELECT chr, trxrange, cdsrange, exoncount, trxcount FROM refgene_{} WHERE name2 ilike '{}'"
            refgene = []
            if ref_id:
                res = execute(query.format(core.annotations.ref_list[ref_id].lower(), genename)).first()
                refgene.append({
                    "id": ref_id, 
                    "name": core.annotations.ref_list[ref_id], 
                    "start": res.trxrange.lower,
                    "size": res.trxrange.upper - res.trxrange.lower,
                    "exon": res.exoncount,
                    "trx": res.trxcount})
            else:
                for ref_id in core.annotations.ref_list.keys():
                    if ref_id > 0:
                        suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                        res = execute(query.format(suffix, genename)).first()
                        if res:
                            refgene.append({
                                "id": ref_id, 
                                "name": core.annotations.ref_list[ref_id], 
                                "start": res.trxrange.lower,
                                "size": res.trxrange.upper - res.trxrange.lower,
                                "exon": res.exoncount,
                                "trx": res.trxcount})
            data.update({"refgene": refgene})

            # Get hpo data
            hpo = {"diseases": [], "phenotypes": []}
            query = "SELECT distinct hpo_id, label FROM hpo_disease WHERE genes @> '{{{}}}' ORDER BY hpo_id".format(genename)
            for row in execute(query):
                hpo["diseases"].append({"id": row.hpo_id, "label": row.label})
            query = "SELECT distinct hpo_id, label FROM hpo_phenotype WHERE genes @> '{{{}}}' ORDER BY label".format(genename)
            for row in execute(query):
                hpo["phenotypes"].append({"id": row.hpo_id, "label": row.label})

            data.update({"hpo": hpo})
        return data






