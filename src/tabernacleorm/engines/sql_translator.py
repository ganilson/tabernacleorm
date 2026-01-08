from typing import Any, Dict, List, Tuple

def build_where_clause(query: Dict[str, Any], dialect: str = "sqlite") -> Tuple[str, List[Any]]:
    """
    Convert MongoDB-style query dict to SQL WHERE clause and parameters.
    
    Supported operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin.
    
    Returns: (where_conditions, params)
    Note: Does NOT include " WHERE " prefix - caller should add it
    """
    if not query:
        return "", []

    clauses = []
    params = []

    for key, value in query.items():
        if key.startswith("$"):
            # Handle top-level operators like $or, $and (if needed later)
            continue
            
        # Treat 'id' as 'id' (assuming SQL table has 'id' standard column)
        # Engines usually denormalize _id to id.
        
        if isinstance(value, dict):
            # Complex Operator: {"age": {"$gt": 18}}
            for op, op_val in value.items():
                if op == "$eq":
                    clauses.append(f"{key} = ?")
                    params.append(op_val)
                elif op == "$ne":
                    clauses.append(f"{key} != ?")
                    params.append(op_val)
                elif op == "$gt":
                    clauses.append(f"{key} > ?")
                    params.append(op_val)
                elif op == "$gte":
                    clauses.append(f"{key} >= ?")
                    params.append(op_val)
                elif op == "$lt":
                    clauses.append(f"{key} < ?")
                    params.append(op_val)
                elif op == "$lte":
                    clauses.append(f"{key} <= ?")
                    params.append(op_val)
                elif op == "$in":
                    if not op_val:
                        clauses.append("1=0") # Empty IN is always false
                    else:
                        placeholders = ", ".join(["?"] * len(op_val))
                        clauses.append(f"{key} IN ({placeholders})")
                        params.extend(op_val)
                elif op == "$nin":
                    if not op_val:
                         pass # Not IN empty set is always true? OR simply ignore?
                    else:
                        placeholders = ", ".join(["?"] * len(op_val))
                        clauses.append(f"{key} NOT IN ({placeholders})")
                        params.extend(op_val)
        else:
            # Simple Equality: {"name": "John"}
            clauses.append(f"{key} = ?")
            params.append(value)
            
    if not clauses:
        return "", []
        
    # Return conditions WITHOUT " WHERE " prefix
    conditions = " AND ".join(clauses)
    
    return conditions, params
