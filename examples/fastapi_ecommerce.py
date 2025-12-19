"""
FastAPI Example 1: E-commerce API
Complex models with products, categories, orders, and users
Demonstrates: populate, complex queries, aggregations
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from tabernacleorm import connect, Model, fields


# Models
class Category(Model):
    name = fields.StringField(required=True, unique=True)
    description = fields.StringField()
    parent_id = fields.ForeignKey("Category", nullable=True)
    
    class Meta:
        collection = "categories"


class Product(Model):
    name = fields.StringField(required=True)
    description = fields.StringField()
    price = fields.FloatField(required=True)
    stock = fields.IntegerField(default=0)
    category_id = fields.ForeignKey(Category)
    tags = fields.JSONField()
    rating = fields.FloatField(default=0.0)
    reviews_count = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "products"


class User(Model):
    username = fields.StringField(required=True, unique=True)
    email = fields.StringField(required=True, unique=True)
    full_name = fields.StringField()
    address = fields.JSONField()
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "users"


class Order(Model):
    user_id = fields.ForeignKey(User, required=True)
    items = fields.JSONField()  # [{product_id, quantity, price}]
    total = fields.FloatField(required=True)
    status = fields.StringField(default="pending")
    shipping_address = fields.JSONField()
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "orders"


class Review(Model):
    product_id = fields.ForeignKey(Product, required=True)
    user_id = fields.ForeignKey(User, required=True)
    rating = fields.IntegerField(required=True)
    comment = fields.StringField()
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "reviews"


# Pydantic Schemas
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category_id: str
    tags: Optional[List[str]] = []


class OrderCreate(BaseModel):
    user_id: str
    items: List[dict]
    shipping_address: dict


class ReviewCreate(BaseModel):
    product_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# FastAPI App
app = FastAPI(title="E-commerce API", version="1.0.0")


@app.on_event("startup")
async def startup():
    db = connect("sqlite:///ecommerce.db")
    await db.connect()
    
    # Create tables
    await Category.createTable()
    await Product.createTable()
    await User.createTable()
    await Order.createTable()
    await Review.createTable()
    
    print("Database connected and tables created")


@app.on_event("shutdown")
async def shutdown():
    pass


# Category Endpoints
@app.post("/categories")
async def create_category(category: CategoryCreate):
    new_cat = await Category.create(**category.dict())
    return {"id": str(new_cat.id), "name": new_cat.name}


@app.get("/categories")
async def list_categories(parent_id: Optional[str] = None):
    if parent_id:
        categories = await Category.find({"parent_id": parent_id}).exec()
    else:
        categories = await Category.find({"parent_id": None}).exec()
    
    return [{"id": str(c.id), "name": c.name, "description": c.description} for c in categories]


# Product Endpoints
@app.post("/products")
async def create_product(product: ProductCreate):
    new_product = await Product.create(**product.dict())
    return {"id": str(new_product.id), "name": new_product.name}


@app.get("/products")
async def list_products(
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "-created_at",
    limit: int = 20,
    skip: int = 0
):
    """
    Complex query with multiple filters, sorting, and pagination
    """
    query = {}
    
    if category_id:
        query["category_id"] = category_id
    
    if min_price is not None or max_price is not None:
        price_query = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        query["price"] = price_query
    
    # Build query
    qs = Product.find(query).sort(sort_by).skip(skip).limit(limit)
    
    # Execute with populate
    products = await qs.populate("category_id").exec()
    
    result = []
    for p in products:
        product_dict = {
            "id": str(p.id),
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "rating": p.rating,
            "reviews_count": p.reviews_count
        }
        
        if hasattr(p.category_id, 'name'):
            product_dict["category"] = {
                "id": str(p.category_id.id),
                "name": p.category_id.name
            }
        
        result.append(product_dict)
    
    return result


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get product with populated category and recent reviews"""
    product = await Product.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Populate category
    category = await Category.findById(product.category_id)
    
    # Get recent reviews with user info
    reviews = await Review.find({"product_id": product_id}).sort("-created_at").limit(5).populate("user_id").exec()
    
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "rating": product.rating,
        "reviews_count": product.reviews_count,
        "category": {"id": str(category.id), "name": category.name} if category else None,
        "recent_reviews": [
            {
                "rating": r.rating,
                "comment": r.comment,
                "user": r.user_id.username if hasattr(r.user_id, 'username') else None,
                "created_at": str(r.created_at)
            }
            for r in reviews
        ]
    }


