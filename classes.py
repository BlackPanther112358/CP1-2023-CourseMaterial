from enum import Enum
from typing import List, Optional
import gspread

DB_NAME:str = "cp1-2023"
STUDENT_COLLECTION:str = "students"
PROBLEM_COLLECTION:str = "practice"
PROBLEM_CAP:int = 50
DIV2_COLLECTION:str = "div2"
DIV2_CAP:int = 3000
DIV3_COLLECTION:str = "div3"
DIV3_CAP:int = 10
LAB_COLLECTION:str = "labs"

SHEET_ID:str = "1SHPTPYRx3ZDkgolJw7zGr6TLB41bb4jZDp23TZDq-lw"
SHEET_NAME_TO_ID:dict[str, int] = {
    "practice": 0,
    "div2": 1,
    "div3": 2,
    "labs": 3,
}

GROUP_ID:str = "uc4hHQ2lbv"
LAB_IDS:dict[str, dict[str, str]] = {
    '1': { "main":"447928", "upsolve":"447930" },
    '2': { "main":"450117", "upsolve":"450118" },
    '3': { "main":"452783", "upsolve":"452785" },
}

UPSOLVE_RATIO:dict[int, float] = {
    '1': 0.6,
    '2': 0.4,
    '3': 0.4,
}

class Student:

    def __init__(self, name:str, roll:str, email:str, srl_no:int, cf_id:str=None):
        self.name = name
        self.roll = roll
        self.email = email
        self.srl_no = srl_no
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
            "cf_id": self.cf_id,
            "sno" : self.srl_no,
        }
    
class Contest:

    def __init__(self, contest_id:int, srl_no:int, scores:dict[int:int])->None:
        self.contest_id = contest_id
        self.srl_no = srl_no
        self.scores = scores
    
    def __str__(self):
        return f"Contest {self.contest_id} for {self.srl_no}"
    
    def __repr__(self):
        return f"Contest(contest_id={self.contest_id}, srl_no={self.srl_no}, scores={self.scores})"
    
    def to_dict(self):
        dict_val:dict = {}
        dict_val["contest_id"] = self.contest_id
        dict_val["srl_no"] = self.srl_no
        for key, val in self.scores.items():
            dict_val[str(key)] = val
        return dict_val
    
class Lab_performance:

    def __init__(self, student_roll:str)->None:
        self.student_roll = student_roll
        self.scores = {
            '1': {'A':0, 'B':0, 'C':0, 'D':0, 'E':0, 'F':0},
            '2': {'A':0, 'B':0, 'C':0, 'D':0, 'E':0, 'F':0},
            '3': {'A':0, 'B':0, 'C':0, 'D':0, 'E':0, 'F':0},
        }
        self.tot_score = {
            '1': 0,
            '2': 0,
            '3': 0,
        }
        self.final_score = 0

    def solved(self, lab_num:int, problem:str)->None:
        self.scores[lab_num][problem] = 1

    def upsolved(self, lab_num:int, problem:str)->None:
        if(self.scores[lab_num][problem] == 0):
            self.scores[lab_num][problem] = UPSOLVE_RATIO[lab_num]

    def get_score(self)->float:
        for lab_num in ['1', '2', '3']:
            self.tot_score[lab_num] = sum(self.scores[lab_num].values())*(15/6)
        return self.tot_score
    
    def get_final_score(self)->float:
        self.final_score = sum(self.tot_score.values()) - min(self.tot_score.values())
        return self.final_score
    
    def __str__(self):
        return f"Lab for {self.student_roll}"
    
    def __repr__(self):
        return f"Lab_performance(student_roll={self.student_roll}, scores={self.scores}, tot_score={self.tot_score}), final_score={self.final_score})"
    
    def to_dict(self):
        dict_val:dict = {}
        dict_val["student_roll"] = self.student_roll
        dict_val["scores"] = self.scores
        dict_val["tot_score"] = self.tot_score
        dict_val["final_score"] = self.final_score
        return dict_val
    
class GoogleSheetConnector:
    """Class to connect to the Google sheet"""

    def __init__(self, sheet_name:str) -> None:
        google_account = gspread.service_account()
        self.sheet = google_account.open_by_key(SHEET_ID)
        self.worksheet = self.sheet.get_worksheet(SHEET_NAME_TO_ID[sheet_name])

    def get_worksheet(self) -> gspread.Worksheet:
        """Returns the worksheet"""
        return self.worksheet
    
    def get_sheet(self) -> gspread.Spreadsheet:
        """Returns the sheet"""
        return self.sheet
    
    def get_cell(self, row:int, col:int) -> str:
        """Returns the value of the cell"""
        return self.worksheet.cell(row, col).value
    
    def update_cell(self, row:int, col:int, value) -> None:
        """Updates the value of the cell"""
        self.worksheet.update_cell(row, col, value)
