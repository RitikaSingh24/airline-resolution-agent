"""
Idempotent seed script.

Inserts exactly 3 customers and 4 bookings.
Safe to run multiple times — uses natural identity keys:
  * Customer.email  for customers
  * (Booking.pnr, Booking.segment_label)  for bookings

Only customers and bookings are seeded.
Conversations, messages, actions, and escalations are NOT seeded.
"""
import datetime

from sqlalchemy.orm import Session

from models.customer import Customer
from models.booking import Booking

# ---------------------------------------------------------------------------
# Seed definitions — source of truth for all tests
# ---------------------------------------------------------------------------

CUSTOMERS_SEED = [
    {
        "name": "Priya Nair",
        "tier": "Gold",
        "email": "priya.nair@example.com",
        "phone_masked": "+91-98xxxxxxx1",
        "flights_12m": 6,
        "prior_complaints": 1,
        "complaint_note": "delayed baggage, resolved w/ voucher",
    },
    {
        "name": "Arvind Kulkarni",
        "tier": "Silver",
        "email": "arvind.kulkarni@example.com",
        "phone_masked": "+91-98xxxxxxx2",
        "flights_12m": 3,
        "prior_complaints": 0,
        "complaint_note": None,
    },
    {
        "name": "Meher Kaur",
        "tier": "Platinum",
        "email": "meher.kaur@example.com",
        "phone_masked": "+91-98xxxxxxx3",
        "flights_12m": 10,
        "prior_complaints": 1,
        "complaint_note": "overbooking, resolved w/ tier upgrade",
    },
]

# Bookings keyed by (pnr, segment_label); customer identified by email.
BOOKINGS_SEED = [
    # Booking 1 — Priya outbound (Cancelled)
    {
        "pnr": "SK4821X",
        "customer_email": "priya.nair@example.com",
        "segment_label": "outbound",
        "flight_no": "SK-204",
        "route": "Delhi->Goa",
        "flight_date": datetime.date(2026, 9, 23),
        "sched_dep": datetime.time(18, 40),
        "status": "Cancelled",
        "delay_minutes": None,
        "new_dep": None,
        "cause": "operational reasons",
    },
    # Booking 2 — Priya return (Unaffected; flight_no intentionally NULL)
    {
        "pnr": "SK4821X",
        "customer_email": "priya.nair@example.com",
        "segment_label": "return",
        "flight_no": None,          # NOT provided — do not invent
        "route": "Goa->Delhi",
        "flight_date": datetime.date(2026, 9, 25),
        "sched_dep": datetime.time(16, 20),
        "status": "Unaffected",
        "delay_minutes": None,
        "new_dep": None,
        "cause": None,
    },
    # Booking 3 — Arvind outbound (Delayed 4h)
    {
        "pnr": "TR1190B",
        "customer_email": "arvind.kulkarni@example.com",
        "segment_label": "outbound",
        "flight_no": "SK-118",
        "route": "Mumbai->Bengaluru",
        "flight_date": datetime.date(2026, 9, 23),
        "sched_dep": datetime.time(7, 10),
        "status": "Delayed 4h",
        "delay_minutes": 240,
        "new_dep": datetime.time(11, 10),
        "cause": None,              # NOT provided — do not invent
    },
    # Booking 4 — Meher outbound (Delayed 6h)
    {
        "pnr": "WL7742",
        "customer_email": "meher.kaur@example.com",
        "segment_label": "outbound",
        "flight_no": "SK-305",
        "route": "Delhi->Hyderabad",
        "flight_date": datetime.date(2026, 9, 23),
        "sched_dep": datetime.time(14, 0),
        "status": "Delayed 6h",
        "delay_minutes": 360,
        "new_dep": datetime.time(20, 0),
        "cause": None,              # NOT provided — do not invent
    },
]


# ---------------------------------------------------------------------------
# Public seed function
# ---------------------------------------------------------------------------

def seed(db: Session) -> None:
    """Insert seed data if not already present. Idempotent."""

    # --- Customers ---
    email_to_customer: dict[str, Customer] = {}
    for data in CUSTOMERS_SEED:
        existing = db.query(Customer).filter_by(email=data["email"]).first()
        if existing is None:
            customer = Customer(
                name=data["name"],
                tier=data["tier"],
                email=data["email"],
                phone_masked=data["phone_masked"],
                flights_12m=data["flights_12m"],
                prior_complaints=data["prior_complaints"],
                complaint_note=data["complaint_note"],
            )
            db.add(customer)
            db.flush()  # populate customer.id before referencing it below
            email_to_customer[data["email"]] = customer
        else:
            email_to_customer[data["email"]] = existing

    # --- Bookings ---
    for data in BOOKINGS_SEED:
        existing = (
            db.query(Booking)
            .filter_by(pnr=data["pnr"], segment_label=data["segment_label"])
            .first()
        )
        if existing is None:
            customer = email_to_customer[data["customer_email"]]
            booking = Booking(
                pnr=data["pnr"],
                customer_id=customer.id,
                segment_label=data["segment_label"],
                flight_no=data["flight_no"],
                route=data["route"],
                flight_date=data["flight_date"],
                sched_dep=data["sched_dep"],
                status=data["status"],
                delay_minutes=data["delay_minutes"],
                new_dep=data["new_dep"],
                cause=data["cause"],
            )
            db.add(booking)

    db.commit()


seed_data = seed
