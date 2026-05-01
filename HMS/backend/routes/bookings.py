from fastapi import APIRouter
from pydantic import BaseModel
from database import get_connection
from datetime import datetime

router = APIRouter()

class CheckInRequest(BaseModel):
    room_number: str
    guest_name: str
    phone: str
    id_proof: str
    advance: float
    pay_mode: str

@router.post("/bookings/checkin")
def checkin(req: CheckInRequest):
    conn = get_connection()
    cursor = conn.cursor()

    # Save booking
    cursor.execute("""
        INSERT INTO bookings
        (room_number, guest_name, phone, id_proof, advance, pay_mode, check_in, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
    """, (
        req.room_number, req.guest_name, req.phone,
        req.id_proof, req.advance, req.pay_mode,
        datetime.now()
    ))

    # Mark room as occupied
    cursor.execute(
        "UPDATE rooms SET status = 'occupied' WHERE room_number = %s",
        (req.room_number,)
    )

    conn.commit()
    booking_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return {"success": True, "booking_id": booking_id}

@router.get("/bookings/active")
def get_active_bookings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, r.type, r.price
        FROM bookings b
        JOIN rooms r ON b.room_number = r.room_number
        WHERE b.status = 'active'
        ORDER BY b.check_in DESC
    """)
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert datetime to string for JSON
    for b in bookings:
        if b.get("check_in"):
            b["check_in"] = str(b["check_in"])

    return bookings

@router.post("/bookings/checkout/{booking_id}")
def checkout(booking_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get booking + room price
    cursor.execute("""
        SELECT b.*, r.price
        FROM bookings b
        JOIN rooms r ON b.room_number = r.room_number
        WHERE b.id = %s
    """, (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        return {"success": False, "message": "Booking not found"}

    # Calculate bill
    check_in  = booking["check_in"]
    check_out = datetime.now()
    days      = max(1, (check_out - check_in).days)
    total     = days * float(booking["price"])
    balance   = max(0, total - float(booking["advance"]))

    # Save bill
    cursor2 = conn.cursor()
    cursor2.execute("""
        INSERT INTO bills
        (booking_id, days, room_price, total_amount, advance, balance, pay_mode, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        booking_id, days, booking["price"],
        total, booking["advance"], balance,
        booking["pay_mode"], check_out
    ))

    # Update booking status
    cursor2.execute(
        "UPDATE bookings SET status='completed', check_out=%s WHERE id=%s",
        (check_out, booking_id)
    )

    # Set room to cleaning
    cursor2.execute(
        "UPDATE rooms SET status='cleaning' WHERE room_number=%s",
        (booking["room_number"],)
    )

    conn.commit()
    cursor.close()
    cursor2.close()
    conn.close()

    return {
        "success": True,
        "bill": {
            "days": days,
            "room_price": float(booking["price"]),
            "total": total,
            "advance": float(booking["advance"]),
            "balance": balance
        }
    }