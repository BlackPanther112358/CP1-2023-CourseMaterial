from classes import Student, DB_NAME, STUDENT_COLLECTION
import pandas as pd
import pymongo
import logging as log

STUDENT_FILE_NAME = "CP1 & CP2 Registration list.xlsx"
STUDENT_ID_FILE = "CF_IDs.xlsx"
STUDENT_SHEET = "CP1"

log.basicConfig(filename="update_student_list.log", filemode="a", level=log.DEBUG)
logging = log.getLogger(__name__)

def read_sheet_students() -> pd.DataFrame:
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

def read_sheet_ids() -> pd.DataFrame:
    """Reads the sheet containing the CF IDs from the excel file and returns a pandas dataframe"""
    logging.info("Reading CF ID sheet from excel file")
    try:
        df:pd.DataFrame = pd.read_excel(STUDENT_ID_FILE)
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
    students:pd.DataFrame = read_sheet_students()
    cf_ids:pd.DataFrame = read_sheet_ids()
    ids:dict[str, str] = {}
    for row in cf_ids.itertuples():
        ids[row[4]] = row[5]
    cnt:int = 0
    for row in students.itertuples():
        cnt += 1
        student_list.append(Student(
            name=row[2],
            roll=row[1],
            email=row[3],
            srl_no=cnt,
            cf_id=ids.get(row[1], None)
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
    cnt:int = 0
    logging.info("Updating students to MongoDB")
    for student in student_list:
        cnt += 1
        collection.update_one(
            filter={"roll": student.roll},
            update={"$set": student.to_dict()},
            upsert=True
        )
    logging.info(f"{cnt} students updated to MongoDB")

if __name__ == "__main__":
    logging.info("Starting update_student_list.py")
    update_students()
    logging.info("Finished update_student_list.py")