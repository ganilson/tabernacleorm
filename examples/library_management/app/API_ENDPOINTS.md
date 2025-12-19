# Library Management System - API Endpoints

## Tabernacle ORM Query Demonstrations

Este documento lista todos os endpoints disponíveis e o que cada um demonstra do TabernacleORM.

---

## 📚 BOOKS ENDPOINTS

### 1. GET /api/books/
**Descrição:** Get all books with pagination and populated author/category
```
- Query: skip=0, limit=20
- Features: populate("author_id"), populate("category_id"), skip(), limit(), sort()
```
**Exemplo:**
```bash
curl http://localhost:8000/api/books/?skip=0&limit=10
```

### 2. GET /api/books/available
**Descrição:** Get only available books (copies > 0) using where() query
```
- Features: where("available_copies").gt(0), populate()
```
**Exemplo:**
```bash
curl http://localhost:8000/api/books/available?skip=0&limit=10
```

### 3. GET /api/books/search?q=python
**Descrição:** Search books by title or description (regex search)
```
- Features: find({$regex}), populate(), $options: "i" (case insensitive)
```
**Exemplo:**
```bash
curl http://localhost:8000/api/books/search?q=python&skip=0&limit=10
```

### 4. GET /api/books/author/{author_id}
**Descrição:** Get books by specific author with populated author data
```
- Features: find({author_id}), populate("author_id"), skip(), limit()
```
**Exemplo:**
```bash
curl http://localhost:8000/api/books/author/507f1f77bcf86cd799439011
```

### 5. GET /api/books/category/{category_id}
**Descrição:** Get books by category with populate
```
- Features: find({category_id}), populate("category_id"), skip(), limit()
```
**Exemplo:**
```bash
curl http://localhost:8000/api/books/category/507f1f77bcf86cd799439012
```

### 6. GET /api/books/{book_id}
**Descrição:** Get specific book with populated relationships (author & category)
```
- Features: findOne(), populate("author_id"), populate("category_id")
```
**Exemplo:**
```bash
curl http://localhost:8000/api/books/507f1f77bcf86cd799439013
```

### 7. POST /api/books/
**Descrição:** Create new book (librarian only)
```json
{
  "title": "The Great Gatsby",
  "isbn": "978-0743273565",
  "author_id": "507f1f77bcf86cd799439011",
  "category_id": "507f1f77bcf86cd799439012",
  "description": "A classic novel",
  "available_copies": 5,
  "total_copies": 5
}
```
**Features:** create()

### 8. PUT /api/books/{book_id}
**Descrição:** Update book using findOneAndUpdate (admin only)
```json
{
  "title": "Updated Title",
  "available_copies": 3
}
```
**Features:** findOneAndUpdate(), new=True, $set operator

### 9. DELETE /api/books/{book_id}
**Descrição:** Delete book using findOneAndDelete (admin only)
```
- Features: findOneAndDelete()
```
**Exemplo:**
```bash
curl -X DELETE http://localhost:8000/api/books/507f1f77bcf86cd799439013
```

---

## 📕 LOANS ENDPOINTS

### 1. GET /api/loans/
**Descrição:** Get loans with filtering and sorting
```
- Filter: status in ["active", "overdue"]
- Features: find({$in}), populate("book_id"), populate("user_id"), sort("-due_date"), skip(), limit()
```
**Exemplo:**
```bash
curl http://localhost:8000/api/loans/?skip=0&limit=20
```

### 2. GET /api/loans/my-loans
**Descrição:** Get current user's loans with populated book data
```
- Features: find({user_id}), populate("book_id"), sort("-loan_date")
```
**Exemplo:**
```bash
curl http://localhost:8000/api/loans/my-loans
```

### 3. GET /api/loans/overdue
**Descrição:** Get all overdue loans using where() query (librarian only)
```
- Features: find().where("status").eq("active").where("due_date").lt(now)
- Demonstra: where() chains, comparison operators (lt, eq)
```
**Exemplo:**
```bash
curl http://localhost:8000/api/loans/overdue
```

### 4. GET /api/loans/{loan_id}
**Descrição:** Get specific loan with populated relationships
```
- Features: findOne({_id}), populate("book_id"), populate("user_id")
```
**Exemplo:**
```bash
curl http://localhost:8000/api/loans/507f1f77bcf86cd799439014
```

### 5. POST /api/loans/
**Descrição:** Create new loan (borrow a book)
```json
{
  "book_id": "507f1f77bcf86cd799439013",
  "duration_days": 14
}
```
**Features:** create(), automatic calculation of due_date

