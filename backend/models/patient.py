"""SQLAlchemy models for Patients and User-Patient access permissions."""

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.document import Document


class Patient(Base):
    """Synthetic or de-identified patient record entity."""

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    mrn_synthetic: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    primary_condition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    permissions: Mapped[list["UserPatientPermission"]] = relationship(
        "UserPatientPermission", back_populates="patient", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Patient {self.mrn_synthetic} - {self.first_name} {self.last_name}>"


class UserPatientPermission(Base):
    """Explicit mapping between a user and an authorized patient dossier."""

    __tablename__ = "user_patient_permissions"
    __table_args__ = (UniqueConstraint("user_id", "patient_id", name="uq_user_patient"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="read"
    )  # read, write, admin
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission User:{self.user_id} -> Patient:{self.patient_id} ({self.permission_level})>"
