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
import ped_parser



from config import *
from core.framework.common import *
from core.model import *



# =====================================================================================================================
# Variants MANAGER
# =====================================================================================================================


class VariantManager:
    def __init__(self):
        pass


    def get(self, reference_id, variant_id, analysis_id=None):
        """
            return all data available about a variant
        """

        db_suffix = execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first().table_suffix 
        from core.core import core
        ref_name = core.annotations.ref_list[int(reference_id)]
        # query = "SELECT _var.bin as vbin, _var.chr as vchr, _var.pos as vpos, _var.ref as vref, _var.alt as valt, dbnfsp_variant.* FROM (SELECT bin, chr, pos, ref, alt FROM variant_{} WHERE id={}) AS _var LEFT JOIN dbnfsp_variant ON _var.bin=dbnfsp_variant.bin_hg19 AND _var.chr=dbnfsp_variant.chr_hg19 AND _var.pos=dbnfsp_variant.pos_hg19 AND _var.ref=dbnfsp_variant.ref AND _var.alt=dbnfsp_variant.alt"
        query = "SELECT _var.bin as vbin, _var.chr as vchr, _var.pos as vpos, _var.ref as vref, _var.alt as valt, rg.name2 as genename FROM (SELECT bin, chr, pos, ref, alt FROM variant_{0} WHERE id={1}) AS _var LEFT JOIN refgene_{0} rg ON rg.bin=_var.bin AND rg.chr=_var.chr AND rg.txrange @> _var.pos"
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
                    {"name" : "Varsome", "url"  : "https://varsome.com/variant/{0}/chr{1}-{2}-{3}".format(ref_name, chrm, pos, ref)},
                    {"name" : "Marrvel", "url"  : "http://marrvel.org/search/variant/{0}:{1}%20{2}%3E{3}".format(variant.vchr, pos, ref, "")}
                ],
                "stats": {},
                "online_tools_gene": []}
            if gene:
                result.update({"online_tools_gene": [
                    {"name" : "Genetest",    "url"  : "https://www.genetests.org/genes/?gene={0}".format(gene)},
                    {"name" : "Decipher",    "url"  : "https://decipher.sanger.ac.uk/search?q={0}".format(gene)},
                    {"name" : "Cosmic",      "url"  : "http://cancer.sanger.ac.uk/cosmic/gene/overview?ln={0}".format(gene)},
                    {"name" : "Nih_ghr",     "url"  : "https://ghr.nlm.nih.gov/gene/{0}".format(gene)},
                    {"name" : "Hgnc",        "url"  : "http://www.genenames.org/cgi-bin/gene_symbol_report?match={0}".format(gene)},
                    {"name" : "Genatlas",    "url"  : "http://genatlas.medecine.univ-paris5.fr/fiche.php?symbol={0}".format(gene)},
                    {"name" : "Genecards",   "url"  : "http://www.genecards.org/cgi-bin/carddisp.pl?gene={0}".format(gene)},
                    {"name" : "Gopubmed",    "url"  : "http://www.gopubmed.org/search?t=hgnc&q={0}".format(gene)},
                    {"name" : "H_invdb",     "url"  : "http://biodb.jp/hfs.cgi?db1=HUGO&type=GENE_SYMBOL&db2=Locusview&id={0}".format(gene)},
                    {"name" : "Kegg_patway", "url"  : "http://www.kegg.jp/kegg-bin/search_pathway_text?map=map&keyword={0}&mode=1&viewImage=true".format(gene)}]})
            if analysis_id is not None:
                result.update({"analysis": {"id": analysis_id}})
            return result 
        return None
