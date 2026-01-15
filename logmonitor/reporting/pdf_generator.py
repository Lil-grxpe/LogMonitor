"""
Module de génération de rapports PDF (F4)
Responsable : Camel DADAVI

Ce module génère des rapports PDF avec ReportLab (conforme au cahier des charges)
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class PDFReportGenerator:
    """Générateur de rapports PDF avec ReportLab"""
    
    def __init__(self, output_dir: str):
        """
        Initialise le générateur de rapports
        
        Args:
            output_dir: Répertoire de sortie des rapports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        ))
    
    def generate_report(self, alerts: List[Dict[str, Any]], statistics: Dict[str, Any], 
                       period: str = "last-7-days") -> str:
        """
        Génère un rapport PDF complet
        
        Args:
            alerts: Liste des alertes
            statistics: Statistiques du système
            period: Période couverte par le rapport
        
        Returns:
            Chemin vers le fichier PDF généré
        """
        # Nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logmonitor_report_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        # Créer le document
        doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Construire le contenu
        story = []
        
        # Page de titre
        story.extend(self._build_title_page(period))
        
        # Résumé exécutif
        story.extend(self._build_executive_summary(statistics))
        
        # Alertes par sévérité
        story.extend(self._build_alerts_by_severity(statistics.get('alerts_by_severity', {})))
        
        # Top IPs suspectes
        story.extend(self._build_top_suspicious_ips(statistics.get('top_suspicious_ips', [])))
        
        # Liste des alertes critiques
        story.extend(self._build_critical_alerts_table(alerts))
        
        # Timeline des événements
        story.extend(self._build_timeline(alerts))
        
        # Générer le PDF
        doc.build(story)
        
        return str(filepath)
    
    def _build_title_page(self, period: str) -> List:
        """Construit la page de titre"""
        elements = []
        
        title = Paragraph("Rapport LogMonitor", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        subtitle = Paragraph(f"Période: {period}", self.styles['Normal'])
        elements.append(subtitle)
        
        date_generated = Paragraph(
            f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['Normal']
        )
        elements.append(date_generated)
        elements.append(Spacer(1, 48))
        
        return elements
    
    def _build_executive_summary(self, statistics: Dict[str, Any]) -> List:
        """Construit le résumé exécutif"""
        elements = []
        
        elements.append(Paragraph("Résumé Exécutif", self.styles['SectionTitle']))
        
        summary_data = [
            ["Métrique", "Valeur"],
            ["Total de logs analysés", f"{statistics.get('total_logs', 0):,}"],
            ["Total d'alertes générées", f"{statistics.get('total_alerts', 0):,}"],
            ["Alertes critiques", f"{statistics.get('alerts_by_severity', {}).get('critical', 0):,}"],
            ["Alertes haute sévérité", f"{statistics.get('alerts_by_severity', {}).get('high', 0):,}"],
        ]
        
        table = Table(summary_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_alerts_by_severity(self, alerts_by_severity: Dict[str, int]) -> List:
        """Construit le graphique des alertes par sévérité"""
        elements = []
        
        elements.append(Paragraph("Alertes par Niveau de Sévérité", self.styles['SectionTitle']))
        
        if not alerts_by_severity:
            elements.append(Paragraph("Aucune alerte à afficher", self.styles['Normal']))
            return elements
        
        # Créer un graphique camembert
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        
        pie.data = list(alerts_by_severity.values())
        pie.labels = list(alerts_by_severity.keys())
        
        # Couleurs par sévérité
        color_map = {
            'critical': colors.red,
            'high': colors.orange,
            'medium': colors.yellow,
            'low': colors.green
        }
        pie.slices.strokeWidth = 0.5
        for i, severity in enumerate(alerts_by_severity.keys()):
            pie.slices[i].fillColor = color_map.get(severity, colors.grey)
        
        drawing.add(pie)
        elements.append(drawing)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_top_suspicious_ips(self, top_ips: List[Dict[str, Any]]) -> List:
        """Construit le tableau des IPs suspectes"""
        elements = []
        
        elements.append(Paragraph("Top 10 des IPs Suspectes", self.styles['SectionTitle']))
        
        if not top_ips:
            elements.append(Paragraph("Aucune IP suspecte détectée", self.styles['Normal']))
            return elements
        
        table_data = [["Adresse IP", "Nombre de tentatives"]]
        for ip_data in top_ips[:10]:
            table_data.append([
                ip_data.get('source_ip', 'N/A'),
                str(ip_data.get('count', 0))
            ])
        
        table = Table(table_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffe5e5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_critical_alerts_table(self, alerts: List[Dict[str, Any]]) -> List:
        """Construit le tableau des alertes critiques"""
        elements = []
        
        critical_alerts = [a for a in alerts if a.get('severity') == 'critical' or a.get('severity') == 'high']
        
        elements.append(Paragraph(f"Alertes Critiques ({len(critical_alerts)})", self.styles['SectionTitle']))
        
        if not critical_alerts:
            elements.append(Paragraph("Aucune alerte critique", self.styles['Normal']))
            return elements
        
        table_data = [["Date/Heure", "Règle", "Description"]]
        
        for alert in critical_alerts[:20]:  # Limiter à 20
            timestamp = alert.get('timestamp', 'N/A')
            if 'T' in timestamp:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%d/%m %H:%M')
            
            table_data.append([
                timestamp,
                alert.get('rule_name', 'N/A')[:30],
                alert.get('description', 'N/A')[:60]
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffe5e5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_timeline(self, alerts: List[Dict[str, Any]]) -> List:
        """Construit une timeline des événements"""
        elements = []
        
        elements.append(Paragraph("Timeline des Événements", self.styles['SectionTitle']))
        
        if not alerts:
            elements.append(Paragraph("Aucun événement à afficher", self.styles['Normal']))
            return elements
        
        # Grouper par heure
        hourly_counts = {}
        for alert in alerts:
            timestamp = alert.get('timestamp', '')
            if 'T' in timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.strftime('%d/%m %H:00')
                    hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                except:
                    pass
        
        if hourly_counts:
            table_data = [["Période", "Nombre d'alertes"]]
            for hour in sorted(hourly_counts.keys())[-24:]:  # Dernières 24 heures
                table_data.append([hour, str(hourly_counts[hour])])
            
            table = Table(table_data, colWidths=[2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        
        return elements
