"""Business logic cho UC27 - Tiếp nhận, xử lý khiếu nại/tranh chấp."""
from datetime import datetime

from app.core.database import get_session
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus
from app.repositories.complaint_repository import ComplaintRepository


class ComplaintError(Exception):
    pass


class ComplaintService:
    def __init__(self):
        self.complaint_repo = ComplaintRepository()

    def submit_complaint(
        self,
        created_by_id: int,
        subject: str,
        description: str,
        booking_id: int | None = None,
        facility_id: int | None = None,
    ) -> Complaint:
        if not subject or not description:
            raise ComplaintError("Vui lòng nhập đầy đủ tiêu đề và nội dung khiếu nại.")
        with get_session() as session:
            complaint = Complaint(
                created_by_id=created_by_id,
                booking_id=booking_id,
                facility_id=facility_id,
                subject=subject,
                description=description,
                status=ComplaintStatus.OPEN,
            )
            self.complaint_repo.add(session, complaint)
            session.expunge(complaint)
            return complaint

    def list_my_complaints(self, user_id: int) -> list[Complaint]:
        with get_session() as session:
            complaints = self.complaint_repo.list_by_user(session, user_id)
            session.expunge_all()
            return complaints

    def list_all_complaints(self, status: ComplaintStatus | None = None) -> list[Complaint]:
        with get_session() as session:
            complaints = self.complaint_repo.list_all(session, status=status)
            session.expunge_all()
            return complaints

    def resolve_complaint(
        self, complaint_id: int, admin_id: int, status: ComplaintStatus, resolution_note: str
    ) -> Complaint:
        if status not in (ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED, ComplaintStatus.IN_PROGRESS):
            raise ComplaintError("Trạng thái xử lý không hợp lệ.")
        with get_session() as session:
            complaint = self.complaint_repo.get_by_id(session, complaint_id)
            if not complaint:
                raise ComplaintError("Không tìm thấy khiếu nại.")

            complaint.status = status
            complaint.resolution_note = resolution_note
            complaint.resolved_by_id = admin_id
            if status in (ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED):
                complaint.resolved_at = datetime.utcnow()

            session.flush()
            session.expunge(complaint)
            return complaint
