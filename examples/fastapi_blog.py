"""
FastAPI Example 2: Blog API
Demonstrates: nested populate, complex relationships, full-text search
"""

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tabernacleorm import connect, Model, fields


# Models
class Author(Model):
    username = fields.StringField(required=True, unique=True)
    email = fields.StringField(required=True, unique=True)
    bio = fields.StringField()
    avatar_url = fields.StringField()
    followers_count = fields.IntegerField(default=0)
    posts_count = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "authors"


class Tag(Model):
    name = fields.StringField(required=True, unique=True)
    slug = fields.StringField(required=True, unique=True)
    posts_count = fields.IntegerField(default=0)
    
    class Meta:
        collection = "tags"


class Post(Model):
    title = fields.StringField(required=True)
    slug = fields.StringField(required=True, unique=True)
    content = fields.StringField(required=True)
    excerpt = fields.StringField()
    author_id = fields.ForeignKey(Author, required=True)
    tags = fields.JSONField()  # List of tag IDs
    status = fields.StringField(default="draft")  # draft, published
    views = fields.IntegerField(default=0)
    likes = fields.IntegerField(default=0)
    comments_count = fields.IntegerField(default=0)
    published_at = fields.DateTimeField(nullable=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(nullable=True)
    
    class Meta:
        collection = "posts"


class Comment(Model):
    post_id = fields.ForeignKey(Post, required=True)
    author_id = fields.ForeignKey(Author, required=True)
    content = fields.StringField(required=True)
    parent_id = fields.ForeignKey("Comment", nullable=True)  # For nested comments
    likes = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "comments"


class Follow(Model):
    follower_id = fields.ForeignKey(Author, required=True)
    following_id = fields.ForeignKey(Author, required=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "follows"


# Pydantic Schemas
class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    author_id: str
    tags: List[str] = []
    status: str = "draft"


class CommentCreate(BaseModel):
    post_id: str
    author_id: str
    content: str
    parent_id: Optional[str] = None


# FastAPI App
app = FastAPI(title="Blog API", version="1.0.0")


@app.on_event("startup")
async def startup():
    db = connect("sqlite:///blog.db")
    await db.connect()
    
    await Author.createTable()
    await Tag.createTable()
    await Post.createTable()
    await Comment.createTable()
    await Follow.createTable()
    
    print("Blog API ready")


# Post Endpoints
@app.post("/posts")
async def create_post(post: PostCreate):
    """Create a new blog post"""
    # Generate slug
    slug = post.title.lower().replace(" ", "-").replace("'", "")
    
    # Create post
    new_post = await Post.create(
        title=post.title,
        slug=slug,
        content=post.content,
        excerpt=post.excerpt or post.content[:200],
        author_id=post.author_id,
        tags=post.tags,
        status=post.status,
        published_at=datetime.now() if post.status == "published" else None
    )
    
    # Update author posts count
    author = await Author.findById(post.author_id)
    author.posts_count += 1
    await author.save()
    
    return {"id": str(new_post.id), "slug": new_post.slug}


@app.get("/posts")
async def list_posts(
    status: str = "published",
    author_id: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "-published_at",
    limit: int = 20,
    skip: int = 0
):
    """
    List posts with complex filtering and populate
    """
    query = {"status": status}
    
    if author_id:
        query["author_id"] = author_id
    
    # Build query
    qs = Post.find(query).sort(sort).skip(skip).limit(limit)
    
    # Execute with populate
    posts = await qs.populate("author_id", select=["username", "avatar_url"]).exec()
    
    result = []
    for p in posts:
        post_dict = {
            "id": str(p.id),
            "title": p.title,
            "slug": p.slug,
            "excerpt": p.excerpt,
            "views": p.views,
            "likes": p.likes,
            "comments_count": p.comments_count,
            "published_at": str(p.published_at) if p.published_at else None
        }
        
        if hasattr(p.author_id, 'username'):
            post_dict["author"] = {
                "username": p.author_id.username,
                "avatar_url": p.author_id.avatar_url
            }
        
        result.append(post_dict)
    
    return result


@app.get("/posts/{slug}")
async def get_post(slug: str):
    """
    Get post with full details, populated author, and comments
    """
    post = await Post.findOne({"slug": slug})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment views
    post.views += 1
    await post.save()
    
    # Populate author
    author = await Author.findById(post.author_id)
    
    # Get comments with nested structure
    comments = await Comment.find({"post_id": post.id, "parent_id": None}).sort("-created_at").populate("author_id").exec()
    
    # Get replies for each comment
    comments_with_replies = []
    for comment in comments:
        replies = await Comment.find({"parent_id": comment.id}).populate("author_id").exec()
        
        comments_with_replies.append({
            "id": str(comment.id),
            "content": comment.content,
            "likes": comment.likes,
            "created_at": str(comment.created_at),
            "author": comment.author_id.username if hasattr(comment.author_id, 'username') else None,
            "replies": [
                {
                    "id": str(r.id),
                    "content": r.content,
                    "likes": r.likes,
                    "author": r.author_id.username if hasattr(r.author_id, 'username') else None,
                    "created_at": str(r.created_at)
                }
                for r in replies
            ]
        })
    
    return {
        "id": str(post.id),
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "views": post.views,
        "likes": post.likes,
        "published_at": str(post.published_at) if post.published_at else None,
        "author": {
            "username": author.username,
            "bio": author.bio,
            "avatar_url": author.avatar_url,
            "followers_count": author.followers_count
        } if author else None,
        "comments": comments_with_replies
    }


@app.post("/comments")
async def create_comment(comment: CommentCreate):
    """Create a comment or reply"""
    new_comment = await Comment.create(**comment.dict())
    
    # Update post comments count
    post = await Post.findById(comment.post_id)
    post.comments_count += 1
    await post.save()
    
    return {"id": str(new_comment.id)}


@app.post("/posts/{post_id}/like")
async def like_post(post_id: str):
    """Like a post"""
    post = await Post.findById(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.likes += 1
    await post.save()
    
    return {"likes": post.likes}


# Author Endpoints
@app.get("/authors/{username}")
async def get_author(username: str):
    """Get author profile with recent posts"""
    author = await Author.findOne({"username": username})
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Get recent posts
    posts = await Post.find({"author_id": author.id, "status": "published"}).sort("-published_at").limit(10).exec()
    
    return {
        "username": author.username,
        "bio": author.bio,
        "avatar_url": author.avatar_url,
        "followers_count": author.followers_count,
        "posts_count": author.posts_count,
        "recent_posts": [
            {
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "views": p.views,
                "likes": p.likes
            }
            for p in posts
        ]
    }


@app.post("/authors/{author_id}/follow")
async def follow_author(author_id: str, follower_id: str):
    """Follow an author"""
    # Check if already following
    existing = await Follow.findOne({"follower_id": follower_id, "following_id": author_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already following")
    
    # Create follow
    await Follow.create(follower_id=follower_id, following_id=author_id)
    
    # Update followers count
    author = await Author.findById(author_id)
    author.followers_count += 1
    await author.save()
    
    return {"message": "Following"}


@app.get("/feed/{author_id}")
async def get_feed(author_id: str, limit: int = 20):
    """Get personalized feed from followed authors"""
    # Get followed authors
    follows = await Follow.find({"follower_id": author_id}).exec()
    following_ids = [f.following_id for f in follows]
    
    if not following_ids:
        return []
    
    # Get posts from followed authors
    posts = await Post.find().where("author_id").in_(following_ids).where("status", "published").sort("-published_at").limit(limit).populate("author_id").exec()
    
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "slug": p.slug,
            "excerpt": p.excerpt,
            "author": p.author_id.username if hasattr(p.author_id, 'username') else None,
            "published_at": str(p.published_at)
        }
        for p in posts
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
