rm -f 01.file_test.db.symb
sqlite 01.file_test.db.symb  "create table t1 (t1key INTEGER PRIMARY KEY,data TEXT,num double,timeEnter DATE);"
sqlite 01.file_test.db.symb  "insert into t1 (data,num) values ('This is sample data',3);"
sqlite 01.file_test.db.symb  "insert into t1 (data,num) values ('More sample data',6);"
sqlite 01.file_test.db.symb  "insert into t1 (data,num) values ('And a little more',9);"
