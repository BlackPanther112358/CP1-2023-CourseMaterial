from classes import Student, GoogleSheetConnector, DB_NAME, STUDENT_COLLECTION, PROBLEM_COLLECTION, PROBLEM_CAP
from collections import defaultdict
import requests
import pymongo
import logging as log
import time

log.basicConfig(filename="update_practice.log", filemode="w", level=log.DEBUG)
logging = log.getLogger(__name__)

client = None
db = None
students = None
practice_collection = None
sheet_connector = None

SHEET_ROW_OFFSET:int = 2
SHEET_COL_OFFSET:int = 3

START_TIME_STAMP = 1685298600 # Time stamp for May 29 2023 00:00:00

class Practice:
    """Class to store practice info for a student"""

    def __init__(self, roll:int, prac_info:dict[int:int]) -> None:
        self.roll = roll
        self.prac_info = prac_info

    def __str__(self) -> str:
        return f"Practice info for {self.roll}"
    
    def __repr__(self) -> str:
        return f"Practice(roll={self.roll}, prac_info={self.prac_info})"
    
    def to_dict(self) -> dict:
        dict_val:dict = {}
        dict_val["roll"] = self.roll
        for key, val in self.prac_info.items():
            dict_val[str(key)] = val
        return dict_val

def get_problem_score(prob_rating:int) -> int:
    """Returns the score for a problem based on its rating"""
    return max(0, (prob_rating - 1099 + 199)//200)

def get_student_info() -> list[Student]:
    """Returns the list of students"""
    student_list:list[Student] = []
    cursor = students.find({})
    for doc in cursor:
        student_list.append(Student(
            name=doc["name"],
            roll=doc["roll"],
            email=doc["email"],
            srl_no=doc["sno"],
            cf_id=doc["cf_id"]
        ))
    logging.info(msg=f"Student list created with {len(student_list)} students")
    logging.debug(msg=f"Student list: {student_list}")
    return student_list

def get_practice_info(cf_id:str) -> dict[int, int]:
    """Returns the practice info for a student"""
    try:
        data = requests.get(f"https://codeforces.com/api/user.status?handle={cf_id}&from=1").json()
        if data["status"] == "FAILED":
            logging.error(msg=f"Error while fetching practice info for {cf_id}: {data['comment']}")
            return defaultdict(int)
        if data["status"] != "OK":
            logging.error(msg=f"Error while fetching practice info for {cf_id}: {data['data']}")
            raise Exception(f"Error while fetching practice info for {cf_id}")
    except Exception as e:
        logging.error(msg=f"Error while fetching practice info for {cf_id}: {e}")
        raise
    practice_info:dict[int, int] = defaultdict(int)
    for submission in data["result"]:
        if submission["creationTimeSeconds"] < START_TIME_STAMP:
            continue
        if submission["verdict"] != "OK":
            continue
        try:
            prob_rating:int = int(submission["problem"]["rating"])
        except KeyError:
            continue
        except Exception as e:
            logging.error(msg=f"Error while fetching practice info for {cf_id}: {e}")
            raise
        practice_info[get_problem_score(prob_rating)] += 1
    logging.debug(msg=f"Practice info for {cf_id}: {practice_info}")
    return practice_info


def update_info(stud_prac:Practice):
    """Updates the practice info for a student"""
    logging.info(msg=f"Updating practice info for {stud_prac.roll}")
    try:
        practice_collection.update_one(
            {"roll": stud_prac.roll},
            {"$set": stud_prac.to_dict()},
            upsert=True
        )
    except Exception as e:
        logging.error(msg=f"Error while updating practice info for {stud_prac.roll}: {e}")
        raise

    stud_roll = stud_prac.roll
    stud_info = students.find_one({"roll": stud_roll})
    if stud_info is None:
        logging.error(msg=f"Student {stud_roll} not found in database")
        return
    sheet_connector.update_cell(SHEET_ROW_OFFSET + stud_info["sno"], 1, stud_info["name"])
    sheet_connector.update_cell(SHEET_ROW_OFFSET + stud_info["sno"], 2, stud_info["cf_id"])
    score:int = 0
    for key, val in stud_prac.prac_info.items():
        time.sleep(1)
        sheet_connector.update_cell(SHEET_ROW_OFFSET + stud_info["sno"], SHEET_COL_OFFSET + key + 1, val)
        score += val * key
    sheet_connector.update_cell(SHEET_ROW_OFFSET + stud_info["sno"], 3, min(score, PROBLEM_CAP))

def main():
    """Update the practice info for all students"""
    try:
        global client, db, students, practice_collection
        client = pymongo.MongoClient()
        db = client[DB_NAME]
        students = db[STUDENT_COLLECTION]
        practice_collection = db[PROBLEM_COLLECTION]
    except Exception as e:
        logging.error(msg=f"Error while connecting to MongoDB: {e}")
        raise
    try:
        global sheet_connector
        sheet_connector = GoogleSheetConnector("practice")
    except Exception as e:
        logging.error(msg=f"Error while connecting to Google Sheet: {e}")
        raise
    student_list:list[Student] = get_student_info()
    for student in student_list:
        time.sleep(5)
        logging.info(msg=f"Updating practice info for {student}")
        practice_info:dict[int, int] = get_practice_info(student.cf_id)
        stud_prac = Practice(roll=student.roll, prac_info=practice_info)
        update_info(stud_prac)

if __name__ == "__main__":
    logging.info(msg="Starting update_practice.py")
    main()
    logging.info(msg="Ending update_practice.py")