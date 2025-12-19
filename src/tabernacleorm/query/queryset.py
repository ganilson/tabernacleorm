"""
QuerySet implementation for TabernacleORM.
Provides Mongoose-like chainable query API.
"""

import asyncio
from typing import Any, Dict, List, Optional, Type, Union, Tuple, TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from ..models.model import Model


class QuerySet:
    """
    Lazy query builder.
    
    API inspired by Mongoose:
    await User.find({"age": {"$gt": 18}}).sort("-name").limit(10).exec()
    """
    
    def __init__(self, model: Type["Model"]):
        self.model = model
        self._query: Dict[str, Any] = {}
        self._sort: List[Tuple[str, int]] = []
        self._skip: int = 0
        self._limit: int = 0
        self._projection: Optional[List[str]] = None
        self._populate: List[Dict[str, Any]] = []
        self._lookups: List[Dict[str, Any]] = []
        self._hint: Optional[str] = None
        self._no_cache: bool = False
        self._lean: bool = False
        self._current_field: Optional[str] = None
    
    def __await__(self):
        """Allow awaiting the queryset directly (executes find)."""
        return self.exec().__await__()
    
    def filter(self, *args, **kwargs) -> "QuerySet":
        """
        Add filter conditions.
        
        Usage:
            .filter(name="John")
            .filter({"age": {"$gt": 18}})
        """
        qs = self._clone()
        
        # Handle dict arguments
        for arg in args:
            if isinstance(arg, dict):
                qs._query.update(arg)
        
        # Handle kwargs
        qs._query.update(kwargs)
        
        return qs
    
    def find(self, query: Optional[Dict[str, Any]] = None) -> "QuerySet":
        """Alias for filter/initial find."""
        return self.filter(query) if query else self._clone()
    
    def sort(self, *args) -> "QuerySet":
        """
        Add sort order.
        
        Usage:
            .sort("name")      # ASC
            .sort("-age")      # DESC
            .sort("name", "-age")
        """
        qs = self._clone()
        
        for arg in args:
            if isinstance(arg, str):
                if arg.startswith("-"):
                    qs._sort.append((arg[1:], -1))
                elif arg.startswith("+"):
                    qs._sort.append((arg[1:], 1))
                else:
                    qs._sort.append((arg, 1))
            elif isinstance(arg, dict):
                 # Handle {"name": 1, "age": -1}
                 for key, direction in arg.items():
                     qs._sort.append((key, direction))
        
        return qs
    
    def skip(self, n: int) -> "QuerySet":
        """Skip n documents."""
        qs = self._clone()
        qs._skip = n
        return qs
    
    def limit(self, n: int) -> "QuerySet":
        """Limit to n documents."""
        qs = self._clone()
        qs._limit = n
        return qs
        
    def select(self, *fields) -> "QuerySet":
        """
        Select specific fields to include.
        
        Usage:
            .select("name", "email")
            .select(["name", "email"])
        """
        qs = self._clone()
        
        flat_fields = []
        for f in fields:
            if isinstance(f, list):
                flat_fields.extend(f)
            else:
                flat_fields.append(f)
        
        qs._projection = flat_fields
        # Always include ID
        if "id" not in qs._projection:
            qs._projection.append("id")
            
        return qs
    
    def exclude(self, *fields) -> "QuerySet":
        """Exclude specific fields (not yet fully implemented in base engine)."""
        # For now, projection is inclusion-only in base engine interface
        # Implementing exclusion would require knowing all fields or engine support
        # Simplification: Only support select/inclusion via projection for v2.0
        raise NotImplementedError("exclude() not yet implemented. Use select() instead.")
    
    def populate(
        self,
        path: Union[str, Dict[str, Any]],
        select: Optional[Union[str, List[str]]] = None,
        model: Optional[str] = None,
        match: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> "QuerySet":
        """
        Populate references.
        
        Usage:
            .populate("author")
            .populate("comments", select=["content"])
            .populate({
                "path": "author",
                "select": "name email"
            })
        """
        qs = self._clone()
        
        population = {}
        if isinstance(path, dict):
            population = path
        else:
            population["path"] = path
            if select:
                population["select"] = select
            if model:
                population["model"] = model
            if match:
                population["match"] = match
            if options:
                population["options"] = options
        
        qs._populate.append(population)
        return qs
    
    def lookup(
        self,
        from_collection: str,
        local_field: str,
        foreign_field: str,
        as_field: str
    ) -> "QuerySet":
        """Add manual lookup/join."""
        qs = self._clone()
        qs._lookups.append({
            "from": from_collection,
            "localField": local_field,
            "foreignField": foreign_field,
            "as": as_field
        })
        return qs
    
    def hint(self, index_name: str) -> "QuerySet":
        """Add index hint."""
        qs = self._clone()
        qs._hint = index_name
        return qs
    
    def no_cache(self) -> "QuerySet":
        """Disable caching."""
        qs = self._clone()
        qs._no_cache = True
        return qs
    
    def where(self, *args, **kwargs) -> "QuerySet":
        """
        Chainable filter method (Mongoose-style).
        
        Usage:
            .where("age", 18)
            .where({"age": {"$gt": 18}})
            .where("age").gt(18)  # When used with comparison methods
        """
        qs = self._clone()
        
        if len(args) == 1 and isinstance(args[0], dict):
            # .where({"age": 18})
            qs._query.update(args[0])
        elif len(args) == 2:
            # .where("age", 18)
            qs._query[args[0]] = args[1]
        elif len(args) == 1 and isinstance(args[0], str):
            # .where("age") - store field for chaining with gt/lt/etc
            qs._current_field = args[0]
        elif kwargs:
            # .where(age=18)
            qs._query.update(kwargs)
        
        return qs
    
    def or_(self, conditions: List[Dict[str, Any]]) -> "QuerySet":
        """
        OR query.
        
        Usage:
            .or_([{"age": {"$gt": 18}}, {"status": "premium"}])
        """
        qs = self._clone()
        qs._query["$or"] = conditions
        return qs
    
    def and_(self, conditions: List[Dict[str, Any]]) -> "QuerySet":
        """
        AND query (explicit).
        
        Usage:
            .and_([{"age": {"$gt": 18}}, {"status": "active"}])
        """
        qs = self._clone()
        qs._query["$and"] = conditions
        return qs
    
    def nor(self, conditions: List[Dict[str, Any]]) -> "QuerySet":
        """
        NOR query (none of the conditions should be true).
        
        Usage:
            .nor([{"age": {"$lt": 18}}, {"status": "banned"}])
        """
        qs = self._clone()
        qs._query["$nor"] = conditions
        return qs
    
    def gt(self, value: Any) -> "QuerySet":
        """
        Greater than comparison.
        
        Usage:
            .where("age").gt(18)
        """
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("gt() must be used after where(field)")
        
        if field not in qs._query:
            qs._query[field] = {}
        if isinstance(qs._query[field], dict):
            qs._query[field]["$gt"] = value
        else:
            qs._query[field] = {"$gt": value}
        
        return qs
    
    def gte(self, value: Any) -> "QuerySet":
        """Greater than or equal comparison."""
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("gte() must be used after where(field)")
        
        if field not in qs._query:
            qs._query[field] = {}
        if isinstance(qs._query[field], dict):
            qs._query[field]["$gte"] = value
        else:
            qs._query[field] = {"$gte": value}
        
        return qs
    
    def lt(self, value: Any) -> "QuerySet":
        """Less than comparison."""
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("lt() must be used after where(field)")
        
        if field not in qs._query:
            qs._query[field] = {}
        if isinstance(qs._query[field], dict):
            qs._query[field]["$lt"] = value
        else:
            qs._query[field] = {"$lt": value}
        
        return qs
    
    def lte(self, value: Any) -> "QuerySet":
        """Less than or equal comparison."""
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("lte() must be used after where(field)")
        
        if field not in qs._query:
            qs._query[field] = {}
        if isinstance(qs._query[field], dict):
            qs._query[field]["$lte"] = value
        else:
            qs._query[field] = {"$lte": value}
        
        return qs
    
    def in_(self, values: List[Any]) -> "QuerySet":
        """
        IN operator (value in list).
        
        Usage:
            .where("status").in_(["active", "pending"])
        """
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("in_() must be used after where(field)")
        
        qs._query[field] = {"$in": values}
        return qs
    
    def nin(self, values: List[Any]) -> "QuerySet":
        """
        NOT IN operator (value not in list).
        
        Usage:
            .where("status").nin(["banned", "deleted"])
        """
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("nin() must be used after where(field)")
        
        qs._query[field] = {"$nin": values}
        return qs
    
    def regex(self, pattern: str, options: str = "") -> "QuerySet":
        """
        Regex pattern matching.
        
        Usage:
            .where("name").regex("^John", "i")  # Case-insensitive
        """
        qs = self._clone()
        field = getattr(qs, "_current_field", None)
        if not field:
            raise ValueError("regex() must be used after where(field)")
        
        regex_query = {"$regex": pattern}
        if options:
            regex_query["$options"] = options
        
        qs._query[field] = regex_query
        return qs
    
    def lean(self) -> "QuerySet":
        """
        Return plain dicts instead of Model instances (performance optimization).
        
        Usage:
            .find().lean().exec()  # Returns list of dicts
        """
        qs = self._clone()
        qs._lean = True
        return qs
    
    async def exists(self) -> Union[bool, Any]:
        """
        Check if any document matches the query.
        
        Returns:
            First document ID if exists, None otherwise
        """
        doc = await self.first()
        return doc.id if doc else None
    
    async def distinct(self, field: str) -> List[Any]:
        """
        Get distinct values for a field in the query results.
        
        Args:
            field: Field name
            
        Returns:
            List of distinct values
        """
        docs = await self.exec()
        values = set()
        for doc in docs:
            val = getattr(doc, field, None)
            if val is not None:
                if isinstance(val, list):
                    values.update(val)
                else:
                    values.add(val)
        return list(values)
    
    
    async def exec(self) -> List["Model"]:
        """Execute the query and return list of model instances."""
        db = self.model._get_db()
        collection = self.model.__collection__
        
        # 1. Fetch main documents
        docs = await db.findMany(
            collection,
            self._query,
            projection=self._projection,
            sort=self._sort,
            skip=self._skip,
            limit=self._limit
        )
        
        # Convert to model instances
        instances = []
        for doc in docs:
            # Handle denormalization of ID
            if "id" in doc:
                doc["id"] = db.denormalizeId(doc["id"])
            instance = self.model(**doc)
            instance._is_new = False
            instance._modified_fields.clear()
            instances.append(instance)
            
            # Run post_find hook
            await instance._run_hooks("post_find")
        
        # 2. Handle Populate (Client-Side implementation for compatibility)
        if self._populate and instances:
            await self._handle_populate(instances)
        
        return instances
    
    async def first(self) -> Optional["Model"]:
        """Execute and return first result."""
        res = await self.limit(1).exec()
        return res[0] if res else None
    
    async def count(self) -> int:
        """Count documents matching query."""
        db = self.model._get_db()
        return await db.count(self.model.__collection__, self._query)
    
    async def delete(self) -> int:
        """Delete documents matching query."""
        return await self.model.deleteMany(self._query)
    
    async def update(self, update: Dict[str, Any]) -> int:
        """Update documents matching query."""
        return await self.model.updateMany(self._query, update)
    
    async def explain(self) -> Dict[str, Any]:
        """Explain query plan."""
        db = self.model._get_db()
        return await db.explain(self.model.__collection__, self._query)
    
    async def cursor(self, batch_size: int = 100):
        """Async iterator/cursor."""
        # Simple implementation using skip/limit pagination
        # For real cursor support, engines need cursor methods
        skip = self._skip
        while True:
            # Fetch a batch
            batch = await self.model.find(self._query)\
                .sort(*self._sort_args())\
                .skip(skip)\
                .limit(batch_size)\
                .exec()
            
            if not batch:
                break
                
            for item in batch:
                yield item
            
            if len(batch) < batch_size:
                break
                
            skip += len(batch)
            
            if self._limit and skip >= self._limit:
                break
    
    def _sort_args(self) -> List[Any]:
        """Convert internal sort list to args for .sort()."""
        args = []
        for field, direction in self._sort:
            if direction == -1:
                args.append(f"-{field}")
            else:
                args.append(field)
        return args
            
    async def _handle_populate(self, instances: List["Model"]):
        """
        Handle population logic with support for:
        - Nested populations (e.g., "author.department")
        - Field selection via 'select'
        - Filtering via 'match'
        - Options (limit, sort, etc.)
        """
        if not instances:
            return
        
        for pop_spec in self._populate:
            await self._populate_field(instances, pop_spec)
    
    async def _populate_field(self, instances: List["Model"], pop_spec: Dict[str, Any]):
        """Populate a single field specification."""
        path = pop_spec["path"]
        select = pop_spec.get("select")
        match = pop_spec.get("match")
        options = pop_spec.get("options", {})
        
        # Handle nested paths (e.g., "author.department")
        if "." in path:
            await self._populate_nested(instances, pop_spec)
            return
        
        # Find the field definition to get related model
        field = self.model._fields.get(path)
        if not field or not hasattr(field, "get_related_model"):
            return
            
        related_model = field.get_related_model()
        if not related_model:
            return
        
        # Collect IDs
        ids = set()
        for instance in instances:
            val = getattr(instance, path, None)
            if val:
                # Handle both single values and lists (for array references)
                if isinstance(val, list):
                    ids.update(str(v) for v in val if v)
                else:
                    ids.add(str(val))
        
        if not ids:
            return
        
        # Build query for related documents
        query = {"id": {"$in": list(ids)}}
        
        # Apply match filter if provided
        if match:
            query.update(match)
        
        # Build QuerySet with options
        qs = related_model.find(query)
        
        # Apply select (projection)
        if select:
            if isinstance(select, str):
                select = select.split()
            qs = qs.select(*select)
        
        # Apply options (sort, limit, skip)
        if "sort" in options:
            sort_arg = options["sort"]
            if isinstance(sort_arg, str):
                qs = qs.sort(sort_arg)
            elif isinstance(sort_arg, list):
                qs = qs.sort(*sort_arg)
        
        if "limit" in options:
            qs = qs.limit(options["limit"])
        
        if "skip" in options:
            qs = qs.skip(options["skip"])
        
        # Execute query
        related_docs = await qs.exec()
        doc_map = {str(d.id): d for d in related_docs}
        
        # Assign back to instances
        for instance in instances:
            val = getattr(instance, path, None)
            if val:
                if isinstance(val, list):
                    # Populate array of references
                    populated = []
                    for v in val:
                        key = str(v)
                        if key in doc_map:
                            populated.append(doc_map[key])
                    setattr(instance, path, populated)
                else:
                    # Populate single reference
                    key = str(val)
                    if key in doc_map:
                        setattr(instance, path, doc_map[key])
    
    async def _populate_nested(self, instances: List["Model"], pop_spec: Dict[str, Any]):
        """Handle nested population (e.g., 'author.department')."""
        path = pop_spec["path"]
        parts = path.split(".", 1)
        first_field = parts[0]
        remaining_path = parts[1] if len(parts) > 1 else None
        
        # First, populate the first level
        first_spec = {
            "path": first_field,
            "select": pop_spec.get("select"),
            "match": pop_spec.get("match"),
            "options": pop_spec.get("options", {})
        }
        await self._populate_field(instances, first_spec)
        
        # If there's a remaining path, populate it on the populated instances
        if remaining_path:
            # Collect all populated instances from the first level
            nested_instances = []
            for instance in instances:
                val = getattr(instance, first_field, None)
                if val:
                    if isinstance(val, list):
                        nested_instances.extend(val)
                    else:
                        nested_instances.append(val)
            
            if nested_instances:
                # Create a temporary QuerySet for the nested model
                if nested_instances:
                    nested_model = type(nested_instances[0])
                    temp_qs = QuerySet(nested_model)
                    
                    # Populate the remaining path
                    nested_spec = {
                        "path": remaining_path,
                        "select": pop_spec.get("select"),
                        "match": pop_spec.get("match"),
                        "options": pop_spec.get("options", {})
                    }
                    await temp_qs._populate_field(nested_instances, nested_spec)

    def _clone(self) -> "QuerySet":
        """Create a copy of this queryset."""
        qs = QuerySet(self.model)
        qs._query = copy.deepcopy(self._query)
        qs._sort = copy.deepcopy(self._sort)
        qs._skip = self._skip
        qs._limit = self._limit
        qs._projection = copy.deepcopy(self._projection)
        qs._populate = copy.deepcopy(self._populate)
        qs._lookups = copy.deepcopy(self._lookups)
        qs._hint = self._hint
        qs._no_cache = self._no_cache
        qs._lean = self._lean
        qs._current_field = getattr(self, "_current_field", None)
        return qs
    
    # Utilities
    def __repr__(self) -> str:
        return f"<QuerySet {self.model.__name__}: {self._query}>"
