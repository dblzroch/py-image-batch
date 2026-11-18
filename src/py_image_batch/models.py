"""Domain models for py-image-batch."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class ProcessingResult:
    """Result of processing a single image."""

    source: Path
    destination: Path
    status: str  # "ok" or "error"
    bytes_before: int = 0
    bytes_after: int = 0
    error: str | None = None

    @property
    def savings(self) -> int:
        return self.bytes_before - self.bytes_after

    @property
    def savings_percent(self) -> float:
        if self.bytes_before == 0:
            return 0.0
        return (self.savings / self.bytes_before) * 100


@dataclass
class BatchResult:
    """Outcome of a batch run."""

    input_folder: Path
    output_folder: Path
    total: int = 0
    processed: int = 0
    errors: int = 0
    bytes_before_total: int = 0
    bytes_after_total: int = 0
    results: list[ProcessingResult] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_savings(self) -> int:
        return self.bytes_before_total - self.bytes_after_total

    @property
    def total_savings_percent(self) -> float:
        if self.bytes_before_total == 0:
            return 0.0
        return (self.total_savings / self.bytes_before_total) * 100

    def to_html(self) -> str:
        """Render the batch result as an HTML report."""
        rows = []
        for r in self.results:
            status_class = "ok" if r.status == "ok" else "error"
            rows.append(
                f"<tr class='{status_class}'>"
                f"<td>{r.source.name}</td>"
                f"<td>{r.bytes_before:,}</td>"
                f"<td>{r.bytes_after:,}</td>"
                f"<td>{r.savings_percent:.1f}%</td>"
                f"<td>{r.status}</td>"
                f"<td>{r.error or ''}</td>"
                f"</tr>"
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Image Batch Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; padding: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
  th {{ background: #f4f4f4; }}
  tr.ok {{ color: #0a7; }}
  tr.error {{ color: #a00; }}
  .summary {{ margin-bottom: 1rem; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 0.4rem; }}
  .ok {{ background: #dcfce7; color: #166534; }}
  .error {{ background: #fee2e2; color: #991b1b; }}
</style>
</head>
<body>
  <h1>Image Batch Report</h1>
  <div class="summary">
    <p><strong>Input:</strong> {self.input_folder}</p>
    <p><strong>Output:</strong> {self.output_folder}</p>
    <p><strong>Generated:</strong> {self.generated_at.isoformat()}</p>
    <p><strong>Total:</strong> {self.total} &nbsp;
    <strong>Processed:</strong> {self.processed} &nbsp;
    <strong>Errors:</strong> {self.errors}</p>
    <p><strong>Before:</strong> {self.bytes_before_total:,} bytes &nbsp;
    <strong>After:</strong> {self.bytes_after_total:,} bytes &nbsp;
    <strong>Savings:</strong> {self.total_savings:,} bytes
      ({self.total_savings_percent:.1f}%)</p>
  </div>
  <table>
    <thead>
      <tr><th>File</th><th>Before</th><th>After</th><th>Savings</th><th>Status</th><th>Error</th></tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>"""
