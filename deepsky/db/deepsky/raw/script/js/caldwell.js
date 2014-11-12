for (var i = 1; i <= 110; i++){
    var obj = db.deepsky.findOne({'alias':'C'+i});
    if (obj == null){
        print('Cannot find C' + i);
    } else {
        //print(obj);
        db.catalogs.caldwell.insert({'object':'C'+i, 'data':new DBRef('deepsky',obj._id)});
    }
}
