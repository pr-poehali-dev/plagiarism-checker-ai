import json
import os
import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class UniquenessRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000)

class Match(BaseModel):
    source: str
    similarity: float
    excerpt: str

class UniquenessResponse(BaseModel):
    uniqueness: float
    words: int
    characters: int
    matches: List[Match]
    ai_analysis: str

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Analyze text uniqueness using DeepSeek AI from SambaNova
    Args: event - dict with httpMethod, body
          context - object with request_id attribute
    Returns: HTTP response with uniqueness score and matches
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
        req = UniquenessRequest(**body_data)
        
        api_key = os.environ.get('SAMBANOVA_API_KEY')
        if not api_key:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'isBase64Encoded': False,
                'body': json.dumps({'error': 'API key not configured'})
            }
        
        import requests
        
        prompt = f"""Проанализируй следующий текст на уникальность и оригинальность.

Текст для анализа:
{req.text}

Ответь в формате JSON со следующей структурой:
{{
  "uniqueness_score": <число от 0 до 100>,
  "analysis": "<краткий анализ на русском>",
  "potential_matches": [
    {{
      "source": "<название источника или тип контента>",
      "similarity": <процент схожести от 0 до 100>,
      "excerpt": "<цитата или описание совпадения>"
    }}
  ]
}}

Оцени:
1. Оригинальность мыслей и идей
2. Уникальность формулировок
3. Признаки использования AI или копирования
4. Стиль написания

Если текст оригинальный - дай высокий процент уникальности (85-100%).
Если есть подозрения на плагиат или AI-генерацию - укажи это в matches."""

        response = requests.post(
            'https://api.sambanova.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'Meta-Llama-3.3-70B-Instruct',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 2000
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'isBase64Encoded': False,
                'body': json.dumps({'error': f'AI API error: {response.text}'})
            }
        
        ai_response = response.json()
        content = ai_response['choices'][0]['message']['content']
        
        json_matches = re.findall(r'\{[^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)*\}', content)
        
        ai_data = None
        for match_str in json_matches:
            try:
                parsed = json.loads(match_str)
                if 'uniqueness_score' in parsed:
                    ai_data = parsed
                    break
            except json.JSONDecodeError:
                continue
        
        if not ai_data:
            ai_data = {
                'uniqueness_score': 50,
                'analysis': 'ИИ не смог определить точный процент уникальности. Рекомендуется повторная проверка.',
                'potential_matches': []
            }
        
        words = len(req.text.split())
        characters = len(req.text)
        
        matches = []
        for match in ai_data.get('potential_matches', [])[:5]:
            matches.append(Match(
                source=match.get('source', 'Unknown source'),
                similarity=float(match.get('similarity', 0)),
                excerpt=match.get('excerpt', '')[:200]
            ))
        
        result = UniquenessResponse(
            uniqueness=float(ai_data.get('uniqueness_score', 85)),
            words=words,
            characters=characters,
            matches=matches,
            ai_analysis=ai_data.get('analysis', 'Анализ завершен')
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'isBase64Encoded': False,
            'body': json.dumps(result.dict(), ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }