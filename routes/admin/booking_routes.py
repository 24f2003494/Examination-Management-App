
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot
from models.examination import Examination
from models.user import User
from utils.decorators import role_required


admin_booking_bp = Blueprint(
    "admin_bookings",
    __name__,
    url_prefix="/admin/bookings"
)


@admin_booking_bp.route("/")
@role_required("admin")
def booking_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    examination_id = request.args.get("examination_id", type=int)

    query = (
        Booking.query
        .join(User, Booking.student_id == User.id)
        .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
        .join(Examination, ExaminationSlot.examination_id == Examination.id)
    )

    if search:
        if search.isdigit():
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.id == int(search),
                    Booking.id == int(search)
                )
            )
        else:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )

    if status in ("booked", "cancelled"):
        query = query.filter(Booking.status == status)

    if examination_id:
        query = query.filter(
            ExaminationSlot.examination_id == examination_id
        )

    bookings = query.order_by(Booking.booking_date.desc()).all()

    examinations = Examination.query.order_by(
        Examination.exam_name
    ).all()

    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        examinations=examinations,
        search=search,
        selected_status=status,
        selected_examination=examination_id
    )


@admin_booking_bp.route("/reschedule/<int:booking_id>", methods=["GET", "POST"])
@role_required("admin")
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.status != "booked":
        flash("Only active bookings can be rescheduled.", "danger")
        return redirect(url_for("admin_bookings.booking_list"))

    current_slot = booking.slot

    if request.method == "POST":
        new_slot_id = request.form.get("slot_id", type=int)
        new_slot = db.session.get(ExaminationSlot, new_slot_id)

        if not new_slot:
            flash("The selected slot does not exist.", "danger")
            return redirect(
                url_for("admin_bookings.reschedule_booking",
                        booking_id=booking.id)
            )

        if new_slot.examination_id != current_slot.examination_id:
            flash("A booking can only be moved to another slot of the same examination.", "danger")
            return redirect(
                url_for("admin_bookings.reschedule_booking",
                        booking_id=booking.id)
            )

        if new_slot.id != current_slot.id:
            active_bookings = Booking.query.filter_by(
                slot_id=new_slot.id,
                status="booked"
            ).count()

            if new_slot.status != "available" or active_bookings >= new_slot.capacity:
                flash("The selected slot is full or unavailable.", "danger")
                return redirect(
                    url_for("admin_bookings.reschedule_booking",
                            booking_id=booking.id)
                )

        try:
            old_slot = current_slot

            booking.slot_id = new_slot.id

            if new_slot.id != old_slot.id:
                new_count = Booking.query.filter_by(
                    slot_id=new_slot.id,
                    status="booked"
                ).count()

                new_slot.status = (
                    "full" if new_count >= new_slot.capacity else "available"
                )

                old_count = Booking.query.filter_by(
                    slot_id=old_slot.id,
                    status="booked"
                ).count()

                old_slot.status = (
                    "full" if old_count >= old_slot.capacity else "available"
                )

            db.session.commit()
            flash("Booking rescheduled successfully.", "success")
            return redirect(url_for("admin_bookings.booking_list"))

        except Exception:
            db.session.rollback()
            flash("Unable to reschedule this booking.", "danger")

    available_slots = ExaminationSlot.query.filter_by(
        examination_id=current_slot.examination_id,
        status="available"
    ).order_by(
        ExaminationSlot.slot_date,
        ExaminationSlot.start_time
    ).all()

    return render_template(
        "admin/reschedule_booking.html",
        booking=booking,
        available_slots=available_slots
    )
