from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.get("/bills")
def get_bills():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT bl.*, bk.guest_name, bk.phone, bk.room_number
        FROM bills bl
        JOIN bookings bk ON bl.booking_id = bk.id
        ORDER BY bl.created_at DESC
    """)
    bills = cursor.fetchall()
    cursor.close()
    conn.close()

    for b in bills:
        if b.get("created_at"):
            b["created_at"] = str(b["created_at"])

    return bills

@router.get("/reports/daily")
def daily_report():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pay_mode,
            COUNT(*) as count,
            SUM(total_amount) as total,
            SUM(balance) as collected
        FROM bills
        WHERE DATE(created_at) = CURDATE()
        GROUP BY pay_mode
    """)
    breakdown = cursor.fetchall()

    cursor.execute("""
        SELECT
            SUM(total_amount) as total_revenue,
            COUNT(*) as total_checkouts
        FROM bills
        WHERE DATE(created_at) = CURDATE()
    """)
    summary = cursor.fetchone()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='available' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN status='occupied'  THEN 1 ELSE 0 END) as occupied,
            SUM(CASE WHEN status='cleaning'  THEN 1 ELSE 0 END) as cleaning,
            COUNT(*) as total
        FROM rooms
    """)
    room_stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "summary": summary,
        "breakdown": breakdown,
        "room_stats": room_stats
    }