from pydantic import BaseModel
from sqlalchemy import Engine, text


class KnowledgeBaseValidation(BaseModel):
    """Deterministic integrity findings for the control knowledge base."""

    orphan_crosswalks: int
    unreachable_soc2_controls: list[str]

    @property
    def valid(self) -> bool:
        """Return whether every enforced integrity rule passes."""
        return self.orphan_crosswalks == 0 and not self.unreachable_soc2_controls


def validate_kb(engine: Engine) -> KnowledgeBaseValidation:
    """Find orphan mappings and SOC 2 criteria without a NIST path through SCF."""
    orphan_sql = text(
        "SELECT count(*) FROM crosswalks w "
        "LEFT JOIN controls a ON a.id = w.control_a "
        "LEFT JOIN controls b ON b.id = w.control_b "
        "WHERE a.id IS NULL OR b.id IS NULL"
    )
    unreachable_sql = text(
        "WITH soc AS ("
        " SELECT c.id, c.control_code FROM controls c JOIN frameworks f ON f.id = c.framework_id"
        " WHERE f.name = 'SOC 2 TSC' AND c.control_code NOT LIKE '%-POF%'"
        "), reachable AS ("
        " SELECT DISTINCT sw.control_b AS id FROM crosswalks sw"
        " JOIN crosswalks nw ON nw.control_a = sw.control_a"
        " JOIN controls nc ON nc.id = nw.control_b"
        " JOIN frameworks nf ON nf.id = nc.framework_id"
        " WHERE nf.name = 'NIST SP 800-53'"
        ") SELECT control_code FROM soc WHERE id NOT IN (SELECT id FROM reachable)"
        " ORDER BY control_code"
    )
    with engine.connect() as connection:
        return KnowledgeBaseValidation(
            orphan_crosswalks=connection.execute(orphan_sql).scalar_one(),
            unreachable_soc2_controls=list(connection.execute(unreachable_sql).scalars()),
        )
