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
        from core.core import core
        ref_name = core.annotations.ref_list[int(reference_id)]
        # query = "SELECT _var.bin as vbin, _var.chr as vchr, _var.pos as vpos, _var.ref as vref, _var.alt as valt, dbnfsp_variant.* FROM (SELECT bin, chr, pos, ref, alt FROM variant_{} WHERE id={}) AS _var LEFT JOIN dbnfsp_variant ON _var.bin=dbnfsp_variant.bin_hg19 AND _var.chr=dbnfsp_variant.chr_hg19 AND _var.pos=dbnfsp_variant.pos_hg19 AND _var.ref=dbnfsp_variant.ref AND _var.alt=dbnfsp_variant.alt"
        query = "SELECT _var.bin as vbin, _var.chr as vchr, _var.pos as vpos, _var.ref as vref, _var.alt as valt FROM (SELECT bin, chr, pos, ref, alt FROM variant_{} WHERE id={}) AS _var"
        variant = execute(query.format('hg19', variant_id)).first()
        chrm = CHR_DB_MAP[variant.vchr]
        pos = variant.vpos + 1  # return result as 1-based coord
        ref = variant.vref
        alt = variant.valt
        gene = None  # variant.genename
        result = {
            "id": variant_id,
            "reference_id": reference_id,
            "reference": ref_name,
            "chr": chrm,
            "pos": pos,
            "ref": ref,
            "alt": alt,
            "annotations": {},
            "online_tools_variant": {
                "varsome": "https://varsome.com/variant/{0}/chr{1}-{2}-{3}".format(ref_name, chrm, pos, ref)},
            "stats": {}}
        if gene:
            result.update({"online_tools_gene": {
                "genetest": "https://www.genetests.org/genes/?gene={0}".format(gene),
                "decipher": "https://decipher.sanger.ac.uk/search?q={0}".format(gene),
                "cosmic": "http://cancer.sanger.ac.uk/cosmic/gene/overview?ln={0}".format(gene),
                "nih_ghr": "https://ghr.nlm.nih.gov/gene/{0}".format(gene),
                "hgnc": "http://www.genenames.org/cgi-bin/gene_symbol_report?match={0}".format(gene),
                "genatlas": "http://genatlas.medecine.univ-paris5.fr/fiche.php?symbol={0}".format(gene),
                "genecards": "http://www.genecards.org/cgi-bin/carddisp.pl?gene={0}".format(gene),
                "gopubmed": "http://www.gopubmed.org/search?t=hgnc&q={0}".format(gene),
                "h_invdb": "http://biodb.jp/hfs.cgi?db1=HUGO&type=GENE_SYMBOL&db2=Locusview&id={0}".format(gene),
                "kegg_patway": "http://www.kegg.jp/kegg-bin/search_pathway_text?map=map&keyword={0}&mode=1&viewImage=true".format(gene)}})
        if analysis_id is not None:
            result.update({"analysis": {"id": analysis_id}})
        return result 
