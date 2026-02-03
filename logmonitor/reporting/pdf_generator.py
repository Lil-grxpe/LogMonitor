"""PDF report generation using ReportLab."""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak, HRFlowable
)
from reportlab.lib.units import cm, inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart


class PDFReportGenerator:
    """PDF report generator using ReportLab."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._init_styles()
    
    def _init_styles(self):
        self.styles.add(ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        self.styles.add(ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7f8c8d')
        ))
        
        self.styles.add(ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        ))
    
    def generate(self, output_file: str, statistics: Dict[str, Any], alerts: List[Dict]):
        pdf_path = Path(output_file)
        pdf_path.parent.mkdir(exist_ok=True, parents=True)
        
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        story.extend(self._create_title_page())
        story.append(PageBreak())
        
        story.extend(self._create_summary_section(statistics))
        story.append(Spacer(1, 20))
        
        if statistics.get('alerts_by_severity'):
            story.extend(self._create_severity_chart(statistics['alerts_by_severity']))
            story.append(Spacer(1, 20))
        
        if alerts:
            story.extend(self._create_alerts_section(alerts))
        
        doc.build(story)
        return str(pdf_path)
    
    def _create_title_page(self) -> List:
        elements = []
        
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("LogMonitor", self.styles['CustomTitle']))
        elements.append(Paragraph("Security Analysis Report", self.styles['CustomSubtitle']))
        
        elements.append(Spacer(1, 50))
        
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated: {date_str}", self.styles['CustomSubtitle']))
        
        return elements
    
    def _create_summary_section(self, statistics: Dict[str, Any]) -> List:
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#3498db')))
        
        data = [
            ['Metric', 'Value'],
            ['Total Logs', str(statistics.get('total_logs', 0))],
            ['Total Alerts', str(statistics.get('total_alerts', 0))],
        ]
        
        for severity, count in statistics.get('alerts_by_severity', {}).items():
            data.append([f'{severity.upper()} Alerts', str(count)])
        
        table = Table(data, colWidths=[10*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_severity_chart(self, alerts_by_severity: Dict[str, int]) -> List:
        elements = []
        
        elements.append(Paragraph("Alert Distribution", self.styles['SectionTitle']))
        
        if not alerts_by_severity:
            elements.append(Paragraph("No alerts to display", self.styles['Normal']))
            return elements
        
        drawing = Drawing(400, 200)
        
        pie = Pie()
        pie.x = 100
        pie.y = 25
        pie.width = 150
        pie.height = 150
        pie.data = list(alerts_by_severity.values())
        pie.labels = list(alerts_by_severity.keys())
        
        severity_colors = {
            'low': colors.HexColor('#27ae60'),
            'medium': colors.HexColor('#f39c12'),
            'high': colors.HexColor('#e67e22'),
            'critical': colors.HexColor('#e74c3c'),
            'emergency': colors.HexColor('#9b59b6')
        }
        
        pie.slices.strokeWidth = 0.5
        for i, severity in enumerate(alerts_by_severity.keys()):
            pie.slices[i].fillColor = severity_colors.get(severity, colors.gray)
        
        drawing.add(pie)
        elements.append(drawing)
        
        return elements
    
    def _create_alerts_section(self, alerts: List[Dict]) -> List:
        elements = []
        
        elements.append(Paragraph("Recent Alerts", self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e74c3c')))
        
        max_alerts = 20
        alerts_to_show = alerts[:max_alerts]
        
        data = [['Timestamp', 'Severity', 'Rule', 'Description']]
        
        for alert in alerts_to_show:
            timestamp = alert.get('timestamp', 'N/A')
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1][:8]
            
            description = alert.get('description', 'N/A')
            if len(description) > 50:
                description = description[:47] + '...'
            
            data.append([
                timestamp,
                alert.get('severity', 'N/A').upper(),
                alert.get('rule_name', 'N/A'),
                description
            ])
        
        table = Table(data, colWidths=[3.5*cm, 2.5*cm, 4*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        severity_row_colors = {
            'LOW': colors.HexColor('#d4edda'),
            'MEDIUM': colors.HexColor('#fff3cd'),
            'HIGH': colors.HexColor('#ffeeba'),
            'CRITICAL': colors.HexColor('#f8d7da'),
            'EMERGENCY': colors.HexColor('#f5c6cb')
        }
        
        for i, row in enumerate(data[1:], 1):
            severity = row[1]
            if severity in severity_row_colors:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), severity_row_colors[severity])
                ]))
        
        elements.append(table)
        
        if len(alerts) > max_alerts:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"... and {len(alerts) - max_alerts} more alerts",
                self.styles['Normal']
            ))
        
        return elements
