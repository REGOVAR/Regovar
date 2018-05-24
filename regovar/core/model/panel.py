#!env/python3
# coding: utf-8
import os
import uuid


from core.framework.common import *
from core.framework.postgresql import *




# =====================================================================================================================
# TOOL
# =====================================================================================================================

def format_entries(json):
    result = []
    for entry in json:
        fixed = {}
        if "type" in entry and entry["type"] == "gene":
            try:
                fixed["type"] = "gene"
                fixed["symbol"] = str(entry["symbol"])
                fixed["details"] = str(entry["details"])
                result.append(fixed)
            except Exception as ex:
                raise RegovarException("Unable to create panel with provided data", exception=ex)
        else:
            try:
                fixed["type"] = "region"
                fixed["label"] = str(entry["label"])
                fixed["chr"] = str(CHR_DB_RMAP[str(entry["chr"])])
                fixed["start"] = str(entry["start"])
                fixed["end"] = str(entry["end"])
                result.append(fixed)
            except Exception as ex:
                raise RegovarException("Unable to create panel with provided data", exception=ex)
        
    return result






# =====================================================================================================================
# PANEL
# /!\ As SQLAlchemy is not able to automaticaly create class for table with int8range field, we manage it ourself
# =====================================================================================================================


def panel_init(self, loading_depth=0):
    """
        Init properties of a panel :
            - id          : str           : The universam unique id of the panel in the database
            - versions    : [json]        : The ordered list of version: from current (idx=0) to formest (idx=count)
            - name        : str           : The name
            - description : str           : An optional description
            - owner       : str           : The owner
            - update_date : date          : The last time that the object have been updated
            - create_date : date          : The datetime when the object have been created
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - versions    : [json]        : The list of entries by version of the panel
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth") and self.loading_depth >= loading_depth:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.versions = self.get_versions()
    except Exception as ex:
        raise RegovarException("Panel data corrupted (id={}).".format(self.id), "", ex)



def panel_from_id(panel_id, loading_depth=0):
    """
        Retrieve panel with the provided id in the database
    """
    panel = Session().query(Panel).filter_by(id=panel_id).first()
    if panel:
        Session().refresh(panel)
        panel.init(loading_depth)
    return panel


def panel_from_ids(panel_ids, loading_depth=0):
    """
        Retrieve panels corresponding to the list of provided id
    """
    panels = []
    if panel_ids and len(panel_ids) > 0:
        panels = Session().query(Panel).filter(Panel.id.in_(panel_ids)).all()
        for f in panels:
            Session().refresh(f)
            f.init(loading_depth)
    return panels


def panel_to_json(self, fields=None, loading_depth=-1):
    """
        Export the panel into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Panel.public_fields
    for f in fields:
        if f in Panel.public_fields:
            if f in ["create_date", "update_date"]:
                result[f] = eval("self." + f + ".isoformat()")
            elif f in ["versions"]:
                versions = []
                for v in self.versions:
                    versions.append({
                        "id": v["id"], 
                        "version": v["version"], 
                        "comment": v["comment"], 
                        "entries": v["entries"], 
                        "create_date": v["create_date"].isoformat(), 
                        "update_date": v["update_date"].isoformat()})
                result[f] = versions
            elif hasattr(self, f):
                result[f] = eval("self." + f)
    return result


def panel_load(self, data):
    try:
        # Required fields
        if "name" in data.keys(): self.name = check_string(data['name'])
        if "description" in data.keys(): self.description = check_string(data['description'])
        if "owner" in data.keys(): self.owner = check_string(data['owner'])
        if "update_date" in data.keys(): self.update_date = check_date(data['update_date'])
        if "shared" in data.keys(): self.shared = check_bool(data['shared'])
        self.save()
        
        # if version id provided : update version  (can be done for one version at time)
        if "version_id" in data.keys() and data["version_id"]:
            version_id = data["version_id"]
            
            # Update internal collection
            for v in self.versions:
                if v["id"] == version_id:
                    v["update_date"] = datetime.datetime.now()
                    if "version" in data.keys():
                        v["version"] = sql_escape(data["version"])
                        execute("UPDATE TABLE panel_entry SET version='{1}' WHERE id='{0}'".format(version_id, v["version"]))
                    if "comment" in data.keys():
                        v["comment"] = sql_escape(data['comment'])
                        execute("UPDATE panel_entry SET comment='{2}' WHERE id='{0}'".format(version_id, v["comment"]))
                          
        # else, if only data provided : create new version
        elif "entries" in data.keys():
            version = sql_escape(check_string(data["version"], "")) if "version" in data else ""
            comment = sql_escape(check_string(data["comment"], "")) if "comment" in data else ""
            
            entries = format_entries(data['entries'])
            entries = json.dumps(entries)
            pv_uuid = str(uuid.uuid4())
            sql = "INSERT INTO panel_entry (id, panel_id, version, data, comment, update_date) VALUES ('{3}', '{0}', '{1}', '{2}', '{4}', CURRENT_TIMESTAMP)"
            execute(sql.format(self.id, version, entries, pv_uuid, comment))

            # Reload version from db
            self.versions = self.get_versions()
    except Exception as ex:
        raise RegovarException('Panel error', ex)
    return self


def panel_save(self):
    generic_save(self)


def panel_delete(panel_id):
    """
        Delete the panel with the provided id in the database
    """
    execute("DELETE * FROM panel_entry WHERE panel_id={0}".format(self.id))
    Session().query(Panel).filter_by(id=panel_id).delete(synchronize_session=False)


def panel_new():
    """
        Create a new panel and init/synchronise it with the database
    """
    s = Panel()
    s.id = str(uuid.uuid4()) # universal unique id as panel may be shared with others servers
    s.save()
    s.init()
    return s


def panel_count():
    """
        Return total of Panel entries in database
    """
    return generic_count(Panel)



def panel_get_versions(self):
    """
        Return list of all version defined for the panel.
    """
    result = []
    for row in execute("SELECT * from panel_entry WHERE panel_id LIKE '{}' ORDER BY create_date DESC".format(self.id)):
        result.append({"id": row.id, "version": row.version, "comment": row.comment, "entries": row.data, "create_date": row.create_date, "update_date": row.update_date})
    return result



Panel = Base.classes.panel
Panel.public_fields = ["id", "versions", "name", "description", "owner", "create_date", "update_date", "shared"]


Panel.init = panel_init
Panel.from_id = panel_from_id
Panel.from_ids = panel_from_ids
Panel.to_json = panel_to_json
Panel.load = panel_load
Panel.save = panel_save
Panel.delete = panel_delete
Panel.new = panel_new
Panel.count = panel_count
Panel.get_versions = panel_get_versions




