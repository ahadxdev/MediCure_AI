import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship
from backend.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255), nullable=True, index=True)
    strength = Column(String(100), nullable=False)
    dosage_form = Column(String(100), nullable=False)
    pack_size = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    inventory = relationship("InventoryRecord", back_populates="medicine", uselist=False, cascade="all, delete-orphan")
    sales_records = relationship("SalesRecord", back_populates="medicine", cascade="all, delete-orphan")
    quotation_requests = relationship("QuotationRequest", back_populates="medicine")


class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    medicine_id = Column(String(36), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    usable_stock = Column(Float, nullable=False, default=0.0)
    reorder_level = Column(Float, nullable=False, default=0.0)
    last_counted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("usable_stock >= 0", name="chk_usable_stock_non_negative"),
        CheckConstraint("reorder_level >= 0", name="chk_reorder_level_non_negative"),
    )

    # Relationship
    medicine = relationship("Medicine", back_populates="inventory")


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    medicine_id = Column(String(36), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    quantity_dispensed = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity_dispensed >= 0", name="chk_qty_dispensed_non_negative"),
    )

    # Relationship
    medicine = relationship("Medicine", back_populates="sales_records")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=True)
    default_lead_time_days = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    quotations = relationship("Quotation", back_populates="supplier")


class QuotationRequest(Base):
    __tablename__ = "quotation_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    medicine_id = Column(String(36), ForeignKey("medicines.id"), nullable=False, index=True)
    required_quantity = Column(Float, nullable=False)
    required_by_date = Column(Date, nullable=True)
    delivery_location = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="draft", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("required_quantity > 0", name="chk_req_quantity_positive"),
    )

    # Relationships
    medicine = relationship("Medicine", back_populates="quotation_requests")
    quotations = relationship("Quotation", back_populates="request")


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    request_id = Column(String(36), ForeignKey("quotation_requests.id"), nullable=True, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=True, index=True)
    raw_email_body = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, default="PKR")
    price_unit = Column(String(50), nullable=True)
    quoted_quantity = Column(Float, nullable=True)
    minimum_order_quantity = Column(Float, nullable=True)
    delivery_days = Column(Float, nullable=True)
    delivery_fee = Column(Float, nullable=True, default=0.0)
    payment_terms = Column(String(100), nullable=True)
    valid_until = Column(String(50), nullable=True)
    review_status = Column(String(50), nullable=False, default="pending", index=True)
    warning_flags = Column(Text, nullable=True)  # JSON-encoded array or comma-separated
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    request = relationship("QuotationRequest", back_populates="quotations")
    supplier = relationship("Supplier", back_populates="quotations")
    purchase_orders = relationship("PurchaseOrder", back_populates="quotation")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quotation_id = Column(String(36), ForeignKey("quotations.id"), nullable=True, index=True)
    po_number = Column(String(50), nullable=False, unique=True, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="draft", index=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    quotation = relationship("Quotation", back_populates="purchase_orders")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    payload = Column(Text, nullable=True)  # JSON-encoded payload
