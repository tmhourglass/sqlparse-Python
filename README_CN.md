# SQL血缘分析工具说明文档

## 功能概述

这是一个基于Python sqlparse库开发的SQL血缘分析工具，用于分析SQL语句中的表和字段之间的依赖关系。

## 主要功能

### 1. SQL解析功能

- 使用sqlparse库解析SQL语句
- 支持识别SQL语句的类型(SELECT/INSERT/CREATE等)
- 可以构建SQL的AST(抽象语法树)结构

### 2. 血缘关系分析功能

#### 2.1 表血缘分析

- 自动识别SQL中的表名
- 分析表之间的依赖关系
- 支持多表联合查询的血缘分析
- 可处理子查询场景

#### 2.2 字段血缘分析

- 识别SQL中的字段名
- 追踪字段间的依赖传递
- 支持字段别名解析
- 处理函数和表达式中的字段依赖

### 3. 可视化展示

#### 3.1 表血缘可视化

- 使用pyecharts树形图展示表间关系
- 直观展示数据流向
- 支持交互式操作
- 可导出为HTML格式

#### 3.2 字段血缘可视化

- 使用Sankey图展示字段依赖
- 清晰显示数据流动路径
- 支持节点拖拽和缩放
- 提供完整的血缘链路展示

## 使用场景

- 数据治理与管理
- 数据血缘追踪
- 数据安全分析
- 数据中台建设
- ETL任务依赖分析

## 技术特点

1. 解析引擎
   - 基于sqlparse的SQL解析
   - 支持复杂SQL语句
   - 高效的Token处理机制

2. 血缘分析
   - 精准的依赖关系识别
   - 完整的血缘链路追踪
   - 支持多种SQL语法

3. 可视化能力
   - 直观的图形化展示
   - 交互式操作体验
   - 多种展示形式支持

## 使用说明

### 安装依赖

```bash
pip install sqlparse
pip install pyecharts
```

### 基本用法

```python
from sqlparse import MainDef
# 解析SQL并分析表血缘
blood_result = MainDef.blood_table(sql_statement)
# 分析字段血缘
column_result = MainDef.blood_column(sql_statement)
# 生成可视化图表
MainDef.Tree_visus(table_names, type_name)
MainDef.column_visus()
```

## 注意事项

1. 确保SQL语句格式正确
2. 大型SQL建议分段处理
3. 可视化展示需要足够的显示空间
4. 注意内存使用情况

## 后续规划

- [ ] 支持更多数据库方言
- [ ] 优化大规模SQL处理性能
- [ ] 添加更多可视化方案
- [ ] 提供Web服务接口
- [ ] 支持批量SQL处理
