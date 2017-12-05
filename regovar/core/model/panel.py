#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# PANEL
# /!\ As SQLAlchemy is not able to automaticaly create class for table with int8range field, we manage it ourself
# =====================================================================================================================

"id", "version", "name", "description", "owner", "create_date", "update_date", "entries"


def panel_init(self, loading_depth=0):
    """
        Init properties of a panel :
            - id          : int           : The id of the panel in the database
            - versions    : [json]        : The ordered list of version: from current (idx=0) to formest (idx=count)
            - name        : str           : The name
            - description : str           : An optional description
            - owner       : str           : The owner
            - update_date : date          : The last time that the object have been updated
            - create_date : date          : The datetime when the object have been created
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - versions
              - entries   : [json]        : The list of entries by version of the panel
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth") and self.loading_depth >= loading_depth:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.versions = self.versions = self.get_versions(self.loading_depth-1)
    except Exception as ex:
        raise RegovarException("Panel data corrupted (id={}).".format(self.id), "", ex)



def panel_from_id(panel_id, loading_depth=0):
    """
        Retrieve panel with the provided id in the database
    """
    panel = session().query(Panel).filter_by(id=panel_id).first()
    if panel:
        panel.init(loading_depth)
    return panel


def panel_from_ids(panel_ids, loading_depth=0):
    """
        Retrieve panels corresponding to the list of provided id
    """
    panels = []
    if panel_ids and len(panel_ids) > 0:
        panels = session().query(Panel).filter(Panel.id.in_(panel_ids)).all()
        for f in panels:
            f.init(loading_depth)
    return panels


def panel_to_json(self, fields=None, loading_depth=-1):
    """
        Export the panel into json format with only requested fields
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = Panel.public_fields
    for f in fields:
        if f in Panel.public_fields:
            if f in ["create_date", "update_date"]:
                result[f] = eval("self." + f + ".isoformat()")
            elif hasattr(self, f):
                result[f] = eval("self." + f)
    return result


def panel_load(self, data):
    try:
        # Required fields
        if "name" in data.keys(): self.name = data['name']
        if "description" in data.keys(): self.description = data['description']
        if "owner" in data.keys(): self.owner = data['owner']
        if "update_date" in data.keys(): self.update_date = data['update_date']
        self.save()
        
        # update versions
        if "versions" in data.keys():
            # It's not allowed to delete or edit formest version. Only possible to add new one
            # TODO
            ipdb.set_trace()
            pass

        # check to reload dynamics properties
        self.init(self.loading_depth)
    except Exception as ex:
        raise RegovarException('Panel error', ex)
    return self


def panel_save(self):
    generic_save(self)


def panel_delete(panel_id):
    """
        Delete the panel with the provided id in the database
    """
    session().query(Panel).filter_by(id=panel_id).delete(synchronize_session=False)
    # TODO: delete entries


def panel_new():
    """
        Create a new panel and init/synchronise it with the database
    """
    s = Panel()
    s.save()
    s.init()
    return s


def panel_count():
    """
        Return total of Panel entries in database
    """
    return generic_count(Panel)





Panel = Base.classes.panel
Panel.public_fields = ["id", "versions", "name", "description", "owner", "create_date", "update_date"]


Panel.init = panel_init
Panel.from_id = panel_from_id
Panel.from_ids = panel_from_ids
Panel.to_json = panel_to_json
Panel.save = panel_save
Panel.delete = panel_delete
Panel.new = panel_new
Panel.count = panel_count




