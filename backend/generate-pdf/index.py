import json
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import base64
from io import BytesIO

class Match(BaseModel):
    source: str
    similarity: float
    excerpt: str

class PDFRequest(BaseModel):
    text: str = Field(..., min_length=1)
    uniqueness: float = Field(..., ge=0, le=100)
    words: int
    characters: int
    matches: List[Match]
    ai_analysis: str

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Generate PDF report for text uniqueness analysis
    Args: event - dict with httpMethod, body
          context - object with request_id attribute
    Returns: HTTP response with base64-encoded PDF file
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        req = PDFRequest(**body_data)
        
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        except:
            pass
        
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#7C3AED'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#7C3AED'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            fontName='DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
        )
        
        story.append(Paragraph('Отчет о проверке уникальности текста', title_style))
        story.append(Paragraph(f'PlagiatAI - {datetime.now().strftime("%d.%m.%Y %H:%M")}', normal_style))
        story.append(Spacer(1, 20))
        
        uniqueness_color = colors.green if req.uniqueness >= 80 else (colors.orange if req.uniqueness >= 60 else colors.red)
        
        summary_data = [
            ['Показатель', 'Значение'],
            ['Уникальность', f'{req.uniqueness:.1f}%'],
            ['Слов', str(req.words)],
            ['Символов', str(req.characters)],
            ['Совпадений найдено', str(len(req.matches))]
        ]
        
        summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ]))
        
        story.append(Paragraph('Общая информация', heading_style))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph('Анализ ИИ', heading_style))
        story.append(Paragraph(req.ai_analysis, normal_style))
        story.append(Spacer(1, 20))
        
        if req.matches:
            story.append(Paragraph('Найденные совпадения', heading_style))
            
            for idx, match in enumerate(req.matches, 1):
                match_data = [
                    ['Источник', match.source],
                    ['Совпадение', f'{match.similarity:.1f}%'],
                    ['Фрагмент', match.excerpt]
                ]
                
                match_table = Table(match_data, colWidths=[4*cm, 12*cm])
                match_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0E7FF')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1E40AF')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (1, 0), (1, -1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                ]))
                
                story.append(Paragraph(f'Совпадение #{idx}', normal_style))
                story.append(match_table)
                story.append(Spacer(1, 15))
        
        story.append(PageBreak())
        story.append(Paragraph('Проверенный текст', heading_style))
        
        text_paragraphs = req.text.split('\n')
        for para in text_paragraphs:
            if para.strip():
                story.append(Paragraph(para, normal_style))
        
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                'pdf': pdf_base64,
                'filename': f'uniqueness_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }
