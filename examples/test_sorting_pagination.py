"""
Test Sorting and Pagination
Demonstrates various sorting techniques and pagination strategies
"""

import asyncio
from tabernacleorm import connect, Model, fields


class Article(Model):
    title = fields.StringField(required=True)
    author = fields.StringField(required=True)
    views = fields.IntegerField(default=0)
    likes = fields.IntegerField(default=0)
    published_date = fields.DateTimeField(auto_now_add=True)
    category = fields.StringField()
    
    class Meta:
        collection = "articles"


async def main():
    print("=" * 60)
    print("TabernacleORM - Sorting and Pagination Test")
    print("=" * 60)
    
    # Connect
    db = connect("sqlite:///test_sorting.db")
    await db.connect()
    
    # Create table
    print("\n📦 Creating table...")
    await Article.createTable()
    
    # Create test data
    print("\n📝 Creating test articles...")
    await Article.create(title="Python Basics", author="Alice", views=1500, likes=120, category="Programming")
    await Article.create(title="JavaScript Guide", author="Bob", views=2300, likes=180, category="Programming")
    await Article.create(title="Data Science 101", author="Alice", views=3200, likes=250, category="Data Science")
    await Article.create(title="Machine Learning", author="Charlie", views=4100, likes=320, category="Data Science")
    await Article.create(title="Web Development", author="Bob", views=1800, likes=95, category="Programming")
    await Article.create(title="AI Fundamentals", author="Alice", views=2900, likes=210, category="AI")
    await Article.create(title="React Tutorial", author="David", views=2100, likes=165, category="Programming")
    await Article.create(title="Django REST API", author="Charlie", views=1600, likes=140, category="Programming")
    await Article.create(title="Neural Networks", author="Alice", views=3500, likes=280, category="AI")
    await Article.create(title="Cloud Computing", author="Bob", views=2700, likes=190, category="Cloud")
    
    print("✅ Test data created!")
    
    # Test 1: Sort by single field (ascending)
    print("\n" + "=" * 60)
    print("Test 1: Sort by views (ascending)")
    print("=" * 60)
    articles = await Article.find().sort("views").limit(5).exec()
    for article in articles:
        print(f"📰 {article.title}: {article.views} views")
    
    # Test 2: Sort by single field (descending)
    print("\n" + "=" * 60)
    print("Test 2: Sort by views (descending)")
    print("=" * 60)
    articles = await Article.find().sort("-views").limit(5).exec()
    for article in articles:
        print(f"📰 {article.title}: {article.views} views")
    
    # Test 3: Sort by multiple fields
    print("\n" + "=" * 60)
    print("Test 3: Sort by category (asc), then views (desc)")
    print("=" * 60)
    articles = await Article.find().sort("category", "-views").exec()
    for article in articles:
        print(f"📰 [{article.category}] {article.title}: {article.views} views")
    
    # Test 4: Pagination - Page 1
    print("\n" + "=" * 60)
    print("Test 4: Pagination - Page 1 (3 items per page)")
    print("=" * 60)
    page_size = 3
    page_1 = await Article.find().sort("-views").limit(page_size).exec()
    for i, article in enumerate(page_1, 1):
        print(f"{i}. {article.title}: {article.views} views")
    
    # Test 5: Pagination - Page 2
    print("\n" + "=" * 60)
    print("Test 5: Pagination - Page 2")
    print("=" * 60)
    page_2 = await Article.find().sort("-views").skip(page_size).limit(page_size).exec()
    for i, article in enumerate(page_2, page_size + 1):
        print(f"{i}. {article.title}: {article.views} views")
    
    # Test 6: Pagination - Page 3
    print("\n" + "=" * 60)
    print("Test 6: Pagination - Page 3")
    print("=" * 60)
    page_3 = await Article.find().sort("-views").skip(page_size * 2).limit(page_size).exec()
    for i, article in enumerate(page_3, page_size * 2 + 1):
        print(f"{i}. {article.title}: {article.views} views")
    
    # Test 7: Top N by category
    print("\n" + "=" * 60)
    print("Test 7: Top 2 articles per category")
    print("=" * 60)
    categories = await Article.distinct("category")
    for category in categories:
        print(f"\n📂 {category}:")
        articles = await Article.find({"category": category}).sort("-views").limit(2).exec()
        for article in articles:
            print(f"   📰 {article.title}: {article.views} views")
    
    # Test 8: Sort by likes-to-views ratio
    print("\n" + "=" * 60)
    print("Test 8: Articles with best engagement (likes/views ratio)")
    print("=" * 60)
    all_articles = await Article.findMany()
    # Calculate ratio and sort in Python
    articles_with_ratio = [(a, a.likes / a.views if a.views > 0 else 0) for a in all_articles]
    articles_with_ratio.sort(key=lambda x: x[1], reverse=True)
    
    for article, ratio in articles_with_ratio[:5]:
        print(f"📰 {article.title}: {ratio:.2%} engagement ({article.likes} likes / {article.views} views)")
    
    # Test 9: Pagination info
    print("\n" + "=" * 60)
    print("Test 9: Pagination Information")
    print("=" * 60)
    total_count = await Article.count()
    page_size = 4
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    
    print(f"Total articles: {total_count}")
    print(f"Page size: {page_size}")
    print(f"Total pages: {total_pages}")
    
    for page_num in range(1, total_pages + 1):
        skip = (page_num - 1) * page_size
        articles = await Article.find().sort("-views").skip(skip).limit(page_size).exec()
        print(f"\nPage {page_num}: {len(articles)} articles")
        for article in articles:
            print(f"  - {article.title}")
    
    # Test 10: Cursor-based pagination simulation
    print("\n" + "=" * 60)
    print("Test 10: Cursor-based Pagination (using ID)")
    print("=" * 60)
    
    # First page
    first_page = await Article.find().sort("id").limit(3).exec()
    print("First page:")
    for article in first_page:
        print(f"  📰 {article.title} (ID: {article.id})")
    
    if first_page:
        last_id = first_page[-1].id
        # Next page (articles with ID > last_id)
        next_page = await Article.find({"id": {"$gt": last_id}}).sort("id").limit(3).exec()
        print("\nNext page (ID > {})".format(last_id))
        for article in next_page:
            print(f"  📰 {article.title} (ID: {article.id})")
    
    print("\n" + "=" * 60)
    print("✅ All sorting and pagination tests completed!")
    print("=" * 60)
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
