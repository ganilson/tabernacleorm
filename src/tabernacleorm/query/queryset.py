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
        """Handle population logic."""
        # This is a complex topic usually. Simplified version:
        # Collect IDs for each populated field
        # Fetch related documents
        # Assign to instances
        
        for pop_spec in self._populate:
            path = pop_spec["path"]
            
            # Find the field definition to get related model
            field = self.model._fields.get(path)
            if not field or not hasattr(field, "get_related_model"):
                continue
                
            related_model = field.get_related_model()
            if not related_model:
                continue
            
            # Collect IDs
            ids = set()
            for instance in instances:
                val = getattr(instance, path, None)
                if val:
                    ids.add(val)
            
            if not ids:
                continue
            
            # Fetch related docs
            # TODO: Support 'select', 'match', etc. from pop_spec
            related_docs = await related_model.find({"id": {"$in": list(ids)}}).exec()
            doc_map = {str(d.id): d for d in related_docs}
            
            # Assign back
            for instance in instances:
                val = getattr(instance, path, None)
                if val:
                    # Check matching types (str vs UUID vs ObjectId etc) is tricky
                    # Assuming str conversion for mapping
                    key = str(val)
                    if key in doc_map:
                        setattr(instance, path, doc_map[key])

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
        return qs
    
    # Utilities
    def __repr__(self) -> str:
        return f"<QuerySet {self.model.__name__}: {self._query}>"
