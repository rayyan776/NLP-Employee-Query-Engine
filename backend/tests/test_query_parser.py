import pytest
from services.query_parser import QueryParser

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


def test_detect_count():
    """Test COUNT operation detection"""
    p = QueryParser()
    intent = p.parse_intent("How many employees do we have?", mock_schema)
    assert intent["operation"] == "COUNT"
    assert intent["target_tables"] == ["employees"]


def test_detect_group_avg_by_dept():
    """Test grouped aggregation by department"""
    p = QueryParser()
    intent = p.parse_intent("Average salary by department", mock_schema)
    assert intent["operation"] == "AGGREGATE"
    assert intent["grouping"] == "org"
    assert intent["aggregation"]["function"] == "AVG"
    assert intent["aggregation"]["column"] == "annual_salary"


def test_detect_salary_filter():
    """Test numeric filter detection"""
    p = QueryParser()
    intent = p.parse_intent("Employees with salary over 120000", mock_schema)
    assert intent["operation"] == "LIST"
    assert len(intent["filters"]) > 0
    assert intent["filters"][0]["operator"] == ">"
    assert intent["filters"][0]["value"] == 120000


def test_detect_window_top_each_dept():
    """Test window function for top N per department"""
    p = QueryParser()
    intent = p.parse_intent("Top 5 highest paid employees in each department", mock_schema)
    assert intent["window_function"] is not None
    assert intent["window_function"]["type"] == "ROW_NUMBER"
    assert intent["window_function"]["limit"] == 5


def test_detect_reports_to():
    """Test reports to relationship detection"""
    p = QueryParser()
    intent = p.parse_intent("Who reports to Anjali Gupta?", mock_schema)
    assert intent["reports_to"] == "Anjali Gupta"
    assert intent["person_name"] == "Anjali Gupta"
