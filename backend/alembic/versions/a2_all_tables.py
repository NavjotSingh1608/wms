"""All remaining WMS tables

Revision ID: a2_all_tables
Revises: a1_initial
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a2_all_tables"
down_revision: Union[str, None] = "a1_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ──────────────────────────────────────────────────────
    grn_status = sa.Enum(
        "QUARANTINE", "UNDER_TEST", "APPROVED", "REJECTED",
        "QUARANTINE_RETESTING", "BLOCKED_PENDING_QC_RELEASE",
        "FULLY_DISPENSED", "APPROVED_BP_USP",
        name="grn_status",
    )
    grn_status.create(op.get_bind(), checkfirst=True)

    qc_decision_type = sa.Enum("APPROVED", "REJECTED", name="qc_decision_type")
    qc_decision_type.create(op.get_bind(), checkfirst=True)

    ledger_txn_type = sa.Enum("IN", "OUT", "TRANSFER_OUT", "TRANSFER_IN", name="ledger_txn_type")
    ledger_txn_type.create(op.get_bind(), checkfirst=True)

    ledger_stage = sa.Enum(
        "QUARANTINE", "UNDER_TEST", "APPROVED", "REJECTED",
        "QUARANTINE_RETESTING", "FINISHED_GOODS", "DISPATCHED",
        name="ledger_stage",
    )
    ledger_stage.create(op.get_bind(), checkfirst=True)

    label_type = sa.Enum("QUARANTINE", "QUARANTINE_RETESTING", "SHIPPER", name="label_type")
    label_type.create(op.get_bind(), checkfirst=True)

    retest_outcome = sa.Enum("APPROVED", "REJECTED", name="retest_outcome")
    retest_outcome.create(op.get_bind(), checkfirst=True)

    transfer_status = sa.Enum("PENDING", "BLOCKED_PENDING_QC_RELEASE", "APPROVED", "REJECTED", name="transfer_status")
    transfer_status.create(op.get_bind(), checkfirst=True)

    fg_status = sa.Enum(
        "PENDING_QA_VERIFICATION", "QA_VERIFIED", "QA_APPROVED",
        "QA_REJECTED", "WH_RECEIVED", "DISPATCHED",
        name="fg_status",
    )
    fg_status.create(op.get_bind(), checkfirst=True)

    notification_type = sa.Enum(
        "RETEST_ALERT", "EXPIRY_ALERT", "LABEL_REPRINT_REQUEST",
        "GRADE_TRANSFER_REQUEST", "FG_PENDING_QA",
        name="notification_type",
    )
    notification_type.create(op.get_bind(), checkfirst=True)

    # ── materials ───────────────────────────────────────────────────────
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("item_code", sa.String(50), nullable=False, unique=True),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("grade", sa.String(20), nullable=True),
        sa.Column("unit_of_measure", sa.String(20), nullable=False),
        sa.Column("specifications", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── grn ─────────────────────────────────────────────────────────────
    op.create_table(
        "grn",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_number", sa.String(20), nullable=False, unique=True),
        sa.Column("item_code", sa.String(50), nullable=False),
        sa.Column("batch_no", sa.String(100), nullable=False),
        sa.Column("supplier_name", sa.String(255), nullable=False),
        sa.Column("manufacturer_name", sa.String(255), nullable=False),
        sa.Column("total_recv_qty", sa.Numeric(15, 4), nullable=False),
        sa.Column("container_qty", sa.Numeric(15, 4), nullable=False),
        sa.Column("containers_count", sa.Integer(), nullable=False),
        sa.Column("pack_size_description", sa.String(100), nullable=True),
        sa.Column("unit_of_measure", sa.String(20), nullable=False),
        sa.Column("recv_date", sa.Date(), nullable=False),
        sa.Column("mfg_date", sa.Date(), nullable=False),
        sa.Column("exp_date", sa.Date(), nullable=False),
        sa.Column("status", grn_status, nullable=False, server_default="QUARANTINE"),
        sa.Column("material_issue_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rack_no", sa.String(50), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("grade", sa.String(20), nullable=True),
        sa.Column("revised_from_grn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("balance_qty", sa.Numeric(15, 4), nullable=False),
        sa.Column("retest_alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("retest_alert_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("retesting_date", sa.Date(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["item_code"], ["materials.item_code"]),
        sa.ForeignKeyConstraint(["revised_from_grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index("ix_grn_item_code", "grn", ["item_code"])
    op.create_index("ix_grn_status", "grn", ["status"])
    op.create_index("ix_grn_exp_date", "grn", ["exp_date"])
    op.create_index("ix_grn_batch_no", "grn", ["batch_no"])

    # ── finished_goods (created before stock_ledger due to FK) ──────────
    op.create_table(
        "finished_goods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("product_code", sa.String(50), nullable=True),
        sa.Column("batch_no", sa.String(100), nullable=False),
        sa.Column("mfg_date", sa.Date(), nullable=False),
        sa.Column("exp_date", sa.Date(), nullable=False),
        sa.Column("total_qty", sa.Numeric(15, 4), nullable=False),
        sa.Column("unit_of_measure", sa.String(20), nullable=False),
        sa.Column("status", fg_status, nullable=False, server_default="PENDING_QA_VERIFICATION"),
        sa.Column("sent_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("qa_verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("qa_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("qa_approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("qa_approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("qa_rejection_reason", sa.Text(), nullable=True),
        sa.Column("wh_received_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("wh_received_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dispatched_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dispatched_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("revised_from_fg_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revised_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["sent_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["qa_verified_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["qa_approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["wh_received_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["dispatched_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["revised_from_fg_id"], ["finished_goods.id"]),
    )

    # ── qc_sampling ─────────────────────────────────────────────────────
    op.create_table(
        "qc_sampling",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ar_number", sa.String(50), nullable=False, unique=True),
        sa.Column("sample_qty", sa.Numeric(15, 4), nullable=False),
        sa.Column("sampled_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sample_date", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["sampled_by"], ["users.id"]),
    )

    # ── qc_decisions ────────────────────────────────────────────────────
    op.create_table(
        "qc_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sampling_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", qc_decision_type, nullable=False),
        sa.Column("test_remarks", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("retesting_date", sa.Date(), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decided_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("retest_cycle_no", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["sampling_id"], ["qc_sampling.id"]),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.CheckConstraint(
            "decision != 'REJECTED' OR rejection_reason IS NOT NULL",
            name="ck_qc_decisions_rejected_reason",
        ),
        sa.CheckConstraint(
            "decision != 'APPROVED' OR retesting_date IS NOT NULL",
            name="ck_qc_decisions_approved_retest",
        ),
    )

    # ── dispensing ──────────────────────────────────────────────────────
    op.create_table(
        "dispensing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("product_batch_no", sa.String(100), nullable=False),
        sa.Column("qty_issued", sa.Numeric(15, 4), nullable=False),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issued_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("balance_qty_after", sa.Numeric(15, 4), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["issued_by"], ["users.id"]),
    )
    op.create_index("ix_dispensing_grn_id", "dispensing", ["grn_id"])

    # ── qr_labels ───────────────────────────────────────────────────────
    op.create_table(
        "qr_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fg_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label_type", label_type, nullable=False),
        sa.Column("qr_data", sa.Text(), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reprint_authorized_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["reprint_authorized_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
    )
    op.create_index("ix_qr_labels_grn_current", "qr_labels", ["grn_id", "is_current"])

    # ── stock_ledger ────────────────────────────────────────────────────
    op.create_table(
        "stock_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("item_code", sa.String(50), nullable=False),
        sa.Column("batch_no", sa.String(100), nullable=False),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fg_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stage", ledger_stage, nullable=False),
        sa.Column("txn_type", ledger_txn_type, nullable=False),
        sa.Column("qty_change", sa.Numeric(15, 4), nullable=False),
        sa.Column("balance_after", sa.Numeric(15, 4), nullable=False),
        sa.Column("ref_type", sa.String(50), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["item_code"], ["materials.item_code"]),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["fg_id"], ["finished_goods.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
    )
    op.create_index("ix_stock_ledger_item_batch", "stock_ledger", ["item_code", "batch_no"])
    op.create_index("ix_stock_ledger_grn_id", "stock_ledger", ["grn_id"])
    op.create_index("ix_stock_ledger_created_at", "stock_ledger", ["created_at"])

    # ── retesting_cycles ────────────────────────────────────────────────
    op.create_table(
        "retesting_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cycle_no", sa.Integer(), nullable=False),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("new_label_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retest_alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("retest_alert_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("outcome", retest_outcome, nullable=True),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["new_label_id"], ["qr_labels.id"]),
    )

    # ── grade_transfers ─────────────────────────────────────────────────
    op.create_table(
        "grade_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_item_code", sa.String(50), nullable=False),
        sa.Column("to_item_code", sa.String(50), nullable=False),
        sa.Column("ar_number_ref", sa.String(50), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rejection_remarks", sa.Text(), nullable=True),
        sa.Column("status", transfer_status, nullable=False, server_default="PENDING"),
        sa.Column("new_grn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"]),
        sa.ForeignKeyConstraint(["from_item_code"], ["materials.item_code"]),
        sa.ForeignKeyConstraint(["to_item_code"], ["materials.item_code"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["new_grn_id"], ["grn.id"]),
    )

    # ── shipper_labels ──────────────────────────────────────────────────
    op.create_table(
        "shipper_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("fg_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("batch_no", sa.String(100), nullable=False),
        sa.Column("mfg_date", sa.Date(), nullable=False),
        sa.Column("exp_date", sa.Date(), nullable=False),
        sa.Column("net_weight", sa.Numeric(10, 4), nullable=True),
        sa.Column("gross_weight", sa.Numeric(10, 4), nullable=True),
        sa.Column("quantity", sa.Numeric(15, 4), nullable=True),
        sa.Column("carton_no", sa.String(50), nullable=True),
        sa.Column("barcode_data", sa.Text(), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=True),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["fg_id"], ["finished_goods.id"]),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
    )

    # ── notifications ───────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ref_type", sa.String(50), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read"])

    # ── audit_logs ──────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("old_values", postgresql.JSONB(), nullable=True),
        sa.Column("new_values", postgresql.JSONB(), nullable=True),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("performed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_performed_by", "audit_logs", ["performed_by"])
    op.create_index("ix_audit_logs_performed_at", "audit_logs", ["performed_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("shipper_labels")
    op.drop_table("grade_transfers")
    op.drop_table("retesting_cycles")
    op.drop_table("stock_ledger")
    op.drop_table("qr_labels")
    op.drop_table("dispensing")
    op.drop_table("qc_decisions")
    op.drop_table("qc_sampling")
    op.drop_table("finished_goods")
    op.drop_table("grn")
    op.drop_table("materials")

    sa.Enum(name="notification_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="fg_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transfer_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="retest_outcome").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="label_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="ledger_stage").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="ledger_txn_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="qc_decision_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="grn_status").drop(op.get_bind(), checkfirst=True)
