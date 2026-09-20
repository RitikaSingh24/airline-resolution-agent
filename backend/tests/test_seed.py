"""
Seed tests — verifies exact data values and idempotency.

Uses the in-memory database session provided by conftest.py.
"""
import datetime

import pytest
from sqlalchemy.orm import Session

from db.seed import seed, CUSTOMERS_SEED, BOOKINGS_SEED
from models.customer import Customer
from models.booking import Booking


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def count_customers(db: Session) -> int:
    return db.query(Customer).count()


def count_bookings(db: Session) -> int:
    return db.query(Booking).count()


# ---------------------------------------------------------------------------
# Basic count tests
# ---------------------------------------------------------------------------

class TestSeedCounts:
    def test_customer_count_is_three(self, db: Session):
        seed(db)
        assert count_customers(db) == 3

    def test_booking_count_is_four(self, db: Session):
        seed(db)
        assert count_bookings(db) == 4


# ---------------------------------------------------------------------------
# Customer value tests
# ---------------------------------------------------------------------------

class TestCustomerValues:
    def _get(self, db: Session, email: str) -> Customer:
        c = db.query(Customer).filter_by(email=email).first()
        assert c is not None, f"Customer {email!r} not found"
        return c

    def test_priya_nair_values(self, db: Session):
        seed(db)
        c = self._get(db, "priya.nair@example.com")
        assert c.name == "Priya Nair"
        assert c.tier == "Gold"
        assert c.phone_masked == "+91-98xxxxxxx1"
        assert c.flights_12m == 6
        assert c.prior_complaints == 1
        assert c.complaint_note == "delayed baggage, resolved w/ voucher"

    def test_arvind_kulkarni_values(self, db: Session):
        seed(db)
        c = self._get(db, "arvind.kulkarni@example.com")
        assert c.name == "Arvind Kulkarni"
        assert c.tier == "Silver"
        assert c.phone_masked == "+91-98xxxxxxx2"
        assert c.flights_12m == 3
        assert c.prior_complaints == 0
        assert c.complaint_note is None

    def test_meher_kaur_values(self, db: Session):
        seed(db)
        c = self._get(db, "meher.kaur@example.com")
        assert c.name == "Meher Kaur"
        assert c.tier == "Platinum"
        assert c.phone_masked == "+91-98xxxxxxx3"
        assert c.flights_12m == 10
        assert c.prior_complaints == 1
        assert c.complaint_note == "overbooking, resolved w/ tier upgrade"


# ---------------------------------------------------------------------------
# Booking value tests
# ---------------------------------------------------------------------------

class TestBookingValues:
    def _get(self, db: Session, pnr: str, segment: str) -> Booking:
        b = db.query(Booking).filter_by(pnr=pnr, segment_label=segment).first()
        assert b is not None, f"Booking {pnr!r}/{segment!r} not found"
        return b

    def test_priya_outbound_is_cancelled(self, db: Session):
        seed(db)
        b = self._get(db, "SK4821X", "outbound")
        assert b.status == "Cancelled"
        assert b.flight_no == "SK-204"
        assert b.route == "Delhi->Goa"
        assert b.flight_date == datetime.date(2026, 9, 23)
        assert b.sched_dep == datetime.time(18, 40)
        assert b.delay_minutes is None
        assert b.new_dep is None
        assert b.cause == "operational reasons"

    def test_priya_return_flight_no_is_null(self, db: Session):
        """The return flight number was not provided; must remain NULL."""
        seed(db)
        b = self._get(db, "SK4821X", "return")
        assert b.flight_no is None
        assert b.status == "Unaffected"
        assert b.route == "Goa->Delhi"
        assert b.flight_date == datetime.date(2026, 9, 25)
        assert b.sched_dep == datetime.time(16, 20)
        assert b.delay_minutes is None
        assert b.new_dep is None
        assert b.cause is None

    def test_arvind_delay_240_minutes(self, db: Session):
        seed(db)
        b = self._get(db, "TR1190B", "outbound")
        assert b.status == "Delayed 4h"
        assert b.delay_minutes == 240
        assert b.new_dep == datetime.time(11, 10)
        assert b.cause is None

    def test_meher_delay_360_minutes(self, db: Session):
        seed(db)
        b = self._get(db, "WL7742", "outbound")
        assert b.status == "Delayed 6h"
        assert b.delay_minutes == 360
        assert b.new_dep == datetime.time(20, 0)
        assert b.cause is None


# ---------------------------------------------------------------------------
# Idempotency tests
# ---------------------------------------------------------------------------

class TestSeedIdempotency:
    def test_running_seed_twice_keeps_three_customers(self, db: Session):
        seed(db)
        seed(db)
        assert count_customers(db) == 3

    def test_running_seed_twice_keeps_four_bookings(self, db: Session):
        seed(db)
        seed(db)
        assert count_bookings(db) == 4

    def test_no_duplicate_customers_after_double_seed(self, db: Session):
        seed(db)
        seed(db)
        emails = [row.email for row in db.query(Customer).all()]
        assert len(emails) == len(set(emails)), "Duplicate customer emails found"

    def test_no_duplicate_bookings_after_double_seed(self, db: Session):
        seed(db)
        seed(db)
        keys = [
            (row.pnr, row.segment_label) for row in db.query(Booking).all()
        ]
        assert len(keys) == len(set(keys)), "Duplicate booking (pnr, segment_label) pairs found"
