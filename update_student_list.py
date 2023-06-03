from classes import Student, DB_NAME, STUDENT_COLLECTION
import pandas as pd
import pymongo
import logging as log

STUDENT_FILE_NAME = "CP1 & CP2 Registration list.xlsx"
STUDENT_SHEET = "CP1"

log.basicConfig(filename="update_student_list.log", filemode="a", level=log.DEBUG)
logging = log.getLogger(__name__)

def read_sheet() -> pd.DataFrame:
    """Reads the student sheet from the excel file and returns a pandas dataframe"""
    logging.info("Reading student sheet from excel file")
    try:
        df:pd.DataFrame = pd.read_excel(STUDENT_FILE_NAME, sheet_name=STUDENT_SHEET)
    except FileNotFoundError:
        logging.error(msg=f"File {STUDENT_FILE_NAME} not found")
        raise
    except Exception as e:
        logging.error(msg=f"Error while reading excel file: {e}")
        raise
    return df

def get_student_list() -> list[Student]:
    """Returns the list of students"""
    student_list:list[Student] = []
    students:pd.DataFrame = read_sheet()
    for row in students.itertuples():
        student_list.append(Student(
            name=row[1],
            roll=row[2],
            email=row[3],
        ))
    logging.info(msg=f"Student list created with {len(student_list)} students")
    logging.debug(msg=f"Student list: {student_list}")
    return student_list

def update_students():
    """Updates the students to MongoDB"""
    logging.info("Fetching student list from Excel file")
    student_list:list[Student] = get_student_list()
    logging.info("Connecting to MongoDB")
    try:
        client = pymongo.MongoClient()
        db = client[DB_NAME]
        collection = db[STUDENT_COLLECTION]
    except Exception as e:
        logging.error(msg=f"Error while connecting to MongoDB: {e}")
        raise
    logging.info("Updating students to MongoDB")
    for student in student_list:
        collection.update_one(
            filter={"roll": student.roll},
            update={"$set": student.to_dict()},
            upsert=True
        )
    logging.info("Students updated to MongoDB")

if __name__ == "__main__":
    logging.info("Starting update_student_list.py")
    update_students()
    logging.info("Finished update_student_list.py")