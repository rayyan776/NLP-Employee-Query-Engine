from typing import Dict, Any, List, Optional, Tuple
import re


class QueryParser:
    """Semantic query parser - handles all recruiter queries"""
    
    def parse_intent(self, query: str, schema: dict) -> Dict[str, Any]:
        ql = query.lower().strip()
        
        intent = {
            'operation': self._detect_operation(ql),
            'target_tables': self._identify_target_tables(ql, schema),
            'aggregation': None,
            'filters': [],
            'grouping': None,
            'having': None,
            'ordering': None,
            'limit': None,
            'window_function': None,
            'person_name': None,
            'reports_to': None
        }
        
        intent['person_name'] = self._extract_person_name(query)
        intent['reports_to'] = self._detect_reports_to(query, intent['person_name'])
        intent['aggregation'] = self._detect_aggregation(ql, schema, intent['target_tables'])
        intent['grouping'] = self._detect_grouping(ql, intent['aggregation'])
        intent['filters'] = self._detect_filters(ql, schema, intent['target_tables'])
        intent['having'] = self._detect_having(ql)
        intent['ordering'] = self._detect_ordering(ql, schema, intent['target_tables'])
        intent['limit'] = self._detect_limit(ql)
        intent['window_function'] = self._detect_window_function(ql, intent['limit'])
        
        return intent
    
    def _detect_operation(self, query: str) -> str:
        if any(kw in query for kw in ['how many', 'count', 'number of']):
            return 'COUNT'
        if any(kw in query for kw in ['average', 'avg', 'sum', 'max', 'min']):
            return 'AGGREGATE'
        return 'LIST'
    
    def _identify_target_tables(self, query: str, schema: dict) -> List[str]:
        for table in schema.get('tables', []):
            if table.get('semantic_tag') == 'primary_entity':
                return [table['name']]
        return [schema['tables'][0]['name']] if schema.get('tables') else []
    
    def _detect_aggregation(self, query: str, schema: dict, target_tables: List[str]) -> Optional[Dict]:
        func_map = {'average': 'AVG', 'avg': 'AVG', 'sum': 'SUM', 'max': 'MAX', 'min': 'MIN'}
        
        detected_func = None
        for kw, func in func_map.items():
            if kw in query:
                detected_func = func
                break
        
        if not detected_func or not target_tables:
            return None
        
        table = next((t for t in schema['tables'] if t['name'] == target_tables[0]), None)
        if not table:
            return None
        
        for col in table['columns']:
            if col.get('semantic_tag') == 'numeric_measure':
                return {'function': detected_func, 'column': col['name']}
        
        return None
    
    def _detect_grouping(self, query: str, aggregation: Optional[Dict]) -> Optional[str]:
        if not aggregation:
            return None
        
        if any(kw in query for kw in ['department', 'dept', 'division', 'by department', 'per department', 'each department', 'in each department']):
            return 'org'
        
        if any(kw in query for kw in ['city', 'location', 'by city', 'by location']):
            return 'location'
        
        return None
    
    def _detect_filters(self, query: str, schema: dict, target_tables: List[str]) -> List[Dict]:
        filters = []
        
        if not target_tables:
            return filters
        
        table = next((t for t in schema['tables'] if t['name'] == target_tables[0]), None)
        if not table:
            return filters
        
        # Numeric filters
        if any(kw in query for kw in ['over', 'above', 'exceeds', 'greater', 'more than']):
            num = self._extract_number(query)
            if num:
                col = next((c['name'] for c in table['columns'] 
                          if c.get('semantic_tag') == 'numeric_measure'), None)
                if col:
                    filters.append({'column': col, 'operator': '>', 'value': num})
        
        # Date filters
        if 'this year' in query or 'hired this year' in query or 'joined this year' in query:
            col = next((c['name'] for c in table['columns'] 
                      if c.get('semantic_tag') == 'date'), None)
            if col:
                filters.append({'column': col, 'operator': 'YEAR_EQUALS', 'value': 'CURRENT_YEAR'})
        
        if 'last year' in query:
            col = next((c['name'] for c in table['columns'] 
                      if c.get('semantic_tag') == 'date'), None)
            if col:
                filters.append({'column': col, 'operator': 'YEAR_EQUALS', 'value': 'LAST_YEAR'})
        
        return filters
    
    def _detect_having(self, query: str) -> Optional[Dict]:
        if any(kw in query for kw in ['where average', 'where avg', 'having']):
            if any(kw in query for kw in ['exceeds', 'over', 'above']):
                num = self._extract_number(query)
                if num:
                    return {'operator': '>', 'value': num}
        return None
    
    def _detect_ordering(self, query: str, schema: dict, target_tables: List[str]) -> Optional[Dict]:
        if not target_tables:
            return None
        
        table = next((t for t in schema['tables'] if t['name'] == target_tables[0]), None)
        if not table:
            return None
        
        if any(kw in query for kw in ['top', 'highest', 'largest']):
            col = next((c['name'] for c in table['columns'] 
                      if c.get('semantic_tag') == 'numeric_measure'), None)
            if col:
                return {'column': col, 'direction': 'DESC'}
        
        return None
    
    def _detect_limit(self, query: str) -> Optional[int]:
        patterns = [r'top\s+(\d+)', r'(\d+)\s+(highest|lowest|top)']
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        return None
    
    def _detect_window_function(self, query: str, limit: Optional[int]) -> Optional[Dict]:
        if any(kw in query for kw in ['in each', 'per department', 'for each department', 'each department']):
            if any(kw in query for kw in ['top', 'highest']):
                return {'type': 'ROW_NUMBER', 'partition_by': 'dept', 'limit': limit or 5}
        return None
    
    def _detect_reports_to(self, query: str, person_name: Optional[str]) -> Optional[str]:
        """Detect 'who reports to X' queries"""
        if any(kw in query for kw in ['reports to', 'reporting to', 'managed by']):
            return person_name
        return None
    
    def _extract_person_name(self, query: str) -> Optional[str]:
        """FIXED: Extract person name, skip question words"""
        # Skip question words
        skip_words = {'Who', 'What', 'Where', 'When', 'How', 'Why', 'Which'}
        
        matches = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', query)
        
        # Filter out question words
        valid_names = [m for m in matches if m not in skip_words]
        
        return valid_names[0] if valid_names else None
    
    def _extract_number(self, query: str) -> Optional[int]:
        match = re.search(r'(\d+)k?', query, re.IGNORECASE)
        if match:
            num = int(match.group(1))
            if 'k' in match.group(0).lower():
                num *= 1000
            return num
        return None
