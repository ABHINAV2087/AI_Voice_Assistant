import datetime as dt
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Appointment, get_db, init_db

init_db()


class AppointmentRequest(BaseModel):
    patient_name: str
    reason: str | None = None
    start_time: dt.datetime


class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    reason: str | None
    start_time: dt.datetime
    canceled: bool
    created_at: dt.datetime


class CancelAppointmentRequest(BaseModel):
    patient_name: str
    date: dt.date


class CancelAppointmentResponse(BaseModel):
    canceled_count: int


class ListAppointmentRequest(BaseModel):
    date: dt.date


app = FastAPI(title="Voice Agent Appointment Backend", version="1.0.0")

allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allowed_origins == ["*"] else allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "service": "voice-agent"}


@app.get("/health")
@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/schedule_appointment/", response_model=AppointmentResponse)
def schedule_appointment(request: AppointmentRequest, db: Session = Depends(get_db)) -> AppointmentResponse:
    new_appointment = Appointment(
        patient_name=request.patient_name,
        reason=request.reason,
        start_time=request.start_time,
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return AppointmentResponse(
        id=new_appointment.id,
        patient_name=new_appointment.patient_name,
        reason=new_appointment.reason,
        start_time=new_appointment.start_time,
        canceled=new_appointment.canceled,
        created_at=new_appointment.created_at,
    )


@app.post("/cancel_appointment/", response_model=CancelAppointmentResponse)
def cancel_appointment(request: CancelAppointmentRequest, db: Session = Depends(get_db)) -> CancelAppointmentResponse:
    start_dt = dt.datetime.combine(request.date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)

    result = db.execute(
        select(Appointment)
        .where(Appointment.patient_name == request.patient_name)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time < end_dt)
        .where(Appointment.canceled == False)
    )

    appointments = result.scalars().all()
    if not appointments:
        raise HTTPException(status_code=404, detail="No matching appointment for the details found in our system")

    for appointment in appointments:
        appointment.canceled = True

    db.commit()
    return CancelAppointmentResponse(canceled_count=len(appointments))


@app.post("/list_appointments/", response_model=list[AppointmentResponse])
def list_appointments(request: ListAppointmentRequest, db: Session = Depends(get_db)) -> list[AppointmentResponse]:
    start_dt = dt.datetime.combine(request.date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)

    result = db.execute(
        select(Appointment)
        .where(Appointment.canceled == False)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time < end_dt)
        .order_by(Appointment.start_time.asc())
    )
    booked_appointments: list[AppointmentResponse] = []
    for appointment in result.scalars().all():
        booked_appointments.append(
            AppointmentResponse(
                id=appointment.id,
                patient_name=appointment.patient_name,
                reason=appointment.reason,
                start_time=appointment.start_time,
                canceled=appointment.canceled,
                created_at=appointment.created_at,
            )
        )

    return booked_appointments


class DashboardStatsResponse(BaseModel):
    total_bookings: int
    active_bookings: int
    canceled_bookings: int
    cancellation_rate: float
    reasons: dict[str, int]
    hourly_distribution: dict[int, int]
    daily_distribution: dict[str, int]


@app.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStatsResponse:
    result = db.execute(select(Appointment))
    appointments = result.scalars().all()
    
    total = len(appointments)
    active = sum(1 for a in appointments if not a.canceled)
    canceled = sum(1 for a in appointments if a.canceled)
    rate = (canceled / total * 100) if total > 0 else 0.0

    reasons: dict[str, int] = {}
    for a in appointments:
        r = (a.reason or "").strip() or "General Consultation"
        reasons[r] = reasons.get(r, 0) + 1

    hourly: dict[int, int] = {}
    for a in appointments:
        h = a.start_time.hour
        hourly[h] = hourly.get(h, 0) + 1

    daily: dict[str, int] = {}
    for a in appointments:
        d = a.start_time.date().isoformat()
        daily[d] = daily.get(d, 0) + 1

    return DashboardStatsResponse(
        total_bookings=total,
        active_bookings=active,
        canceled_bookings=canceled,
        cancellation_rate=round(rate, 2),
        reasons=reasons,
        hourly_distribution=hourly,
        daily_distribution=daily,
    )


@app.get("/dashboard/appointments", response_model=list[AppointmentResponse])
def get_dashboard_appointments(
    patient_name: str | None = None,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
    include_canceled: bool = True,
    db: Session = Depends(get_db)
) -> list[AppointmentResponse]:
    stmt = select(Appointment)
    if not include_canceled:
        stmt = stmt.where(Appointment.canceled == False)
    if patient_name:
        stmt = stmt.where(Appointment.patient_name.ilike(f"%{patient_name.strip()}%"))
    if start_date:
        start_dt = dt.datetime.combine(start_date, dt.time.min)
        stmt = stmt.where(Appointment.start_time >= start_dt)
    if end_date:
        end_dt = dt.datetime.combine(end_date, dt.time.max)
        stmt = stmt.where(Appointment.start_time <= end_dt)
    
    stmt = stmt.order_by(Appointment.start_time.asc())
    result = db.execute(stmt)
    
    return [
        AppointmentResponse(
            id=a.id,
            patient_name=a.patient_name,
            reason=a.reason,
            start_time=a.start_time,
            canceled=a.canceled,
            created_at=a.created_at,
        )
        for a in result.scalars().all()
    ]


@app.post("/dashboard/cancel_appointment/{appointment_id}")
def cancel_appointment_by_id(appointment_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    appointment = db.execute(select(Appointment).where(Appointment.id == appointment_id)).scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.canceled = True
    db.commit()
    return {"status": "success", "message": f"Appointment {appointment_id} canceled successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="0.0.0.0", port=int(os.getenv("PORT", "4444")), reload=False)