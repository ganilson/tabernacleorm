"""
QuerySet implementation for TabernacleORM.
Provides Mongoose-like chainable query API.
"""

import asyncio
from typing import Any, Dict, List, Optional, Type, Union, Tuple, TYPE_CHECKING, Generic, TypeVar
import copy

if TYPE_CHECKING:
    from ..models.model import Model

T = TypeVar("T")

class QuerySet(Generic[T]):
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
        self._read_preference: Optional[str] = None
    
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
    
    def read_from(self, preference: str) -> "QuerySet":
        """
        Set read preference for this query.
        
        Args:
            preference: 'primary', 'secondary', 'secondaryPreferred', 'nearest'
        """
        qs = self._clone()
        qs._read_preference = preference
        return qs
    
    async def exec(self) -> List["Model"]:
        """Execute the query and return list of model instances."""
        # Get engine based on preference if specified
        if self._read_preference:
            conn = get_connection()
            if self._read_preference == 'primary':
                db = conn.get_write_engine()
            else:
                db = conn.get_read_engine()
        else:
            db = self.model.get_engine()
            
        collection = self.model.get_table_name()
        
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
            # Handle denormalization of ID
            if "id" in doc:
                doc["id"] = db.denormalizeId(doc["id"])
            instance = self.model(**doc)
            instance._persisted = True
            # instance._modified_fields.clear() # Not using dirty tracking yet
            instances.append(instance)
            
            # Run post_find hook (not currently in Model spec, skipping for now)
            # await instance._run_hooks("post_find")
        
        # 2. Handle Populate (Client-Side implementation for compatibility)
        if self._populate and instances:
            await self._handle_populate(instances)
        
        return instances

    async def all(self) -> List["Model"]:
        """Alias for exec()."""
        return await self.exec()
    
    async def first(self) -> Optional["Model"]:
        """Execute and return first result."""
        res = await self.limit(1).exec()
        return res[0] if res else None
    
    async def count(self) -> int:
        """Count documents matching query."""
        if self._read_preference:
            conn = get_connection()
            db = conn.get_write_engine() if self._read_preference == 'primary' else conn.get_read_engine()
        else:
            db = self.model.get_engine()
        return await db.count(self.model.get_table_name(), self._query)
    
    async def delete(self) -> int:
        """Delete documents matching query."""
        return await self.model.deleteMany(self._query)
    
    async def update(self, update: Dict[str, Any]) -> int:
        """Update documents matching query."""
        return await self.model.updateMany(self._query, update)
    
    async def explain(self) -> Dict[str, Any]:
        """Explain query plan."""
        db = self.model.get_engine()
        return await db.explain(self.model.get_table_name(), self._query)
    
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
        meta = self.model._tabernacle_meta
        
        for pop_spec in self._populate:
            path = pop_spec["path"]
            
            # --- Case 1: Relationship Field (OneToMany, OneToOne, etc.) ---
            if path in meta["relationships"]:
                rel = meta["relationships"][path]
                target_model_name = rel.link_model
                
                try:
                    if isinstance(target_model_name, type):
                        related_model = target_model_name
                    else:
                        related_model = self.model._resolve_model(target_model_name)
                        
                    # 1a. OneToMany (Reverse)
                    # We are Parent, we want Children where child.fk == parent.id
                    if rel.type == "OneToMany":
                        # Collect Parent IDs
                        parent_ids = [inst.id for inst in instances if inst.id is not None]
                        if not parent_ids: continue
                        
                        # Find children where reverse_field (back_populates?) IN parent_ids
                        # rel object doesn't have back_populates explicitly stored in 'relationships' dict 
                        # usually, but let's assume 'fields' logic handles it.
                        # Wait, 'OneToMany' in fields.py stores arguments.
                        # We need the foreign key field name on the CHILD model.
                        
                        # Convention or explicit config needed?
                        # Usually OneToMany("Post", back_populates="author_id")
                        fk_field_on_child = getattr(rel, "back_populates", None)
                        
                        if not fk_field_on_child:
                            # Fallback: try to guess "parent_model_id" or "parent_model"
                            # We can check registered columns on the related_model
                            target_meta = getattr(related_model, "_tabernacle_meta", {})
                            model_name = self.model.__name__.lower()
                            
                            # Possible FK names: 'user_id', 'author_id', etc.
                            possible_fks = [f"{model_name}_id", model_name]
                            
                            # Inspect columns for foreign key match
                            for col_name, col_args in target_meta.get("columns", {}).items():
                                if col_args.get("foreign_key") == self.model.__name__:
                                    fk_field_on_child = col_name
                                    break
                            
                            if not fk_field_on_child:
                                for candidate in possible_fks:
                                    if candidate in target_meta.get("columns", {}):
                                        fk_field_on_child = candidate
                                        break
                        
                        if not fk_field_on_child:
                            continue

                        # Fetch all related children
                        children = await related_model.find({
                            fk_field_on_child: {"$in": parent_ids}
                        }).exec()
                        
                        # Map children to parents
                        children_map = {} # parent_id -> [child1, child2]
                        for child in children:
                            p_id = getattr(child, fk_field_on_child)
                            # Handle object or ID
                            if hasattr(p_id, "id"): p_id = p_id.id
                            
                            p_id_str = str(p_id)
                            if p_id_str not in children_map:
                                children_map[p_id_str] = []
                            children_map[p_id_str].append(child)
                            
                        # Assign to instances
                        for instance in instances:
                             key = str(instance.id)
                             if key in children_map:
                                 setattr(instance, path, children_map[key])
                             else:
                                 setattr(instance, path, [])
                                 
                    # 1b. OneToOne / ManyToMany (Future)
                    pass
                except Exception:
                    continue

            # --- Case 2: Foreign Key Column (BelongsTo) ---
            elif path in meta["columns"]:
                 col_args = meta["columns"][path]
                 if col_args.get("foreign_key"):
                     target_model_name = col_args["foreign_key"]
                     try:
                        if isinstance(target_model_name, type):
                            related_model = target_model_name
                        else:
                            related_model = self.model._resolve_model(target_model_name)
                     except Exception:
                         continue
                     
                     # Collect IDs
                     ids = set()
                     for instance in instances:
                         val = getattr(instance, path, None)
                         if val:
                             if isinstance(val, related_model): continue
                             ids.add(val)
                     
                     if not ids: continue
                     
                     related_docs = await related_model.find({"id": {"$in": list(ids)}}).exec()
                     doc_map = {str(d.id): d for d in related_docs}
                     
                     for instance in instances:
                         val = getattr(instance, path, None)
                         if val:
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
