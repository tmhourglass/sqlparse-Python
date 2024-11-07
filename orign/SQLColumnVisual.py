'''
Author: Shaowen He
Date: 2024-11-06 17:40:27
LastEditors: heshw@live.cn
LastEditTime: 2024-11-06 18:08:27
FilePath: /sqlparse-Python/sqlparse/SQLColumnVisual.py
Description: 可视化SQL语句中的字段血缘关系

Copyright (c) 2024 by Shaowen He, All Rights Reserved.
'''
from MainDef import *

if __name__ == '__main__':
    sql=get_sqlstr('example_complex_sql.sql')
    stmt_tuple=analysis_statements(sql)
    for each_stmt in stmt_tuple:
        type_name = get_main_functionsql(each_stmt)
        blood_table(each_stmt)
        blood_column(each_stmt)
        column_visus()
