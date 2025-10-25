from typing import Dict, Any, List, Set
from sqlalchemy import create_engine, inspect, text
import re


class SchemaCache:
    _schema: dict | None = None
    
    @classmethod
    def get(cls):
        return cls._schema
    
    @classmethod
    def set(cls, s: dict):
        cls._schema = s


class SchemaDiscovery:
    """
    Discovers database schema dynamically WITHOUT hardcoded assumptions.
    Tags tables and columns semantically based on characteristics.
    """
    
    def analyze_database(self, connection_string: str) -> dict:
        """
        Analyze database and return schema with semantic tags
        """
        eng = create_engine(connection_string, future=True)
        insp = inspect(eng)
        schema: Dict[str, Any] = {"tables": [], "relationships": []}
        
        # Get table metadata
        for tbl in insp.get_table_names():
            cols = insp.get_columns(tbl)
            fks = insp.get_foreign_keys(tbl)
            pks = insp.get_pk_constraint(tbl)
            idx = insp.get_indexes(tbl)
            
            table_info = {
                "name": tbl,
                "columns": [{"name": c["name"], "type": str(c["type"])} for c in cols],
                "primary_key": pks.get("constrained_columns", []),
                "indexes": [{"name": i["name"], "columns": i["column_names"]} for i in idx],
            }
            
            schema["tables"].append(table_info)
            
            # Add foreign key relationships
            for fk in fks:
                schema["relationships"].append({
                    "from_table": tbl,
                    "from_columns": fk.get("constrained_columns", []),
                    "to_table": fk.get("referred_table"),
                    "to_columns": fk.get("referred_columns", []),
                })
        
        # Get sample data for inference
        samples = {}
        for t in [t["name"] for t in schema["tables"][:10]]:  # Limit to prevent slowdown
            with eng.connect() as conn:
                rows = conn.execute(text(f'SELECT * FROM "{t}" LIMIT 5')).mappings().all()
                samples[t] = [dict(r) for r in rows]
        schema["samples"] = samples
        
        # ADD SEMANTIC TAGGING (KEY ENHANCEMENT)
        schema = self._add_semantic_tags(schema)
        
        # Build vocabulary for autocomplete
        schema["alias_vocab"] = self._build_vocabulary(schema)
        
        return schema
    
    def _add_semantic_tags(self, schema: dict) -> dict:
        """
        Tag tables and columns with semantic meanings
        WITHOUT hardcoded lookups - pure inference
        """
        # Tag tables
        for table in schema["tables"]:
            table["semantic_tag"] = self._infer_table_semantic(table, schema)
        
        # Tag columns
        for table in schema["tables"]:
            for column in table["columns"]:
                column["semantic_tag"] = self._infer_column_semantic(
                    column, 
                    table, 
                    schema
                )
        
        return schema
    
    def _infer_table_semantic(self, table: dict, schema: dict) -> str:
        """
        Infer what a table represents based on structure
        Returns: 'primary_entity', 'organizational_unit', 'document_store', 'auxiliary'
        """
        table_name = table["name"].lower()
        columns = [c["name"].lower() for c in table["columns"]]
        
        # Score for primary entity (employee/person/staff)
        entity_score = 0
        entity_indicators = ['name', 'email', 'phone', 'address', 'salary', 'wage', 'pay', 
                            'hire', 'join', 'start', 'birth', 'age']
        for indicator in entity_indicators:
            if any(indicator in col for col in columns):
                entity_score += 1
        
        # Score for organizational unit (department/division)
        org_score = 0
        org_table_indicators = ['dept', 'div', 'team', 'group', 'unit', 'branch']
        org_column_indicators = ['manager', 'head', 'lead', 'director']
        if any(ind in table_name for ind in org_table_indicators):
            org_score += 3
        if any(ind in col for col in columns for ind in org_column_indicators):
            org_score += 2
        
        # Score for document store
        doc_score = 0
        doc_indicators = ['doc', 'file', 'pdf', 'content', 'text', 'upload']
        if any(ind in table_name for ind in doc_indicators):
            doc_score += 2
        if any(ind in col for col in columns for ind in doc_indicators):
            doc_score += 1
        
        # Determine semantic tag
        if entity_score >= 3 and entity_score > org_score:
            return 'primary_entity'
        elif org_score >= 3:
            return 'organizational_unit'
        elif doc_score >= 2:
            return 'document_store'
        else:
            return 'auxiliary'
    
    def _infer_column_semantic(self, column: dict, table: dict, schema: dict) -> str:
        """
        Infer what a column represents
        Returns semantic tag like: 'identifier', 'name', 'numeric_measure', 'date', 'location', etc.
        """
        col_name = column["name"].lower()
        col_type = str(column["type"]).lower()
        
        # Identifier (primary key or ID-like)
        if col_name in table.get("primary_key", []):
            return 'identifier'
        if any(x in col_name for x in ['_id', 'id_', 'code', 'key']):
            return 'identifier'
        
        # Name fields
        if any(x in col_name for x in ['name', 'title', 'label']):
            return 'name'
        
        # Numeric measures (salary, pay, amount, quantity)
        if any(x in col_type for x in ['numeric', 'decimal', 'float', 'money', 'integer']):
            if any(x in col_name for x in ['salary', 'pay', 'wage', 'compensation', 'amount', 
                                           'cost', 'price', 'total', 'sum', 'count', 'quantity']):
                return 'numeric_measure'
            return 'numeric'
        
        # Date/time fields
        if any(x in col_type for x in ['date', 'time', 'timestamp']):
            return 'date'
        
        # Location fields
        if any(x in col_name for x in ['location', 'city', 'state', 'country', 'address', 
                                       'office', 'site', 'place']):
            return 'location'
        
        # Text content
        if any(x in col_type for x in ['text', 'varchar', 'char']):
            if any(x in col_name for x in ['content', 'description', 'note', 'comment', 'text']):
                return 'text_content'
            return 'text'
        
        return 'generic'
    
    def _build_vocabulary(self, schema: dict) -> List[str]:
        """
        Build vocabulary from discovered schema for autocomplete
        """
        vocab = set()
        
        # Add table names
        for table in schema.get("tables", []):
            vocab.add(table["name"])
            vocab.add(table["name"].lower())
            
            # Add column names
            for col in table.get("columns", []):
                vocab.add(col["name"])
                vocab.add(col["name"].lower())
        
        return list(vocab)
    
    def map_natural_language_to_schema(self, query: str, schema: dict) -> dict:
        """
        Map natural language query to schema elements using semantic tags
        """
        q = query.lower()
        tokens = set(q.split())
        
        result = {"tables": [], "columns": [], "semantics": {}}
        
        # Find tables mentioned by name or semantic context
        for table in schema.get("tables", []):
            table_name_lower = table["name"].lower()
            
            # Direct name match
            if table_name_lower in q or any(tok in table_name_lower for tok in tokens):
                result["tables"].append(table["name"])
            
            # Store semantic mapping
            result["semantics"][table["name"]] = table.get("semantic_tag", "auxiliary")
        
        # Find columns mentioned
        for table in schema.get("tables", []):
            for col in table.get("columns", []):
                col_name_lower = col["name"].lower()
                if col_name_lower in q or any(tok in col_name_lower for tok in tokens):
                    result["columns"].append((table["name"], col["name"]))
        
        return result
