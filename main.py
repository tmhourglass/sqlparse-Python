'''
Author: Shaowen He
Date: 2024-11-07 11:05:51
LastEditors: heshw@live.cn
LastEditTime: 2024-11-07 14:24:25
FilePath: /sqlparse-Python/main.py
Description:

Copyright (c) 2024 by Shaowen He, All Rights Reserved.
'''
from MainDef import *


def process_sql_visualization(sql_str: str):
    """处理SQL语句并生成可视化"""
    try:
        statements = analysis_statements(sql_str)
        analyzer = BloodlineAnalyzer()
        visualizer = BloodlineVisualizer()

        for stmt in statements:
            analyzer.reset()

            # 分析血缘关系
            table_bloodline = analyzer.analyze_table_bloodline(stmt)
            if not table_bloodline:
                print(f"警告: 在SQL语句中没有找到表名: {stmt}")
                continue

            column_bloodline = analyzer.analyze_column_bloodline(stmt)

            # 创建可视化
            table_viz = visualizer.create_table_tree(
                analyzer.state.table_names,
                stmt.get_type()
            )

            if column_bloodline:
                column_viz = visualizer.create_column_sankey(
                    analyzer.state.table_names,
                    analyzer.state.column_names
                )

            # 显示结果
            if table_viz:
                display(table_viz)
            if column_viz:
                display(column_viz)

    except Exception as e:
        print(f"处理SQL可视化时发生错误: {e}")


if __name__ == '__main__':

    # 创建分析器和可视化器实例
    analyzer = BloodlineAnalyzer()
    visualizer = BloodlineVisualizer()

    # 读取SQL文件
    sql_str = get_sqlstr('example_complex_sql.sql')
    statements = analysis_statements(sql_str)

    # 对每个SQL语句进行分析
    for stmt in statements:
        # 重置分析器状态
        analyzer.reset()

        # 分析血缘关系
        table_bloodline = analyzer.analyze_table_bloodline(stmt)
        column_bloodline = analyzer.analyze_column_bloodline(stmt)

        print(table_bloodline)
        print(column_bloodline)

        print('--------------------------------')

        # 可视化
        process_sql_visualization(sql_str)



