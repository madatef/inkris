import re
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from duckdb import BinderException
from langchain.tools import tool
from sqlalchemy import select

from app.storage.s3_provider import s3
from app.db.duckdb import get_con as duckdb_con
from app.db.session import AsyncSessionLocal
from app.models.excel_metadata import ExcelMetadata



ALLOWED_OPERATORS = {
    "=": "=",
    "!=": "!=",
    ">": ">",
    ">=": ">=",
    "<": "<",
    "<=": "<=",
    "ilike": "ILIKE",
    "like": "LIKE",
    "in": "IN",
    "not_in": "NOT IN",
    "between": "BETWEEN",
    "is_null": "IS NULL",
    "is_not_null": "IS NOT NULL"
}

ALLOWED_AGGREGATIONS = {'min', 'max', 'sum', 'avg', 'count'}

def validate_column(column: str, allowed_columns: set) -> str:
    """
    Validates column name and extracts the actual column from aggregations.
    Returns the validated column (or raises ValueError).
    """
    
    # Check for aggregation functions using regex
    agg_pattern = r'^(min|max|sum|avg|count)\((.+?)\)$'
    match = re.match(agg_pattern, column, re.IGNORECASE)
    
    if match:
        func, inner_col = match.groups()
        
        # For COUNT(*), allow it
        if func.lower() == 'count' and inner_col == '*':
            return column
        
        # Validate the inner column
        if inner_col not in allowed_columns:
            raise ValueError(f"Invalid column in aggregation: {inner_col}")
        
        return f'{func.upper()}("{inner_col}")'
    
    # Not an aggregation, must be a regular column
    if column not in allowed_columns:
        raise ValueError(f"Invalid column: {column}. Make sure the column name is valid and/or only these aggregates are used: {ALLOWED_AGGREGATIONS}")
    
    return f'"{column}"'

def compile_filter(
    filter_node: Dict[str, Any], 
    allowed_columns: set
) -> Tuple[str, List[Any]]:
    """
    Recursively compiles a filter tree into SQL WHERE clause and parameters.
    
    Filter structure:
    - Logical node: {"logical_operator": "AND"/"OR", "conditions": [node1, node2, ...]}
    - Leaf node: {"column": "col_name", "op": "=", "value": value}
    """
    
    # Handle logical operators (AND/OR)
    if "conditions" in filter_node:
        op = filter_node["logical_operator"].upper()
        if op not in ("AND", "OR"):
            raise ValueError(f"Invalid logical operator: {op}. Vald operators: ['AND', 'OR']")

        conditions = filter_node["conditions"]
        if not conditions:
            raise ValueError("Logical operator must have at least one condition")

        clauses = []
        params = []

        for cond in conditions:
            clause, clause_params = compile_filter(cond, allowed_columns)
            clauses.append(f"({clause})")
            params.extend(clause_params)

        return f" {op} ".join(clauses), params

    # Handle leaf nodes (actual conditions)
    column = filter_node.get("column")
    operator = filter_node.get("op")
    value = filter_node.get("value")

    if not column or not operator:
        raise ValueError("Filter must have 'column' and 'op' fields")

    # Validate column
    validated_column = validate_column(column, allowed_columns)

    # Validate operator
    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"Invalid operator: {operator}")

    sql_op = ALLOWED_OPERATORS[operator]
    if not sql_op:
        raise ValueError(f"Invalid SQL operator: {sql_op}")

    # Handle different operator types
    if operator in ("is_null", "is_not_null"):
        # No value needed for NULL checks
        return f"{validated_column} {sql_op}", []

    if value is None:
        raise ValueError(f"Operator '{operator}' requires a value")

    if operator in ("in", "not_in"):
        if not isinstance(value, (list, tuple)) or len(value) == 0:
            raise ValueError(f"{operator.upper()} requires a non-empty list")
        placeholders = ",".join(["?"] * len(value))
        return f"{validated_column} {sql_op} ({placeholders})", list(value)

    elif operator == "between":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("BETWEEN requires exactly two values [min, max]")
        return f"{validated_column} BETWEEN ? AND ?", list(value)

    else:
        # Standard comparison operators
        return f"{validated_column} {sql_op} ?", [value]

