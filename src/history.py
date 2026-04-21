"""
Conversation History

In-memory store of per-tab run records (query, timestamp, result, logs),
with JSON export.
"""

import json
import time
from typing import Dict, List, Optional
from collections import deque


class ConversationHistory:
    """
    Stores per-tab run records. FIFO cap of 50 entries total.
    """

    MAX_ENTRIES = 50
    VALID_TABS = ("research", "code", "pipeline")

    def __init__(self, max_entries: int = 50):
        self.max_entries = max_entries
        self._entries: deque = deque(maxlen=max_entries)

    def add(
        self,
        tab: str,
        query: str,
        result_summary: str,
        logs: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict:
        """Add a run record. Returns the stored entry."""
        entry = {
            "tab": tab,
            "query": query,
            "timestamp": time.time(),
            "result_summary": result_summary,
            "logs": logs,
            "model": model,
            "temperature": temperature,
        }
        self._entries.append(entry)
        return entry

    def get_all(self) -> List[Dict]:
        """Return all entries (newest last)."""
        return list(self._entries)

    def get_by_tab(self, tab: str) -> List[Dict]:
        """Return entries filtered by tab."""
        return [e for e in self._entries if e.get("tab") == tab]

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def export_json(self, path: str) -> str:
        """Export all entries to a JSON file. Returns the path."""
        data = self.get_all()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def to_json_string(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.get_all(), indent=2, default=str)

    def format_display(self) -> str:
        """Format history as readable markdown for UI display."""
        entries = self.get_all()
        if not entries:
            return "_No history yet. Run a query from any tab to populate._"

        lines = [f"### Conversation History ({len(entries)} entries)\n"]
        for i, e in enumerate(reversed(entries), 1):
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["timestamp"]))
            q = (e.get("query") or "").strip()
            q_short = (q[:120] + "...") if len(q) > 120 else q
            summary = (e.get("result_summary") or "").strip()
            summary_short = (summary[:200] + "...") if len(summary) > 200 else summary
            model = e.get("model") or "-"
            temp = e.get("temperature")
            temp_str = f"{temp:.1f}" if isinstance(temp, (int, float)) else "-"
            lines.append(
                f"**{i}. [{e['tab']}]** `{ts}` — model=`{model}` temp=`{temp_str}`\n\n"
                f"- **Query:** {q_short}\n"
                f"- **Summary:** {summary_short}\n"
            )
        return "\n".join(lines)
