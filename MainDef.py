"""
SQL血缘分析工具
用于分析SQL语句中的表和字段之间的血缘关系,并提供可视化功能
"""

import textwrap
from typing import Union, Set, List

import sqlparse
from sqlparse.sql import Parenthesis, Function, Identifier, IdentifierList
from sqlparse.tokens import Keyword, Name
import pyecharts
from pyecharts import options as opts
from pyecharts.charts import Tree, Sankey


# 常量定义
COLUMN_OPERATIONS = {'SELECT', 'FROM'}
FUNCTION_OPERATIONS = {'SELECT', 'DROP', 'INSERT', 'UPDATE', 'CREATE'}
RESULT_OPERATIONS = {'UNION', 'INTERSECT', 'EXCEPT', 'SELECT'}
PRECEDES_TABLE_NAME = {'FROM', 'JOIN', 'DESC', 'DESCRIBE', 'WITH'}
ON_KEYWORD = 'ON'

class GlobalState:
    """全局状态管理类"""
    def __init__(self):
        self.table_names = []     # 存储表名
        self.column_names = []    # 存储列名
        self.function_names = []  # 存储函数名
        self.alias_names = []     # 存储别名
        self.columns_rank = 0     # 列的层级

    def reset(self):
        """重置所有状态"""
        self.__init__()

class TokenUtils:
    """Token工具类"""
    @staticmethod
    def is_identifier(token):
        """判断是否为标识符"""
        return isinstance(token, (IdentifierList, Identifier))

    @staticmethod
    def is_identifier_single(token):
        """判断是否为单个标识符"""
        return isinstance(token, Identifier)

    @staticmethod
    def is_identifier_list(token):
        """判断是否为标识符列表"""
        return isinstance(token, IdentifierList)

    @staticmethod
    def is_function(token):
        """判断是否为函数"""
        return isinstance(token, Function)

    @staticmethod
    def is_parenthesis(token):
        """判断是否为括号"""
        return isinstance(token, Parenthesis)

    @staticmethod
    def precedes_function_name(token_value):
        """判断是否为函数名前缀"""
        return any(keyword in token_value for keyword in FUNCTION_OPERATIONS)

    @staticmethod
    def precedes_table_name(token_value):
        """判断是否为表名前缀"""
        return any(keyword in token_value for keyword in PRECEDES_TABLE_NAME)

    @staticmethod
    def is_result_operation(keyword):
        """判断是否为结果操作"""
        return any(op in keyword.upper() for op in RESULT_OPERATIONS)

