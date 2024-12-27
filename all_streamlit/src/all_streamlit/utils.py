import re


class TableMetadata:
    def __init__(self, catalog="", schema="", table_name=""):
        self.catalog = catalog
        self.schema = schema
        self.table_name = table_name


def extract_table_metadata(ddl: str) -> TableMetadata:
    """
    Example:
    ```python
    vn.extract_table_metadata("CREATE TABLE hive.bi_ads.customers (id INT, name TEXT, sales DECIMAL)")
    ```

    Extracts the table metadata from a DDL statement. This is useful in case the DDL statement contains other information besides the table metadata.
    Override this function if your DDL statements need custom extraction logic.

    Args:
        ddl (str): The DDL statement.

    Returns:
        TableMetadata: The extracted table metadata.
    """
    pattern_with_catalog_schema = re.compile(
        r"CREATE TABLE\s+(\w+)\.(\w+)\.(\w+)\s*\(", re.IGNORECASE
    )
    pattern_with_schema = re.compile(r"CREATE TABLE\s+(\w+)\.(\w+)\s*\(", re.IGNORECASE)
    pattern_with_table = re.compile(r"CREATE TABLE\s+(\w+)\s*\(", re.IGNORECASE)

    match_with_catalog_schema = pattern_with_catalog_schema.search(ddl)
    match_with_schema = pattern_with_schema.search(ddl)
    match_with_table = pattern_with_table.search(ddl)

    if match_with_catalog_schema:
        catalog = match_with_catalog_schema.group(1)
        schema = match_with_catalog_schema.group(2)
        table_name = match_with_catalog_schema.group(3)
        return TableMetadata(catalog, schema, table_name)
    elif match_with_schema:
        schema = match_with_schema.group(1)
        table_name = match_with_schema.group(2)
        return TableMetadata("", schema, table_name)
    elif match_with_table:
        table_name = match_with_table.group(1)
        return TableMetadata("", "", table_name)
    else:
        return TableMetadata()
