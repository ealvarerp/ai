from datetime import datetime

from sqlalchemy import Column, DateTime, MetaData, String, Table, create_engine, insert


class SqlAudit:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.metadata = MetaData()

        self.audit_logs = Table(
            "audit_logs",
            self.metadata,
            Column("id", String, primary_key=True),
            Column("document_id", String, index=True),
            Column("stage", String),
            Column("status", String),
            Column("details", String),
            Column("created_at", DateTime),
        )

        self.metadata.create_all(self.engine)

    def log(
        self,
        document_id: str,
        stage: str,
        status: str,
        details: dict | None = None,
    ) -> None:
        import json
        import uuid

        with self.engine.begin() as conn:
            conn.execute(
                insert(self.audit_logs).values(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    stage=stage,
                    status=status,
                    details=json.dumps(details or {}, default=str),
                    created_at=datetime.utcnow(),
                )
            )
