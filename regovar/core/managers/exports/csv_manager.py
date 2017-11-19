#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy

from core.managers.exports.abstract_export_manager import AbstractVariantExporter
from core.framework.common import *
import core.model as Model





            
class VepImporter(AbstractVariantExporter): 
    metadata = {
            "name" : "CSV", # name of the import manager
            "output" :  ["csv", "tsv"],  # list of file extension that manage the export manager
            "description" : "Export variants into a flat file with columns separeted by comma (CSV) or tab (TSV)" # short desciption about what it does
        }




    @staticmethod
    async def export_data(analysis_id, **kargs):
        """
            Retrieve selected variant of the given analysis and export them is the requested format
        """
        from core.core import core
        
        analysis = Model.analysis.from_id(analysis_id, 1)
        
        if not analysis:
            return {"success": False, "error": "Analysis not found"}
        
        
        
        file = Model.File.from_id(file_id)
        filepath = file.path
        reference_id = kargs["reference_id"]
        start_0 = datetime.datetime.now()
        job_in_progress = []

        
        vcf_metadata = prepare_vcf_parsing(reference_id, filepath)
        db_ref_suffix= "_" + Model.execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first().table_suffix

        # Maybe new annotations table have been created during the execution of prepare_vcf_parsing
        # So we force the server to refresh its annotations maping
        
        await core.annotations.load_annotation_metadata()

        if filepath.endswith(".vcf") or filepath.endswith(".vcf.gz"):
            filepath += ".regovar_import" # a tmp file have been created by prepare_vcf_parsing() method to avoid pysam unsupported file format.
            start = datetime.datetime.now()
            
            # Create vcf parser
            vcf_reader = VariantFile(filepath)

            # get samples in the VCF 
            # samples = {i : Model.get_or_create(Model.session(), Model.Sample, name=i)[0] for i in list((vcf_reader.header.samples))}
            samples = {}
            for i in list((vcf_reader.header.samples)):
                sample = Model.Sample.new()
                sample.name = i
                sample.file_id = file_id
                sample.reference_id = reference_id
                sample.filter_description = {filter[0]:filter[1].description for filter in vcf_reader.header.filters.items()}
                sample.default_dbuid = []
                for dbname in vcf_metadata["annotations"].keys():
                    if vcf_metadata["annotations"][dbname]:
                        sample.default_dbuid.append(vcf_metadata["annotations"][dbname].db_uid)
                # TODO : is_mosaic according to the data in the vcf
                sample.save()
                samples.update({i : sample})
            
            
            if len(samples.keys()) == 0 : 
                war("VCF files without sample cannot be imported in the database.")
                core.notify_all(None, data={'action':'import_vcf_error', 'data' : {'file_id' : file_id, 'msg' : "VCF files without sample cannot be imported in the database."}})
                return;

            core.notify_all(None, data={'action':'import_vcf_start', 'data' : {'file_id' : file_id, 'samples' : [ {'id' : samples[sid].id, 'name' : samples[sid].name} for sid in samples.keys()]}})
            # TODO : update sample's progress indicator


            records_count = vcf_metadata['count']
            log ("Importing file {0}\n\r\trecords  : {1}\n\r\tsamples  :  ({2}) {3}\n\r\tstart    : {4}".format(filepath, records_count, len(samples.keys()), reprlib.repr([sid for sid in samples.keys()]), start))
            run_async(VcfManager.import_delegate, file_id, vcf_reader, db_ref_suffix, vcf_metadata, samples)
        
            return {"success": True, "samples": samples, "records_count": records_count }
        return {"success": False, "error": "File not supported"}






