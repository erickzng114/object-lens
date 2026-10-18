"""Token usage per Claude call.

CLAUDE.md asks for a `cost_log` table; until PostgreSQL is wired up this
keeps rows in memory and writes each one to the log so nothing is lost.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger("object_lens.cost")


@dataclass(frozen=True)
class CostRow:
    search_id: str
    call: str
    model: str
    input_tokens: int
    output_tokens: int
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CostLog:
    def __init__(self) -> None:
        self.rows: list[CostRow] = []

    def record(self, search_id: str, call: str, model: str, usage) -> None:
        row = CostRow(search_id, call, model, usage.input_tokens, usage.output_tokens)
        self.rows.append(row)
        log.info("claude call=%s model=%s search=%s in=%d out=%d",
                 call, model, search_id, row.input_tokens, row.output_tokens)
