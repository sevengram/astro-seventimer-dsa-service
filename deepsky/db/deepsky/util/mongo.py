# -*- coding:utf8 -*-

import re
import pymongo

FROM_OBJECT = 1
FROM_ALIAS = 2
TO_OBJECT = 4
TO_ALIAS = 8

def with_key(record, key):
    if not record.has_key(key) or not record[key]:
        return False
    value = record[key]
    if isinstance(value, str) and (
        value.lower() == 'n/a' or value.lower() == 'unknown' 
        or re.compile('^-*$').match(value)):
        return False
    if key == 'mag': 
        return value != 99.9
    if key == 'brstr' or key == 'subr': 
        return value != 99.9 and value != 79.9
    if key == 'type': 
        return value != 'NONEX'
    return True

class Connector(object):
    def __init__(self, debug=False):
        self.connection = pymongo.Connection('localhost', 27017)
        self.datadb = self.connection.astro_data
        self.userdb = self.connection.astro_users
        self.debug = debug

    def __def__(self):
        self.connection.close()

    def __setvalue__(self, collection, old_record, key, value):
        print('Update: %s: %s <= %s' % (old_record['object'], key, value))
        if not self.debug:
            collection.update({'_id':old_record['_id']}, {'$set':{key: value}})

    def __addtoset__(self, collection, old_record, key, value):
        print('Update: %s: %s add %s' % (old_record['object'], key, value))        
        if not self.debug:
            collection.update({'_id':old_record['_id']}, {'$addToSet':{key:value}})

    def __addalltoset__(self, collection, old_record, key, values):
        print('Update: %s: %s add %s' % (old_record['object'], key, values))        
        if not self.debug:
            collection.update({'_id':old_record['_id']}, {'$addToSet':{key:{'$each':values}}})

    def __insert__(self, collection, item):
        print("Insert: %s"% item)
        if not self.debug:
            collection.insert(item)

    def __update__(self, collection, old_record, new_record, update_keys, overwrite_keys):
        for key in update_keys:
            if key != 'alias' and key != 'notes' and with_key(new_record, key) and not with_key(old_record, key):
                self.__setvalue__(collection, old_record, key, new_record[key])
        for key in overwrite_keys:
            if key != 'alias' and key != 'notes' and with_key(new_record, key):
                self.__setvalue__(collection, old_record, key, new_record[key])

        names = [new_record['object']] if new_record.has_key('object') else []
        if new_record.has_key('alias'):
            if isinstance(new_record['alias'],list):
                names.extend(new_record['alias'])
            else:
                names.append(new_record['alias'])
        try:
            names.remove(old_record['object'])
        except ValueError:
            pass
        if names:
            self.__addalltoset__(collection, old_record, 'alias', names)

        if new_record.has_key('notes') and new_record['notes']:
            notes = old_record['notes'] + ' ' + new_record['notes'] if old_record.has_key('notes') else new_record['notes']
            self.__setvalue__(collection, old_record, 'notes', notes)

    def __search__(self, collection, item, search_mode):
        names = [item['object']] if item.has_key('object') and search_mode & FROM_OBJECT  else []
        if search_mode & FROM_ALIAS and item.has_key('alias'):
            if isinstance(item['alias'],list):
                names.extend(item['alias'])
            else:
                names.append(item['alias'])
        results = []
        for name in names:
            if search_mode & TO_OBJECT:
                results.extend([record for record in collection.find({'object':name})])
            if search_mode & TO_ALIAS:
                results.extend([record for record in collection.find({'alias':name})])
        return results

    def update(self, item, table, update_keys, overwrite_keys=[], search_mode=5):
        collection = getattr(self.datadb, table);
        results = self.__search__(collection, item, search_mode)
        if not results:
            self.__insert__(collection, item)
        else:
            for record in results:
                self.__update__(collection, record, item, update_keys, overwrite_keys)

    def set_unique_index(self, database, table, key):
        db = getattr(self.connection, database)
        collection = getattr(db, table)
        collection.create_index(key, unique=True)

    def add_to_catalogs(self, table, object_name, catalog_name):
        src_collection = getattr(self.datadb, table)
        target_collection = getattr(self.datadb.catalogs, catalog_name)
        obj = src_collection.find_one({'object': object_name})
        if not obj:
            obj = src_collection.find_one({'alias': object_name})
        if not obj:
            print('Cannot find %s' % object_name)
        else:
            item = {'object':obj['object'], 'data':DBRef(table, obj['_id'])}
            self.__insert__(target_collection, item)

    def add_user_record(self, table, username, object_name, observing_time):
        src_collection = getattr(self.datadb, table)
        target_collection = getattr(self.userdb, username).records
        obj = src_collection.find_one({'object': object_name})
        if not obj:
            obj = src_collection.find_one({'alias': object_name})
        if not obj:
            print('Cannot find %s' % object_name)
        else:
            history = target_collection.find_one({'object':obj['object']})
            if not history:
                item = {'object':obj['object'],'history':observing_time,'data':{
                            'database':self.datadb.name, 'collection':table, 'id':obj['_id']}}
                if obj.has_key('alias'):
                    item['alias'] = obj['alias']
                if obj.has_key('mag'):
                    item['mag'] = obj['mag']
                if obj.has_key('type'):
                    item['type'] = obj['type']
                self.__insert__(target_collection, item)
            elif len(observing_time) != 0:
                self.__addalltoset__(target_collection, history, 'history', observing_time)

    def add_skylist_record(self, table, username, record, observing_time):
        src_collection = getattr(self.datadb, table)
        target_collection = getattr(self.userdb, username).records
        obj = None
        for object_name in record['CatalogNumber']:
            object_name = object_name.replace(' ','')
            obj = src_collection.find_one({'object': object_name})
            if not obj:
                obj = src_collection.find_one({'alias': object_name})
            if obj != None:
                break
        if not obj:
            for object_name in record['CatalogNumber']:
                pattern = '^' + object_name.replace(' ','') + '[A-Z\-]+'
                obj = src_collection.find_one({'object': {'$regex':pattern}})
                if not obj:
                    pattern = '^' + object_name + '-'
                    obj = src_collection.find_one({'alias': {'$regex':pattern}})
                if obj != None:
                    break
        if not obj:
            print('Cannot find %s' % object_name)
        else:
            history = target_collection.find_one({'object':obj['object']})
            if not history:
                item = {'object':obj['object'],'history':observing_time,'data':{
                            'database':self.datadb.name, 'collection':table, 'id':obj['_id']}}
                if obj.has_key('alias'):
                    item['alias'] = obj['alias']
                if obj.has_key('mag'):
                    item['mag'] = obj['mag']
                if obj.has_key('type'):
                    item['type'] = obj['type']
                self.__insert__(target_collection, item)
            elif len(observing_time) != 0:
                self.__addalltoset__(target_collection, history, 'history', observing_time)

    def add_to_ssinfo(self, table, record):
        src_collection = getattr(self.datadb, table)
        target_collection = self.datadb.ssinfo
        obj = None
        for object_name in record['CatalogNumber']:
            object_name = object_name.replace(
                '-0','-').replace('+0','+').replace(
                'PK 0','PK ').replace('PN G0','PN G').replace(
                'PK 0', 'PK ').replace('PN G0', 'PN G').replace(
                'St ', 'Stock ').replace('A ', 'Abell ').replace(
                'MCG ','MCG-').replace('Bo ', 'Bochum').replace(
                'Ste ','Steph').replace('Dol-Dzim ','DoDz').replace(
                'Ho ','Hogg').replace('Bl ','Blanco').replace(
                'Pi ','Pismis').replace('Be ','Berk').replace(
                'Bas ','Basel').replace('Ha ','Harvard')
            object_name = object_name.replace(' ','')
            if not object_name.startswith('Abell'):
                obj = src_collection.find_one({'object': object_name})
            if not obj:
                obj = src_collection.find_one({'alias': object_name})
            if obj != None:
                break
        if not obj:
            for object_name in record['CatalogNumber']:
                object_name = object_name.replace(
                    '-0','-').replace('+0','+').replace(
                    'PK 0','PK ').replace('PN G0','PN G').replace(
                    'PK 0', 'PK ').replace('PN G0', 'PN G').replace(
                    'St ', 'Stock ').replace('A ', 'Abell ').replace(
                    'MCG ','MCG-').replace('Bo ', 'Bochum').replace(
                    'Ste ','Steph').replace('Dol-Dzim ','DoDz').replace(
                    'Ho ','Hogg').replace('Bl ','Blanco').replace(
                    'Pi ','Pismis').replace('Be ','Berk').replace(
                    'Bas ','Basel').replace('Ha ','Harvard')
                pattern = '^' + object_name.replace(' ','') + '[A-Z\-]+'
                if not object_name.startswith('Abell'):
                    obj = src_collection.find_one({'object': {'$regex':pattern}})
                if not obj:
                    pattern = '^' + object_name + '-'
                    obj = src_collection.find_one({'alias': {'$regex':pattern}})
                if obj != None:
                    break
        if not obj:
            print('Cannot find %s' % record)
        else:
            item = {}
            item['object'] = obj['object']
            if obj.has_key('alias'):
                item['alias'] = obj['alias']
            item['skysafari_info'] = record
            item['ref'] = table
            self.__insert__(target_collection, item)