class BloodlineAnalyzer:
    """血缘分析核心类"""
    def __init__(self):
        self.state = GlobalState()

    def reset(self):
        """重置分析器状态"""
        self.state.reset()

    def _process_identifier(self, identifier):
        """处理标识符"""
        if '(' not in str(identifier):
            self._get_identifier_tables(identifier)
            return
        self._extract_tables(identifier)

    def _process_column_identifier(self, identifier):
        """处理列标识符"""
        self._get_identifier_columns(identifier)
        self._extract_columns(identifier)

    def _process_function_identifier(self, func):
        """处理函数标识符"""
        for item in func.tokens:
            if TokenUtils.is_identifier_single(item):
                self.state.function_names.append(item.value)
            self._extract_columns(item)

    def _get_identifier_tables(self, identifier):
        """从标识符中提取表名"""
        tokens = identifier.tokens
        if len(tokens) == 1:
            self.state.table_names.append(tokens[0].value)
            return

        if len(tokens) == 3 and tokens[1].value == ' ':
            self.state.table_names.append(tokens[0].value)
            return

        if len(tokens) > 1 and tokens[1].value == '.':
            db = tokens[0].value
            table = tokens[2].value
            full_name = f"{db}.{table}"

            if len(tokens) == 3:
                self.state.table_names.append(full_name)
            else:
                if tokens[3].value == ' ':
                    self.state.table_names.append(full_name)
                else:
                    schema = tokens[4].value
                    self.state.table_names.append(f"{db}.{table}.{schema}")

    def _get_identifier_columns(self, identifier):
        """从标识符中提取列名"""
        if len(identifier.tokens) == 1:
            if not isinstance(identifier.parent, Function):
                if self.state.columns_rank > 0:
                    self.state.column_names[self.state.columns_rank - 1].append(
                        identifier.tokens[0].value
                    )
            else:
                self.state.function_names.append(identifier.value)

        elif len(identifier.tokens) == 5:
            if identifier.tokens[0].ttype == Name:
                if self.state.columns_rank > 0:
                    self.state.column_names[self.state.columns_rank - 1].append(
                        identifier.tokens[0].value
                    )

        elif len(identifier.tokens) == 7:
            self.state.alias_names.append(identifier.tokens[0].value)

    def _create_column_lists(self):
        """创建列名列表"""
        if self.state.table_names:
            self.state.column_names = [[] for _ in range(len(self.state.table_names))]
        else:
            self.state.column_names = []

    def _clean_alias_columns(self):
        """清理别名列"""
        # 1. 确保有列数据
        if not self.state.column_names:
            return

        # 2. 对每个表的列去重
        for i in range(len(self.state.table_names)):
            if i < len(self.state.column_names):
                self.state.column_names[i] = list(set(self.state.column_names[i]))

        # 3. 移除别名
        cleaned_columns = []
        for cols in self.state.column_names:
            cleaned_columns.append(list(set(cols) - set(self.state.alias_names)))
        self.state.column_names = cleaned_columns

    def _extract_columns(self, statement):
        """提取列信息"""
        if not hasattr(statement, 'tokens'):
            return

        for item in statement.tokens:
            # 跳过空白和注释
            if item.is_whitespace or item.ttype == sqlparse.tokens.Comment:
                continue

            if item.is_group and not TokenUtils.is_identifier(item):
                self._extract_columns(item)

            if item.ttype in Keyword and item.value.upper() == 'SELECT':
                self.state.columns_rank += 1

            if isinstance(item, Identifier):
                self._process_column_identifier(item)

            if isinstance(item, IdentifierList):
                for token in item.tokens:
                    if TokenUtils.is_function(token):
                        self._process_function_identifier(token)
                    if TokenUtils.is_identifier(token):
                        self._process_column_identifier(token)

    def _extract_tables(self, statement):
        """提取表信息

        Args:
            statement: SQL语句解析后的语法树对象
        """
        if not hasattr(statement, 'tokens'):
            return

        table_name_preceding = False

        for item in statement.tokens:
            # 跳过空白字符和注释
            if item.is_whitespace or item.ttype == sqlparse.tokens.Comment:
                continue

            if item.is_group and not TokenUtils.is_identifier(item):
                self._extract_tables(item)

            if item.ttype in Keyword:
                if TokenUtils.precedes_table_name(item.value.upper()):
                    table_name_preceding = True
                    continue

            if not table_name_preceding:
                continue

            if item.ttype in Keyword or item.value == ',':
                if (TokenUtils.is_result_operation(item.value) or
                        item.value.upper() == ON_KEYWORD):
                    table_name_preceding = False
                    continue
                break

            if isinstance(item, Identifier):
                self._process_identifier(item)

            if isinstance(item, IdentifierList):
                for token in item.tokens:
                    if TokenUtils.is_identifier(token):
                        self._process_identifier(token)

    def analyze_table_bloodline(self, statement) -> Union[str, Set[str]]:
        """分析SQL语句中的表血缘关系

        Args:
            statement: SQL语句解析后的语法树对象

        Returns:
            对于非SELECT语句: 返回格式为 "目标表->源表集合" 的字符串
            对于SELECT语句: 返回涉及的所有表名集合
            如果没有找到表名: 返回空集合

        示例:
            INSERT语句: "target_table->{source_table1, source_table2}"
            SELECT语句: {"table1", "table2", "table3"}
        """
        # 1. 获取SQL语句类型(SELECT/INSERT/UPDATE等)
        type_name = statement.get_type()

        # 2. 处理函数操作(INSERT/UPDATE等)
        if TokenUtils.precedes_function_name(type_name):
            # 获取第一层标识符(通常是目标表)
            idfr_list = self._get_first_level_identifiers(statement)
            if idfr_list:
                # 将目标表添加到table_names列表
                self._get_identifier_tables(idfr_list[0])

        # 3. 提取语句中涉及的所有表名
        self._extract_tables(statement)

        # 4. 检查是否找到任何表名
        if not self.state.table_names:
            return set()  # 如果没有找到表名，返回空集合

        # 5. 根据语句类型返回不同格式的结果
        if type_name != 'SELECT':
            # 非SELECT语句: 第一个表为目标表,其余为源表
            inherit_table = self.state.table_names[0]  # 目标表
            root_tables = set(self.state.table_names[1:])  # 源表集合
            return f'{inherit_table}->{root_tables}'
        else:
            # SELECT语句: 返回所有涉及的表集合
            return set(self.state.table_names)

    def analyze_column_bloodline(self, statement) -> Union[str, List[List[str]]]:
        """分析字段血缘关系

        Args:
            statement: SQL语句解析后的语法树对象

        Returns:
            对于非SELECT语句: 返回格式为 "目标列->[源列]" 的字符串
            对于SELECT语句: 返回列名的二维列表
            如果没有找到列: 返回空列表
        """
        # 1. 检查是否有表
        if not self.state.table_names:
            return []

        # 2. 创建列名列表并提取列
        self._create_column_lists()
        self._extract_columns(statement)

        # 3. 处理函数名和别名
        self.state.function_names = list(set(self.state.function_names))
        self.state.alias_names = list(set(self.state.alias_names))
        self._clean_alias_columns()

        # 4. 检查是否有列
        if not any(self.state.column_names):
            return []

        # 5. 构建血缘关系
        zipped = list(zip(self.state.table_names, self.state.column_names))
        if not zipped:
            return []

        if statement.get_type() != 'SELECT':
            inherit_cols = zipped[0]
            root_cols = zipped[1:]
            return f'{inherit_cols}->{root_cols}'
        else:
            return self.state.column_names

    def _get_first_level_identifiers(self, statement):
        """获取第一层标识符"""
        return [token for token in statement.tokens
                if token._get_repr_name() == 'Identifier']


