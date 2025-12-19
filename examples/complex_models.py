
import asyncio
from typing import List, Optional
from tabernacleorm import connect, Model, fields

# Define Models for a University System
class Department(Model):
    name = fields.StringField(required=True, unique=True)
    budget = fields.FloatField(default=0.0)
    
    class Meta:
        collection = "departments"

class Student(Model):
    name = fields.StringField(required=True)
    email = fields.StringField(unique=True)
    # Array of strings (tags/interests) - Supported in Mongo/PG
    interests = fields.ArrayField(fields.StringField()) 
    details = fields.JSONField() # Flexible schema
    
    class Meta:
        collection = "students"

class Course(Model):
    code = fields.StringField(required=True, unique=True, max_length=10)
    title = fields.StringField(required=True)
    department_id = fields.ForeignKey(Department, on_delete="CASCADE")
    credits = fields.IntegerField(default=3)
    
    class Meta:
        collection = "courses"

class Enrollment(Model):
    student_id = fields.ForeignKey(Student)
    course_id = fields.ForeignKey(Course)
    grade = fields.FloatField(nullable=True)
    enrolled_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        collection = "enrollments"

async def main():
    # Connect
    await connect("sqlite:///university.db").connect()
    
    # NOTE: In a real app, you would run:
    # tabernacle makemigrations
    # tabernacle migrate
    # Here we simulate it or rely on the previous auto-create logic for testing script
    
    print("Creating tables (simulation of migrate)...")
    await Department.createTable()
    await Student.createTable()
    await Course.createTable()
    await Enrollment.createTable()
    
    # 1. Populate Data
    cs_dept = await Department.create(name="Computer Science", budget=500000.0)
    math_dept = await Department.create(name="Mathematics", budget=300000.0)
    
    s1 = await Student.create(
        name="Alice", 
        email="alice@uni.edu", 
        interests=["AI", "Robotics"],
        details={"year": 2, "advisor": "Dr. Smith"}
    )
    
    c1 = await Course.create(code="CS101", title="Intro to CS", department_id=cs_dept.id)
    c2 = await Course.create(code="MATH202", title="Calculus II", department_id=math_dept.id)
    
    # 2. Relationships
    await Enrollment.create(student_id=s1.id, course_id=c1.id)
    await Enrollment.create(student_id=s1.id, course_id=c2.id)
    
    # 3. Aggregation / Complex Query
    print("Finding all enrollments for Alice...")
    # This would use lookup/join logic in a real query builder
    enrollments = await Enrollment.find({"student_id": s1.id}).exec()
    for e in enrollments:
        # Fetch related course (manual populate for now, lookup support coming)
        course = await Course.findById(e.course_id)
        print(f"- Enrolled in: {course.title} ({course.code})")

if __name__ == "__main__":
    asyncio.run(main())