### 6. POST /api/loans/{loan_id}/return
**Descrição:** Return a borrowed book using findOneAndUpdate
```
- Features: findOneAndUpdate({_id}), $set, new=True
- Calcula multa automática se estiver atrasado
```
**Exemplo:**
```bash
curl -X POST http://localhost:8000/api/loans/507f1f77bcf86cd799439014/return
```

---

## 📊 STATISTICS ENDPOINTS

### 1. GET /api/stats/
**Descrição:** Get system statistics (admin only)
```
- Features: count(), sum(), complex aggregation queries
- Demonstra: find().count(), loops para agregação manual
```
**Exemplo:**
```bash
curl http://localhost:8000/api/stats/
```

### 2. GET /api/stats/my-stats
**Descrição:** Get user's personal statistics
```
- Features: find({user_id}).count(), aggregation by status
```
**Exemplo:**
```bash
curl http://localhost:8000/api/stats/my-stats
```

---

## 🔐 AUTHENTICATION ENDPOINTS

### POST /api/auth/register
**Descrição:** Register new user
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Doe",
  "role": "member"
}
```

### POST /api/auth/login
**Descrição:** Login user
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

---

## 🧪 TABERNACLE ORM FEATURES DEMONSTRATED

| Feature | Endpoint | Descrição |
|---------|----------|-----------|
| **populate()** | /api/books/, /api/loans/my-loans, /api/loans/ | Carrega dados relacionados (ForeignKey) |
| **where()** | /api/books/available, /api/loans/overdue | Queries com cláusulas condicionais |
| **find()** | Todos GET endpoints | Busca documentos com filtros |
| **findOne()** | /api/books/{id}, /api/loans/{id} | Busca um documento específico |
| **findOneAndUpdate()** | PUT /api/books/{id}, POST /api/loans/{id}/return | Atualiza e retorna documento |
| **findOneAndDelete()** | DELETE /api/books/{id} | Deleta e retorna documento |
| **create()** | POST endpoints | Cria novo documento |
| **$regex** | /api/books/search | Busca por padrão (case insensitive) |
| **$in** | /api/loans/ | Filtra por múltiplos valores |
| **skip/limit** | Todos GET endpoints | Paginação |
| **sort()** | Todos endpoints com múltiplos docs | Ordenação (asc/desc) |
| **count()** | /api/stats/ | Conta documentos |
| **Aggregation** | /api/stats/ | Agregação manual de dados |
| **where().gt/lt/eq()** | /api/books/available, /api/loans/overdue | Operadores de comparação |

---

## 📝 EXEMPLO DE USO COMPLETO

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "secret123",
    "full_name": "Alice Smith"
  }'

# 2. Get available books (using where query)
curl http://localhost:8000/api/books/available?skip=0&limit=5

# 3. Search books (regex)
curl "http://localhost:8000/api/books/search?q=python"

# 4. Create loan
curl -X POST http://localhost:8000/api/loans/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "book_id": "BOOK_ID_HERE",
    "duration_days": 14
  }'

# 5. Get user's loans (with populated book data)
curl http://localhost:8000/api/loans/my-loans \
  -H "Authorization: Bearer YOUR_TOKEN"

# 6. Get overdue loans (using where clauses - librarian only)
curl http://localhost:8000/api/loans/overdue \
  -H "Authorization: Bearer LIBRARIAN_TOKEN"

# 7. Return book (using findOneAndUpdate)
curl -X POST http://localhost:8000/api/loans/LOAN_ID_HERE/return \
  -H "Authorization: Bearer YOUR_TOKEN"

# 8. Get statistics (admin only)
curl http://localhost:8000/api/stats/ \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🎓 CONCEITOS DEMONSTRADOS

### TabernacleORM Features:
1. **ForeignKey** - Relacionamentos entre coleções
2. **populate()** - Carrega documentos relacionados (como JOIN em SQL)
3. **where() chains** - Queries programáticas com múltiplas condições
4. **MongoDB operators** - $regex, $in, $gte, $lte, $lt, $gt, $set, $or
5. **Paginação** - skip() e limit()
6. **Ordenação** - sort() com asc/desc
7. **CRUD completo** - Create, Read, Update, Delete
8. **Counts** - count() para agregação básica
9. **Busca por texto** - $regex para regex matching
10. **Auto-increment/timestamps** - auto_now_add para datas automáticas

