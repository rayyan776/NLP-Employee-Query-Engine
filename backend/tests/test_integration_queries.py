import pytest
from services.query_parser import QueryParser
from services.sql_builder import SQLBuilder

mock_schema = {
    "tables": [
        {
            "name": "employees",
            "semantic_tag": "primary_entity",
            "columns": [
                {"name": "emp_id", "type": "INTEGER", "semantic_tag": "identifier"},
                {"name": "full_name", "type": "VARCHAR", "semantic_tag": "name"},
                {"name": "dept_id", "type": "INTEGER", "semantic_tag": "identifier"},
                {"name": "annual_salary", "type": "NUMERIC", "semantic_tag": "numeric_measure"},
                {"name": "join_date", "type": "DATE", "semantic_tag": "date"},
                {"name": "office_location", "type": "VARCHAR", "semantic_tag": "location"},
            ]
        },
        {
            "name": "departments",
            "semantic_tag": "organizational_unit",
            "columns": [
                {"name": "dept_id", "type": "INTEGER", "semantic_tag": "identifier"},
                {"name": "dept_name", "type": "VARCHAR", "semantic_tag": "name"},
                {"name": "manager_id", "type": "INTEGER", "semantic_tag": "identifier"},
            ]
        },
    ],
    "relationships": [
        {
            "from_table": "employees",
            "from_columns": ["dept_id"],
            "to_table": "departments",
            "to_columns": ["dept_id"]
        }
    ]
}


def build_query(query_text):
    """Helper to parse and build SQL"""
    parser = QueryParser()
    builder = SQLBuilder()
    intent = parser.parse_intent(query_text, mock_schema)
    sql, params = builder.build_sql(intent, mock_schema)
    return sql, params, intent


def test_avg_by_dept_sql_generation():
    """Test end-to-end SQL generation for grouped aggregation"""
    sql, params, intent = build_query("Average salary by department")
    
    # Verify SQL structure
    assert "GROUP BY" in sql.upper()
    assert "JOIN" in sql.upper()
    assert "AVG" in sql.upper()
    assert "dept_name" in sql or "department" in sql
    
    # Verify intent was correct
    assert intent["operation"] == "AGGREGATE"
    assert intent["grouping"] == "org"


def test_reports_to_sql_generation():
    """Test end-to-end SQL generation for reports to query"""
    sql, params, intent = build_query("Who reports to Anjali Gupta?")
    
    # Verify SQL structure
    assert "ILIKE" in sql.upper()
    assert "manager_name" in params
    assert params["manager_name"] == "%Anjali Gupta%"
    assert "JOIN" in sql.upper() or "LEFT JOIN" in sql.upper()
    
    # Verify intent was correct
    assert intent["reports_to"] == "Anjali Gupta"