# Order Endpoints
@app.post("/orders")
async def create_order(order: OrderCreate):
    """Create order with automatic total calculation"""
    # Calculate total
    total = 0.0
    for item in order.items:
        product = await Product.findById(item["product_id"])
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
        
        if product.stock < item["quantity"]:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
        
        total += product.price * item["quantity"]
    
    # Create order
    new_order = await Order.create(
        user_id=order.user_id,
        items=order.items,
        total=total,
        shipping_address=order.shipping_address
    )
    
    # Update product stock
    for item in order.items:
        product = await Product.findById(item["product_id"])
        product.stock -= item["quantity"]
        await product.save()
    
    return {"id": str(new_order.id), "total": total, "status": new_order.status}


@app.get("/orders")
async def list_orders(user_id: Optional[str] = None, status: Optional[str] = None):
    """List orders with populated user and product info"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    
    orders = await Order.find(query).sort("-created_at").populate("user_id").exec()
    
    result = []
    for order in orders:
        order_dict = {
            "id": str(order.id),
            "total": order.total,
            "status": order.status,
            "created_at": str(order.created_at),
            "user": order.user_id.username if hasattr(order.user_id, 'username') else None
        }
        result.append(order_dict)
    
    return result


# Review Endpoints
@app.post("/reviews")
async def create_review(review: ReviewCreate):
    """Create review and update product rating"""
    # Check if user already reviewed
    existing = await Review.findOne({"product_id": review.product_id, "user_id": review.user_id})
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this product")
    
    # Create review
    new_review = await Review.create(**review.dict())
    
    # Update product rating
    product = await Product.findById(review.product_id)
    all_reviews = await Review.find({"product_id": review.product_id}).exec()
    
    total_rating = sum(r.rating for r in all_reviews)
    product.rating = total_rating / len(all_reviews)
    product.reviews_count = len(all_reviews)
    await product.save()
    
    return {"id": str(new_review.id), "rating": new_review.rating}


# Analytics Endpoints
@app.get("/analytics/top-products")
async def get_top_products(limit: int = 10):
    """Get top-rated products"""
    products = await Product.find().where("reviews_count").gt(0).sort("-rating").limit(limit).populate("category_id").exec()
    
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "rating": p.rating,
            "reviews_count": p.reviews_count,
            "category": p.category_id.name if hasattr(p.category_id, 'name') else None
        }
        for p in products
    ]


@app.get("/analytics/category-stats")
async def get_category_stats():
    """Get product count and average price per category"""
    categories = await Category.findMany()
    
    stats = []
    for category in categories:
        products = await Product.find({"category_id": category.id}).exec()
        
        if products:
            avg_price = sum(p.price for p in products) / len(products)
            stats.append({
                "category": category.name,
                "product_count": len(products),
                "average_price": round(avg_price, 2),
                "total_stock": sum(p.stock for p in products)
            })
    
    return sorted(stats, key=lambda x: x["product_count"], reverse=True)


@app.get("/analytics/user-orders")
async def get_user_order_stats(user_id: str):
    """Get user order statistics"""
    orders = await Order.find({"user_id": user_id}).exec()
    
    if not orders:
        return {"total_orders": 0, "total_spent": 0.0}
    
    return {
        "total_orders": len(orders),
        "total_spent": sum(o.total for o in orders),
        "average_order": sum(o.total for o in orders) / len(orders),
        "status_breakdown": {
            "pending": len([o for o in orders if o.status == "pending"]),
            "completed": len([o for o in orders if o.status == "completed"]),
            "cancelled": len([o for o in orders if o.status == "cancelled"])
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
