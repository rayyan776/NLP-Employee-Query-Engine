from typing import Dict, Any, List, Tuple


class SQLBuilder:
    
    def build_sql(self, intent: Dict[str, Any], schema: dict) -> Tuple[str, Dict[str, Any]]:
        # NEW: Handle "reports to" queries first
        if intent.get('reports_to'):
            return self._build_reports_to(intent, schema)
        
        # Window function for "Top N in each department"
        if intent.get('window_function'):
            return self._build_window_function(intent, schema)
        
        if intent['operation'] == 'COUNT':
            return self._build_count(intent, schema)
        elif intent['operation'] == 'AGGREGATE':
            return self._build_aggregate(intent, schema)
        else:
            return self._build_list(intent, schema)
    
    def _build_reports_to(self, intent: Dict, schema: dict) -> Tuple[str, Dict]:
        """NEW: Build SQL for 'Who reports to X' queries"""
        person_name = intent['reports_to']
        entity_table = intent['target_tables'][0]
        
        # Find org table
        org_table = next((t['name'] for t in schema['tables'] 
                        if t.get('semantic_tag') == 'organizational_unit'), None)
        
        if not org_table:
            # Fallback: return all employees
            return f'SELECT * FROM "{entity_table}"', {}
        
        # Find FK relationship
        fk_from, fk_to = None, None
        for rel in schema.get('relationships', []):
            if rel['from_table'] == entity_table and rel['to_table'] == org_table:
                fk_from, fk_to = rel['from_columns'][0], rel['to_columns'][0]
                break
        
        if not fk_from:
            return f'SELECT * FROM "{entity_table}"', {}
        
        # Find name column in employees table
        entity_tbl = next((t for t in schema['tables'] if t['name'] == entity_table), None)
        name_col = next((c['name'] for c in entity_tbl['columns'] 
                       if 'name' in c['name'].lower()), None) if entity_tbl else None
        
        # Find dept_name column in org table
        org_tbl = next((t for t in schema['tables'] if t['name'] == org_table), None)
        org_name_col = next((c['name'] for c in org_tbl['columns'] 
                           if c.get('semantic_tag') == 'name'), None) if org_tbl else None
        
        if not all([name_col, org_name_col]):
            return f'SELECT * FROM "{entity_table}"', {}
        
        # Build query: Find manager's department, then list employees in that department
        sql = f'''
        SELECT e.*, o."{org_name_col}" as department
        FROM "{entity_table}" e
        LEFT JOIN "{org_table}" o ON e."{fk_from}" = o."{fk_to}"
        WHERE e."{fk_from}" = (
            SELECT "{fk_from}"
            FROM "{entity_table}"
            WHERE "{name_col}" ILIKE :manager_name
            LIMIT 1
        )
        AND e."{name_col}" NOT ILIKE :manager_name
        ORDER BY e."{name_col}"
        '''
        
        return sql.strip(), {'manager_name': f'%{person_name}%'}
    
    def _build_count(self, intent: Dict, schema: dict) -> Tuple[str, Dict]:
        table = intent['target_tables'][0]
        sql = f'SELECT COUNT(*) as count FROM "{table}"'
        params = {}
        
        if intent['filters']:
            where, params = self._build_where(intent['filters'])
            sql += f' WHERE {where}'
        
        return sql, params
    
    def _build_aggregate(self, intent: Dict, schema: dict) -> Tuple[str, Dict]:
        agg = intent['aggregation']
        if not agg:
            return self._build_list(intent, schema)
        
        agg_expr = f'{agg["function"]}("{agg["column"]}")'
        if agg["function"] == "AVG":
            agg_expr = f'ROUND(CAST({agg_expr} AS NUMERIC), 2)'
        
        # WITH ORG GROUPING
        if intent['grouping'] == 'org':
            entity_table = intent['target_tables'][0]
            org_table = next((t['name'] for t in schema['tables'] 
                            if t.get('semantic_tag') == 'organizational_unit'), None)
            
            if not org_table:
                return f'SELECT {agg_expr} as average_salary FROM "{entity_table}"', {}
            
            fk_from, fk_to = None, None
            for rel in schema.get('relationships', []):
                if rel['from_table'] == entity_table and rel['to_table'] == org_table:
                    fk_from, fk_to = rel['from_columns'][0], rel['to_columns'][0]
                    break
            
            if not fk_from:
                return f'SELECT {agg_expr} as average_salary FROM "{entity_table}"', {}
            
            org_tbl = next((t for t in schema['tables'] if t['name'] == org_table), None)
            org_name_col = next((c['name'] for c in org_tbl['columns'] 
                               if c.get('semantic_tag') == 'name'), None) if org_tbl else None
            
            if not org_name_col:
                return f'SELECT {agg_expr} as average_salary FROM "{entity_table}"', {}
            
            sql = (
                f'SELECT o."{org_name_col}" as department, {agg_expr} as average_salary '
                f'FROM "{entity_table}" e '
                f'JOIN "{org_table}" o ON e."{fk_from}" = o."{fk_to}" '
                f'GROUP BY o."{org_name_col}" '
            )
            
            if intent['having']:
                sql += f'HAVING {agg_expr} {intent["having"]["operator"]} {intent["having"]["value"]} '
            
            sql += 'ORDER BY average_salary DESC'
            return sql, {}
        
        # WITH LOCATION GROUPING
        elif intent['grouping'] == 'location':
            table = intent['target_tables'][0]
            tbl_obj = next((t for t in schema['tables'] if t['name'] == table), None)
            loc_col = next((c['name'] for c in tbl_obj['columns'] 
                          if c.get('semantic_tag') == 'location'), None) if tbl_obj else None
            
            if loc_col:
                return (
                    f'SELECT "{loc_col}" as city, {agg_expr} as average_salary '
                    f'FROM "{table}" '
                    f'GROUP BY "{loc_col}" '
                    f'ORDER BY average_salary DESC'
                ), {}
        
        # WITHOUT GROUPING
        table = intent['target_tables'][0]
        return f'SELECT {agg_expr} as average_salary FROM "{table}"', {}
    
    def _build_window_function(self, intent: Dict, schema: dict) -> Tuple[str, Dict]:
        """Top N per department using ROW_NUMBER()"""
        entity_table = intent['target_tables'][0]
        org_table = next((t['name'] for t in schema['tables'] 
                        if t.get('semantic_tag') == 'organizational_unit'), None)
        
        if not org_table:
            return self._build_list(intent, schema)
        
        fk_from, fk_to = None, None
        for rel in schema.get('relationships', []):
            if rel['from_table'] == entity_table and rel['to_table'] == org_table:
                fk_from, fk_to = rel['from_columns'][0], rel['to_columns'][0]
                break
        
        if not fk_from:
            return self._build_list(intent, schema)
        
        org_tbl = next((t for t in schema['tables'] if t['name'] == org_table), None)
        org_name_col = next((c['name'] for c in org_tbl['columns'] 
                           if c.get('semantic_tag') == 'name'), None) if org_tbl else None
        
        entity_tbl = next((t for t in schema['tables'] if t['name'] == entity_table), None)
        salary_col = next((c['name'] for c in entity_tbl['columns'] 
                         if c.get('semantic_tag') == 'numeric_measure'), None) if entity_tbl else None
        
        if not all([org_name_col, salary_col]):
            return self._build_list(intent, schema)
        
        limit = intent['window_function']['limit']
        
        sql = f'''
        WITH ranked AS (
            SELECT e.*, o."{org_name_col}" as department,
                   ROW_NUMBER() OVER (PARTITION BY e."{fk_from}" ORDER BY e."{salary_col}" DESC) as rn
            FROM "{entity_table}" e
            LEFT JOIN "{org_table}" o ON e."{fk_from}" = o."{fk_to}"
        )
        SELECT * FROM ranked WHERE rn <= {limit}
        ORDER BY department, rn
        '''
        
        return sql.strip(), {}
    
    def _build_list(self, intent: Dict, schema: dict) -> Tuple[str, Dict]:
        table = intent['target_tables'][0]
        params = {}
        
        tbl_obj = next((t for t in schema['tables'] if t['name'] == table), None)
        
        if tbl_obj and tbl_obj.get('semantic_tag') == 'primary_entity':
            org_table = next((t['name'] for t in schema['tables'] 
                            if t.get('semantic_tag') == 'organizational_unit'), None)
            
            if org_table:
                fk_from, fk_to = None, None
                for rel in schema.get('relationships', []):
                    if rel['from_table'] == table and rel['to_table'] == org_table:
                        fk_from, fk_to = rel['from_columns'][0], rel['to_columns'][0]
                        break
                
                if fk_from:
                    org_tbl = next((t for t in schema['tables'] if t['name'] == org_table), None)
                    org_name_col = next((c['name'] for c in org_tbl['columns'] 
                                       if c.get('semantic_tag') == 'name'), None) if org_tbl else None
                    
                    if org_name_col:
                        sql = (
                            f'SELECT e.*, o."{org_name_col}" as department '
                            f'FROM "{table}" e '
                            f'LEFT JOIN "{org_table}" o ON e."{fk_from}" = o."{fk_to}" '
                        )
                        
                        if intent['filters']:
                            where, params = self._build_where(intent['filters'], alias='e')
                            sql += f'WHERE {where} '
                        
                        if intent['ordering']:
                            sql += f'ORDER BY e."{intent["ordering"]["column"]}" {intent["ordering"]["direction"]} '
                        
                        if intent['limit']:
                            sql += f'LIMIT {intent["limit"]}'
                        
                        return sql, params
        
        sql = f'SELECT * FROM "{table}"'
        
        if intent['filters']:
            where, params = self._build_where(intent['filters'])
            sql += f' WHERE {where}'
        
        if intent['ordering']:
            sql += f' ORDER BY "{intent["ordering"]["column"]}" {intent["ordering"]["direction"]}'
        
        if intent['limit']:
            sql += f' LIMIT {intent["limit"]}'
        
        return sql, params
    
    def _build_where(self, filters: List[Dict], alias: str = '') -> Tuple[str, Dict]:
        conditions = []
        params = {}
        prefix = f'{alias}.' if alias else ''
        
        for i, f in enumerate(filters):
            if f['operator'] == 'YEAR_EQUALS':
                if f['value'] == 'CURRENT_YEAR':
                    conditions.append(f'EXTRACT(YEAR FROM {prefix}"{f["column"]}") = EXTRACT(YEAR FROM CURRENT_DATE)')
                elif f['value'] == 'LAST_YEAR':
                    conditions.append(f'EXTRACT(YEAR FROM {prefix}"{f["column"]}") = EXTRACT(YEAR FROM CURRENT_DATE) - 1')
            else:
                param_name = f'f{i}'
                conditions.append(f'{prefix}"{f["column"]}" {f["operator"]} :{param_name}')
                params[param_name] = f['value']
        
        return ' AND '.join(conditions), params