class BloodlineVisualizer:
    """血缘关系可视化类"""

    @staticmethod
    def create_table_tree(table_names: List[str], type_name: str) -> Optional[Tree]:
        """创建表血缘树图

        Args:
            table_names: 表名列表
            type_name: SQL语句类型

        Returns:
            Tree: 树图对象
            None: 如果没有表名数据
        """
        # 1. 输入验证
        if not table_names:
            print("警告: 没有表名数据可供可视化")
            return None

        # 2. 去重处理
        table_names = list(set(table_names))

        # 3. 根据SQL类型构建不同的树结构
        try:
            if type_name != 'SELECT':
                # 非SELECT语句: 第一个表为目标表，其他为源表
                children = [{"name": name} for name in table_names[1:]]
                data = [{"children": children, "name": table_names[0]}]
                title = f"血缘-{type_name}"
            else:
                # SELECT语句: 所有表平级展示
                children = [{"name": name} for name in table_names]
                data = [{"children": children, "name": 'SELECT'}]
                title = f"查询-{type_name}"

            # 4. 创建树图
            tree = (
                Tree()
                .add(
                    "",
                    data,
                    orient="TB",
                    initial_tree_depth=2,
                    collapse_interval=0
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(
                        title=title,
                        subtitle="表血缘关系图"
                    ),
                    toolbox_opts=opts.ToolboxOpts(is_show=True),
                    tooltip_opts=opts.TooltipOpts(
                        trigger="item",
                        trigger_on="mousemove"
                    )
                )
            )

            return tree.render_notebook()

        except Exception as e:
            print(f"创建表血缘树图时发生错误: {e}")
            return None

    @staticmethod
    def create_column_sankey(
        table_names: List[str],
        column_names: List[List[str]]
    ) -> Optional[Sankey]:
        """创建字段血缘桑基图

        Args:
            table_names: 表名列表
            column_names: 列名二维列表

        Returns:
            Sankey: 桑基图对象
            None: 如果没有数据可供可视化
        """
        # 1. 输入验证
        if not table_names or not column_names:
            print("警告: 没有数据可供可视化")
            return None

        try:
            # 2. 创建节点
            nodes = []
            # 添加表节点
            for table in table_names:
                nodes.append({"name": table})

            # 添加列节点
            for i in range(1, len(column_names)):
                for col in column_names[i]:
                    nodes.append({"name": col})

            # 去重
            nodes = [i for n, i in enumerate(nodes) if i not in nodes[:n]]

            # 3. 创建链接
            links = []
            # 表之间的链接
            for i in range(1, len(table_names)):
                links.append({
                    'source': table_names[0],
                    'target': table_names[i],
                    'value': 10
                })

            # 表和列之间的链接
            for i in range(1, len(table_names)):
                for col in column_names[i]:
                    links.append({
                        'source': table_names[i],
                        'target': col,
                        'value': 5
                    })

            # 4. 创建桑基图
            sankey = (
                Sankey()
                .add(
                    "表与字段",
                    nodes=nodes,
                    links=links,
                    linestyle_opt=opts.LineStyleOpts(
                        opacity=0.5,
                        curve=0.5,
                        color="source"
                    ),
                    label_opts=opts.LabelOpts(position="right"),
                    node_width=20,
                    node_gap=10,
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(
                        title="字段血缘",
                        subtitle="表与字段关系图"
                    )
                )
            )

            return sankey.render_notebook()

        except Exception as e:
            print(f"创建字段血缘桑基图时发生错误: {e}")
            return None

# 工具函数
def analysis_statements(sql_str):
    """解析SQL语句"""
    return sqlparse.parse(sql_str)

def get_sqlstr(file_path):
    """从文件读取SQL语句"""
    with open(file_path, encoding='utf-8') as file:
        content = file.read()
        sql_str = sqlparse.format(content, reindent=True, keyword_case='upper')
        sql_str = sql_str.strip(' \t\n;')
        return textwrap.indent(sql_str, "  ")
