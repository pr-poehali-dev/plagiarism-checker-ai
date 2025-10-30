import json
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import base64
from io import BytesIO
import unicodedata

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
        
        def transliterate(text: str) -> str:
            translit_map = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
                'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
                'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
                'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
                'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh',
                'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
                'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts',
                'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
            }
            return ''.join(translit_map.get(c, c) for c in text)
        
        from fpdf import FPDF
        
        class PDF(FPDF):
            def __init__(self):
                super().__init__()
                self.font_name = 'Arial'
            
            def header(self):
                self.set_font(self.font_name, 'B', 16)
                self.set_text_color(124, 58, 237)
                self.cell(0, 10, 'PlagiatAI - Otchet o proverke unikalnosti', 0, 1, 'C')
                self.ln(5)
            
            def footer(self):
                self.set_y(-15)
                self.set_font(self.font_name, '', 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f'Stranica {self.page_no()}', 0, 0, 'C')
        
        pdf = PDF()
        pdf.add_page()
        
        try:
            pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
            pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
            font_name = 'DejaVu'
            pdf.font_name = 'DejaVu'
        except:
            font_name = 'Arial'
            pdf.font_name = 'Arial'
        
        pdf.set_font(font_name, '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, transliterate(f'Дата проверки: {datetime.now().strftime("%d.%m.%Y %H:%M")}'), 0, 1)
        pdf.ln(10)
        
        pdf.set_font(font_name, 'B', 14)
        pdf.set_text_color(124, 58, 237)
        pdf.cell(0, 10, transliterate('Результаты анализа'), 0, 1)
        pdf.ln(5)
        
        uniqueness_color = (34, 197, 94) if req.uniqueness >= 80 else ((251, 146, 60) if req.uniqueness >= 60 else (239, 68, 68))
        
        pdf.set_font(font_name, 'B', 48)
        pdf.set_text_color(*uniqueness_color)
        pdf.cell(0, 20, f'{req.uniqueness:.1f}%', 0, 1, 'C')
        pdf.set_font(font_name, '', 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, transliterate('Уникальность текста'), 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_fill_color(240, 240, 245)
        pdf.set_font(font_name, 'B', 11)
        pdf.set_text_color(50, 50, 50)
        
        stats = [
            (transliterate('Количество слов:'), str(req.words)),
            (transliterate('Количество символов:'), str(req.characters)),
            (transliterate('Найдено совпадений:'), str(len(req.matches)))
        ]
        
        for label, value in stats:
            pdf.set_font(font_name, 'B', 10)
            pdf.cell(80, 8, label, 1, 0, 'L', True)
            pdf.set_font(font_name, '', 10)
            pdf.cell(0, 8, value, 1, 1, 'L', True)
        
        pdf.ln(10)
        
        pdf.set_font(font_name, 'B', 14)
        pdf.set_text_color(124, 58, 237)
        pdf.cell(0, 10, transliterate('Анализ ИИ'), 0, 1)
        pdf.ln(3)
        
        pdf.set_font(font_name, '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, transliterate(req.ai_analysis))
        pdf.ln(10)
        
        if req.matches:
            pdf.set_font(font_name, 'B', 14)
            pdf.set_text_color(124, 58, 237)
            pdf.cell(0, 10, transliterate('Найденные совпадения'), 0, 1)
            pdf.ln(5)
            
            for idx, match in enumerate(req.matches, 1):
                pdf.set_font(font_name, 'B', 11)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 8, transliterate(f'Совпадение #{idx}'), 0, 1)
                
                pdf.set_fill_color(224, 231, 255)
                pdf.set_font(font_name, 'B', 9)
                pdf.set_text_color(30, 64, 175)
                pdf.cell(60, 6, transliterate('Источник:'), 1, 0, 'L', True)
                pdf.set_font(font_name, '', 9)
                pdf.set_text_color(50, 50, 50)
                pdf.multi_cell(0, 6, transliterate(match.source), 1)
                
                pdf.set_font(font_name, 'B', 9)
                pdf.set_text_color(30, 64, 175)
                pdf.cell(60, 6, transliterate('Совпадение:'), 1, 0, 'L', True)
                pdf.set_font(font_name, '', 9)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 6, f'{match.similarity:.1f}%', 1, 1)
                
                pdf.set_font(font_name, 'B', 9)
                pdf.set_text_color(30, 64, 175)
                pdf.cell(60, 6, transliterate('Фрагмент:'), 1, 0, 'L', True)
                pdf.set_font(font_name, '', 9)
                pdf.set_text_color(50, 50, 50)
                
                y_before = pdf.get_y()
                x_before = pdf.get_x()
                pdf.multi_cell(0, 6, transliterate(match.excerpt), 1)
                
                pdf.ln(5)
        
        pdf.add_page()
        pdf.set_font(font_name, 'B', 14)
        pdf.set_text_color(124, 58, 237)
        pdf.cell(0, 10, transliterate('Проверенный текст'), 0, 1)
        pdf.ln(5)
        
        pdf.set_font(font_name, '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, transliterate(req.text))
        
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin1')
        else:
            pdf_bytes = bytes(pdf_output)
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
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'isBase64Encoded': False,
            'body': json.dumps(error_details, ensure_ascii=False)
        }