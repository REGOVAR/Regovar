#!env/python3
# coding: utf-8



import ipdb

import os
import datetime
import sqlalchemy
import subprocess
import multiprocessing as mp
import reprlib
import gzip
from pysam import VariantFile

from core.managers.imports.abstract_import_manager import AbstractImportManager
from core.framework import *
import core.model as Model
            
            
            
class PedManager(AbstractImportManager)
    def __init__(self):
        self.metadata = {
            "name" : "PED",
            "input" :  ["ped", "fam"],
            "description" : "Import sample's attributes from ped file"
        }



    async def import_data(file_id):

        file = Model.File.from_id(file_id)
        filepath = file.path
        reference_id = file.reference_id
        # parse ped file
            if os.path.exists(filepath):
                # extension = os.path.splitext(filepath)[1][1:]
                parser = ped_parser.FamilyParser(open(filepath), "ped")
            else:
                # no ped file -_-
                return False
            # retrieve analysis samples
            samples = {}
            for row in execute("SELECT a_s.sample_id, a_s.nickname, s.name FROM analysis_sample a_s INNER JOIN sample s ON a_s.sample_id=s.id WHERE analysis_id={0}".format(analysis_id)):
                samples[row.name] = row.sample_id
                if row.nickname is not '' and row.nickname is not None:
                    samples[row.nickname] = row.sample_id
            # drop all old "ped" attributes to avoid conflict
            ped_attributes = ['FamilyId', 'SampleId', 'FatherId', 'MotherId', 'Sex', 'Phenotype']
            execute("DELETE FROM attribute WHERE analysis_id={0} AND name IN ('{1}')".format(analysis_id, ''','''.join(ped_attributes)))
            # Insert new attribute's values according to the ped data
            sql = "INSERT INTO attribute (analysis_id, sample_id, name, value) VALUES "
            for sample in parser.individuals:
                if sample.individual_id in samples.keys():
                    sql += "({}, {}, '{}', '{}'),".format(analysis_id, samples[sample.individual_id], 'FamilyId', sample.family)
                    sql += "({}, {}, '{}', '{}'),".format(analysis_id, samples[sample.individual_id], 'FatherId', sample.father)
                    sql += "({}, {}, '{}', '{}'),".format(analysis_id, samples[sample.individual_id], 'MotherId', sample.mother)
                    sql += "({}, {}, '{}', '{}'),".format(analysis_id, samples[sample.individual_id], 'Sex', sample.sex)
                    sql += "({}, {}, '{}', '{}'),".format(analysis_id, samples[sample.individual_id], 'Phenotype', sample.phenotype)
            execute(sql[:-1])
