'''
Author: Shaowen He
Date: 2024-11-06 17:40:27
LastEditors: heshw@live.cn
LastEditTime: 2024-11-06 18:07:46
FilePath: /sqlparse-Python/sqlparse/GetTableBlood.py
Description: 获取SQL语句中的表血缘关系

Copyright (c) 2024 by Shaowen He, All Rights Reserved.
'''
from MainDef import *

if __name__ == '__main__':
    sql=get_sqlstr('example_complex_sql.sql')
    stmt_tuple=analysis_statements(sql)
    for each_stmt in stmt_tuple:
        print(blood_table(each_stmt))
