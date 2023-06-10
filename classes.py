from enum import Enum
from typing import List, Optional

DB_NAME:str = "cp1-2023"
STUDENT_COLLECTION:str = "students"
PROBLEM_COLLECTION:str = "problems"
PROBLEM_CAP:int = 50
DIV2_COLLECTION:str = "div2"
DIV2_CAP:int = 3000
DIV3_COLLECTION:str = "div3"
DIV3_CAP:int = 10

class Student:

    def __init__(self, name:str, roll:str, email:str, cf_id:str=None):
        self.name = name
        self.roll = roll
        self.email = email
        self.cf_id = cf_id

    def __str__(self):
        return f"{self.name} ({self.roll})"

    def __repr__(self):
        return f"Student(roll={self.roll}, name={self.name}, email={self.email}, cf_id={self.cf_id})"

    def to_dict(self):
        return {
            "name": self.name,
            "roll": self.roll,
            "email": self.email,
            "cf_id": self.cf_id
        }