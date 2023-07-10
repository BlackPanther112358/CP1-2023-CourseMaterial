from classes import Student, GoogleSheetConnector, DB_NAME, STUDENT_COLLECTION, DIV2_COLLECTION, DIV2_CAP
import pymongo
import requests
import logging as log
import time

log.basicConfig(filename="update_div2.log", filemode="w", level=log.DEBUG)
logging = log.getLogger(__name__)

client = None
db = None
students = None
div2_collection = None
sheet_connector = None

SHEET_ROW_OFFSET:int = 2
SHEET_COL_OFFSET:int = 3

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

def main()->None:
    """Update the score for all the students for the contest or intialize the sheet"""
    try:
        global client, db, students, div2_collection
        client = pymongo.MongoClient()
        db = client[DB_NAME]
        students = db[STUDENT_COLLECTION]
        div2_collection = db[DIV2_COLLECTION]
    except Exception as e:
        logging.error(msg=f"Error while connecting to MongoDB: {e}")
        raise
    try:
        global sheet_connector
        sheet_connector = GoogleSheetConnector("div2")
    except Exception as e:
        logging.error(msg=f"Error while connecting to Google Sheet: {e}")
        raise
    student_list:list[Student] = get_student_info()
    mode:int = int(input("Enter 1 to initialize, 2 to update the sheet: "))
    if mode == 1:
        for student in student_list:
            time.sleep(3)
            logging.info(msg=f"Updating div2 info for {student}")
            sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, 1, student.name)
            sheet_connector.update_cell(SHEET_ROW_OFFSET + student.srl_no, 2, student.cf_id)
    elif mode == 2:
        pass
    else:
        logging.error(msg=f"Invalid mode {mode}")
        raise ValueError(f"Invalid mode {mode}")

if __name__ == "__main__":
    logging.info(msg="Starting update_div2.py")
    main()
    logging.info(msg="Ending update_div2.py")