from fastapi import APIRouter
from pydantic import BaseModel
from database import get_connection

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

@router.post("/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s AND password = %s AND role = %s",
        (req.username, req.password, req.role)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "role": user["role"]
            }
        }
    else:
        return {"success": False, "message": "Invalid credentials"}