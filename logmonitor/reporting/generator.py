"""Report generation facade."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from .pdf_generator import PDFReportGenerator
from .csv_exporter import CSVExporter


class ReportGenerator:
    """Unified report generation interface."""
    
    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.get('reporting.output_dir', 'reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, output_file: Optional[str] = None, report_format: str = 'pdf') -> str:
        from logmonitor.storage.database import LogDatabase
        
        db_path = self.config.get('storage.database', 'data/logmonitor.db')
        db = LogDatabase(db_path)
        
        statistics = db.get_statistics()
        alerts = db.get_recent_alerts(limit=500)
        
        db.close()
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = str(self.output_dir / f"report_{timestamp}.{report_format}")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if report_format == 'pdf':
            generator = PDFReportGenerator()
            generator.generate(str(output_path), statistics, alerts)
        elif report_format == 'csv':
            exporter = CSVExporter()
            exporter.export_alerts(str(output_path), alerts)
        else:
            raise ValueError(f"Unsupported format: {report_format}")
        
        return str(output_path)
