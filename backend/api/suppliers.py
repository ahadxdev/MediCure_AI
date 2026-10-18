from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import require_api_key, require_api_key_strict
from backend.models.entities import Quotation, Supplier
from backend.schemas.suppliers import SupplierCreate, SupplierResponse

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get(
    "",
    response_model=list[SupplierResponse],
    dependencies=[Depends(require_api_key_strict)],
)
def list_suppliers(db: Annotated[Session, Depends(get_db)]):
    return db.query(Supplier).order_by(Supplier.name.asc()).all()


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    dependencies=[Depends(require_api_key_strict)],
)
def get_supplier(supplier_id: str, db: Annotated[Session, Depends(get_db)]):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[str, Depends(require_api_key)]):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A supplier with this email already exists",
        ) from exc
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: str,
    payload: SupplierCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    for field, value in payload.model_dump().items():
        setattr(supplier, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A supplier with this email already exists",
        ) from exc
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, db: Annotated[Session, Depends(get_db)], _: Annotated[str, Depends(require_api_key)]):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    if db.query(Quotation.id).filter(Quotation.supplier_id == supplier_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier cannot be deleted because quotation history references it",
        )

    db.delete(supplier)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
