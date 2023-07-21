from classes import Student, Lab_performance, GoogleSheetConnector, DB_NAME, STUDENT_COLLECTION, LAB_COLLECTION, LAB_IDS, GROUP_ID
import pymongo
import random
import requests
import logging as log
import time
import json
import hashlib

log.basicConfig(filename="update_labs.log", filemode="w", level=log.DEBUG)
logging = log.getLogger(__name__)

client = None
db = None
students = None
labs = None

SHEET_ROW_OFFSET:int = 2
LAB_COL_OFFSETS:dict[str, int] = {
    '1': 4,
    '2': 7,
    '3': 10,
}

def load_codeforces_keys()->None:
    """Load the codeforces keys from the json file"""
    global CODEFORCES_KEY, CODEFORCES_SECRET
    with open("CF_API_keys.json", "r") as f:
        data = json.load(f)
        CODEFORCES_KEY = data["key"]
        CODEFORCES_SECRET = data["secret"]

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

def questions_solved(contest_id:str, cf_id:str)->set[str]:
    """Returns the set of questions solved by a student in a contest"""
    cur_time = int(time.time())
    random.seed(cur_time)
    rand = str(random.randint(100000, 999999))
    raw_str = f"{rand}/contest.status?apiKey={CODEFORCES_KEY}&contestId={contest_id}&groupCode={GROUP_ID}&handle={cf_id}&time={cur_time}#{CODEFORCES_SECRET}"
    hash_str = hashlib.sha512(raw_str.encode()).hexdigest()
    try:
        res = requests.get(f"https://codeforces.com/api/contest.status?groupCode={GROUP_ID}&contestId={contest_id}&handle={cf_id}&apiKey={CODEFORCES_KEY}&time={cur_time}&apiSig={rand}{hash_str}")
        if res.status_code != 200:
            logging.error(msg=f"Error while fetching details for {cf_id}: {res.status_code}")
            return set()
        logging.debug(msg=f"Response for {cf_id}: {res.text}")
        data = res.json()
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
    
def get_Lab_performance(cf_id:str, roll:str) -> Lab_performance:
    """Returns the performance of a student for all 3 lab"""
    lab_perf:Lab_performance = Lab_performance(roll)
    for lab_num in ['1', '2', '3']:
        ques_solved = questions_solved(LAB_IDS[lab_num]["main"], cf_id)
        for ques in ques_solved:
            lab_perf.solved(lab_num, ques)
        time.sleep(1)
        ques_upsolved = questions_solved(LAB_IDS[lab_num]["upsolve"], cf_id)
        for ques in ques_upsolved:
            lab_perf.upsolved(lab_num, ques)
        time.sleep(1)
    lab_perf.get_score()
    lab_perf.get_final_score()
    logging.debug(msg=f"Lab performance for {cf_id}: {lab_perf.to_dict()}")
    return lab_perf

def main()->None:
    """Update the lab score for all the students for the contest or intialize the sheet"""
    try:
        global client, db, students, labs
        client = pymongo.MongoClient()
        db = client[DB_NAME]
        students = db[STUDENT_COLLECTION]
        labs = db[LAB_COLLECTION]
        load_codeforces_keys()
    except Exception as e:
        logging.error(msg=f"Error while connecting to the database: {e}")
        raise e
    try:
        global sheet_connector
        sheet_connector = GoogleSheetConnector("labs")
    except Exception as e:
        logging.error(msg=f"Error while connecting to Google Sheet: {e}")
        raise e
    student_list:list[Student] = get_student_info()
    labs.delete_many({})
    for student in student_list:
        time.sleep(3)
        logging.info(msg=f"Updating lab info for {student}")
        sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, 1, student.name)
        sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, 2, student.cf_id)
        time.sleep(1)
        lab_performance:Lab_performance = get_Lab_performance(student.cf_id, student.roll)
        logging.debug(msg=f"Lab performance for {student}: {lab_performance.to_dict()}")
        sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, 3, lab_performance.final_score)
        time.sleep(1)
        for lab_num in ['1', '2', '3']:
            cnt_solved = sum([1 for problem in lab_performance.scores[lab_num].values() if problem == 1])
            cnt_unsolved = sum([1 for problem in lab_performance.scores[lab_num].values() if problem == 0])
            cnt_upsolved = 6 - cnt_solved - cnt_unsolved
            sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, LAB_COL_OFFSETS[lab_num], cnt_solved)
            sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, LAB_COL_OFFSETS[lab_num] + 1, cnt_upsolved)
            sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, LAB_COL_OFFSETS[lab_num] + 2, lab_performance.tot_score[lab_num])
            time.sleep(3)
        labs.insert_one(lab_performance.to_dict())
        logging.info(msg=f"Updated lab info for {student}")
    logging.info(msg="Finished updating lab info for all students")
    client.close()

if __name__ == "__main__":
    logging.info(msg="Starting update_labs.py")
    main()
    logging.info(msg="Finished update_labs.py")
