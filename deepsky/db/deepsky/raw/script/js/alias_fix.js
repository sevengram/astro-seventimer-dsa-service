var cursor = db.deepsky.find({'alias':{$regex:/^Berkeley/}})
while(cursor.hasNext()){
    obj = cursor.next();
    var new_alias = []
    for (var i = 0; i < obj.alias.length; i++){
        if (obj.alias[i].substring(0,8) != "Berkeley")
            new_alias.push(obj.alias[i]);
    }
    printjson(new_alias);
    db.deepsky.update({'_id':obj._id},{'$set':{'alias':new_alias}});
}

