from fastapi import APIRouter
from pydantic import BaseModel
from database import get_connection

router = APIRouter()

@router.get("/rooms")
def get_rooms():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms ORDER BY room_number")
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return rooms

@router.put("/rooms/{room_number}/status")
def update_room_status(room_number: str, body: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE rooms SET status = %s WHERE room_number = %s",
        (body["status"], room_number)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"success": True, "message": f"Room {room_number} updated"}