def build_where_clause(
    row_filters: Optional[Union[Dict, List[Dict]]], 
    allowed_columns: set
) -> Tuple[str, List[Any]]:
    """
    Build complete WHERE clause from filters.
    
    Args:
        row_filters: Single filter dict, list of filters (implicit AND), or None
        allowed_columns: Set of valid column names
    
    Returns:
        Tuple of (where_clause_sql, parameters)
    """
    if not row_filters:
        return "", []
    
    # Normalize to dict format
    if isinstance(row_filters, list):
        # Multiple filters = implicit AND
        filter_node = {"op": "AND", "conditions": row_filters}
    else:
        filter_node = row_filters
    
    sql_where, params = compile_filter(filter_node, allowed_columns)
    return f"WHERE {sql_where}", params

@tool(parse_docstring=True)
async def fetch_data(
    file_id: str,
    sheet_name: str,
    columns: Optional[List[str]] = None,
    row_filters: Optional[Union[Dict, List[Dict]]] = None,
    limit: Optional[int] = None,
) -> Any:
    """Fetch spreadsheet data using file ID and sheet name.

    Args:
        file_id: ID of the file in question.
        sheet_name: The sheet to fetch from.
        columns: Which columns to retrieve (Aggregate functions on columns are supported, e.g.: COUNT(User Files). Defaults to None (to fetche all columns). Use column names as-is and DON'T trim leading/trailing spaces.
        row_filters: Filter by row values. Can be a single filter dict, a list of filters (implicit AND), or a nested structure with AND/OR operators. Defaults to None.
        limit: The max no. of rows to fetch. Defaults to None (no limit).

    Returns:
        A dictionary with keys:
            - headers: A list of the column names/headers.
            - records: A list of rows. The values in the rows follow the same order as the headers.
        
    """
    
    # Build S3 path
    key = f"{file_id}/{sheet_name}.parquet"
    s3_path = f"s3://{s3.bucket_name}/{key}"

    con = duckdb_con()

    # Get schema to validate columns
    async with con.execute(f"""
        SELECT *
        FROM read_parquet('{s3_path}')
        LIMIT 0
    """) as schema_cursor:
        schema_df = await schema_cursor.df()

    allowed_columns = set(schema_df.columns)
    
    # Build SELECT clause
    if columns:
        corrected_syntax_columns = []
        # Validate each column
        for col in columns:
            try:
                corr = validate_column(col, allowed_columns)
                corrected_syntax_columns.append(corr)
            except ValueError as e:
                return f'error: {str(e)}'
        select_clause = ", ".join(corrected_syntax_columns)
    else:
        select_clause = "*"
    
    # Build WHERE clause
    where_clause, params = build_where_clause(row_filters, allowed_columns)
    
    # Construct final query
    query = f"SELECT {select_clause} FROM read_parquet('{s3_path}') {where_clause}"

    if limit:
        query += f" LIMIT {limit}"
    
    # Execute with parameters (safe from SQL injection)
    try:
        async with con.execute(query, params) as result_cursor:
            result_df = await result_cursor.df()
    except BinderException as e:
        return f'error: {str(e)}'
    
    headers = result_df.columns.tolist()
    records = result_df.values.tolist()
    
    return {'headers': headers, 'records': records}

@tool(parse_docstring=True)
async def get_sheet_metadata(file_id: str, sheet_name: str):
    """
    Get sheet column names, data types, nullability, etc. along with a 3-row preview.

    Args:
        file_id: ID of the file.
        sheet_name: the sheet in question.

    Returns: 
        Dict with keys:
            - columns: a list of all column names.
            - preview: a list of 2 records/rows. Each row is a list with values corresponding to 'columns' key, with the same order.
    """

    key = f"{file_id}/{sheet_name}.parquet"
    s3_path = f"s3://{s3.bucket_name}/{key}"

    try:
        con = duckdb_con()
        async with con.execute(f"SELECT * FROM read_parquet('{s3_path}') LIMIT 2") as cursor:
            df = await cursor.df()
        columns = df.columns.tolist()
        preview = df.values.tolist()
    except Exception as e:
        return f'error: {str(e)}' 

    return {'columns': columns, 'preview': preview}

@tool(parse_docstring=True)
async def get_sheets_names(file_id: str):
    """
    Gets names of all sheets in a file.

    Args:
    file_id (str): file in question.

    Returns: a list of all sheet names as-is.
    """
    stmt = select(ExcelMetadata).where(ExcelMetadata.file_id == UUID(file_id))
    try:
        async with AsyncSessionLocal() as session:
            meta = (await session.execute(stmt)).scalar_one_or_none().file_metadata
    except Exception as e:
        return f'error: {str(e)}'
    return meta


EXCEL_TOOLS = [fetch_data, get_sheet_metadata, get_sheets_names]