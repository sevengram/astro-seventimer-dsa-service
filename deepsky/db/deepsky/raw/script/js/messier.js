for (var i = 1; i <= 110; i++){
    var obj = db.deepsky.findOne({'alias':'M'+i});
    if (obj == null){
        print('Cannot find M' + i);
    } else {
        db.catalogs.messier.insert({'object':'M'+i, 'data':new DBRef('deepsky',obj._id)});
    }
}
