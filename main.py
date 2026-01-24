from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import mysql.connector
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

@app.get("/fetch")
async def fetch_data(
    query_type: str = Query(..., description="Type of query: empRegister, group, rfid, rfidmine"),
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if query_type == "empRegister":
            cursor.execute("SELECT * FROM sapMsEmpRegister")
            return cursor.fetchall()

        elif query_type == "group":
            cursor.execute("SELECT * FROM msgroup")
            return cursor.fetchall()

        elif query_type == "rfid":
            query = """
                SELECT 
                    staffAttendanceRFID.ADate,
                    (SELECT CONCAT(surname, ' ', name) 
                     FROM msemployee 
                     WHERE msemployee.empno = staffAttendanceRFID.emid) AS FullName,
                    (SELECT aliasName 
                     FROM msemployee 
                     WHERE msemployee.empno = staffAttendanceRFID.emid) AS AliasName,
                    TIME_FORMAT(staffAttendanceRFID.InTime, '%H:%i:%s') AS InTime,
                    TIME_FORMAT(staffAttendanceRFID.OutTime, '%H:%i:%s') AS OutTime,
                    staffAttendanceRFID.emid
                FROM staffAttendanceRFID
                WHERE staffAttendanceRFID.ADate = CURRENT_DATE()
                ORDER BY staffAttendanceRFID.InTime
            """
            cursor.execute(query)
            return cursor.fetchall()

        elif query_type.startswith("z"): 
            emid = int(query_type[1:])
            print(emid)
            query = """
                SELECT 
                    staffAttendanceRFID.ADate,
                    (SELECT CONCAT(surname, ' ', name) 
                     FROM msemployee 
                     WHERE msemployee.empno = staffAttendanceRFID.emid) AS FullName,
                    (SELECT aliasName 
                     FROM msemployee 
                     WHERE msemployee.empno = staffAttendanceRFID.emid) AS AliasName,
                    TIME_FORMAT(staffAttendanceRFID.InTime, '%H:%i:%s') AS InTime,
                    TIME_FORMAT(staffAttendanceRFID.OutTime, '%H:%i:%s') AS OutTime
                FROM staffAttendanceRFID
                WHERE staffAttendanceRFID.emid = %(emdid)s ORDER BY staffAttendanceRFID.ADate DESC, staffAttendanceRFID.InTime
            """
            cursor.execute(query, {'emdid': emid})
            result = cursor.fetchall()
            if not result:
                raise HTTPException(status_code=404, detail=f"No attendance records found for emid")
            return result

        else:
            raise HTTPException(status_code=400, detail="Unknown query_type parameter")

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
