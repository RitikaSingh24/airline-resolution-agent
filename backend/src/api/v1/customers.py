"""Customer and customer-booking API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.exceptions import NotFoundException
from db.session import get_db
import repositories.booking_repo as booking_repo
import repositories.customer_repo as customer_repo
from schemas.booking import BookingResponse
from schemas.customer import CustomerResponse

router = APIRouter(tags=["Customers"])


@router.get(
    "/customers",
    response_model=list[CustomerResponse],
    summary="List Customers",
    description="Retrieve list of all airline customers.",
)
def list_customers(db: Session = Depends(get_db)) -> list[CustomerResponse]:
    """Retrieves all customer records."""
    return customer_repo.list_all(db)


@router.get(
    "/customers/{customer_id}/bookings",
    response_model=list[BookingResponse],
    summary="Get Customer Bookings",
    description="Retrieve all flight bookings for a specific customer.",
)
def get_customer_bookings(
    customer_id: int, db: Session = Depends(get_db)
) -> list[BookingResponse]:
    """Retrieves bookings for the given customer ID."""
    customer = customer_repo.get_by_id(db, customer_id)
    if not customer:
        raise NotFoundException(message="Customer not found")

    return booking_repo.list_by_customer(db, customer_id)
