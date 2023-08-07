from classes import get_json_resp, Student, Contest, GoogleSheetConnector, DB_NAME, STUDENT_COLLECTION, GROUP_ID
import pymongo
import json
import random
import hashlib
import pandas as pd
import requests
import logging as log
import time


log.basicConfig(filename="update_endsem.log", filemode="w", level=log.DEBUG)
logging = log.getLogger(__name__)

client = None
db = None
students = None
sheet_connector = None

ATTENDANCE_SHEET:str = "Endsem_data.xlsx"

SHEET_ROW_OFFSET:int = 2

def load_codeforces_keys()->None:
    """Load the codeforces keys from the json file"""
    global CODEFORCES_KEY, CODEFORCES_SECRET
    with open("CF_API_keys.json", "r") as f:
        data = json.load(f)
        CODEFORCES_KEY = data["key"]
        CODEFORCES_SECRET = data["secret"]

def questions_solved(contest_id:str, cf_id:str)->set[str]:
    """Returns the set of questions solved by a student in a contest"""
    cur_time = int(time.time())
    random.seed(cur_time)
    rand = str(random.randint(100000, 999999))
    raw_str = f"{rand}/contest.status?apiKey={CODEFORCES_KEY}&contestId={contest_id}&groupCode={GROUP_ID}&handle={cf_id}&time={cur_time}#{CODEFORCES_SECRET}"
    hash_str = hashlib.sha512(raw_str.encode()).hexdigest()
    try:
        data = get_json_resp(f"https://codeforces.com/api/contest.status?groupCode={GROUP_ID}&contestId={contest_id}&handle={cf_id}&apiKey={CODEFORCES_KEY}&time={cur_time}&apiSig={rand}{hash_str}")
        if data["status"] == "FAILED":
            logging.error(msg=f"Error while fetching details for {cf_id}")
            return set()
        if data["status"] != "OK":
            logging.error(msg=f"Error while fetching details for {cf_id}: {data['comment']}")
            return set()
        if data["result"] == []:
            logging.info(msg=f"No submissions for {cf_id} in contest {contest_id}")
            return set()
    except Exception as e:
        logging.error(msg=f"Error while fetching details for {cf_id}: {e}")
        raise e
    solved_problems:set[str] = set()
    for submission in data["result"]:
        if submission["verdict"] == "OK" and submission["author"]["participantType"] == "CONTESTANT":
            solved_problems.add(submission["problem"]["index"])
    logging.debug(msg=f"Questions solved by {cf_id} in contest {contest_id}: {solved_problems}")
    return solved_problems

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

def get_attendance() -> dict[int:dict[str:str]]:
    """Returns the list of attendance records for endsem exam"""
    logging.info(msg="Fetching attendance records for endsem exam")
    sheet_data = pd.read_excel(ATTENDANCE_SHEET)
    sheet_data = sheet_data.dropna()
    attendance:dict[int:dict[str:str]] = {}
    for row in sheet_data.itertuples():
        attendance[int(row[1])] = {"cf_id": row[2], "contest_id": str(int(row[3]))}
    logging.info(msg=f"Attendance records fetched for {len(attendance)} students")
    logging.debug(msg=f"Attendance records: {attendance}")
    return attendance

def main()->None:
    try:
        global client, db, students, div3_collection
        client = pymongo.MongoClient()
        db = client[DB_NAME]
        students = db[STUDENT_COLLECTION]
        load_codeforces_keys()
    except Exception as e:
        logging.error(msg=f"Error while connecting to MongoDB: {e}")
        raise
    try:
        global sheet_connector
        sheet_connector = GoogleSheetConnector("endsem")
    except Exception as e:
        logging.error(msg=f"Error while connecting to Google Sheet: {e}")
        raise
    student_list:list[Student] = get_student_info()
    attendance_list:dict[int:dict[str:str]] = get_attendance()
    for student in student_list:
        logging.info(msg=f"Updating details for {student.name} ({student.roll})")
        if student.roll not in attendance_list:
            logging.error(msg=f"No attendance record found for {student.name} ({student.roll})")
            continue
        solve_cnt = len(questions_solved(attendance_list[student.roll]["contest_id"], attendance_list[student.roll]["cf_id"]))
        sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, 3, solve_cnt)
        logging.info(msg=f"Details updated for {student.name} ({student.roll})")

if __name__ == "__main__":
    logging.info(msg="Starting the update process")
    main()
    logging.info(msg="Update process completed")