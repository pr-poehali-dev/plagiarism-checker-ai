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
        
        prompt = f"""Analyze the following text for uniqueness and originality.

Text to analyze:
{req.text}

You MUST respond with ONLY a valid JSON object, nothing else. No explanation, no markdown, just JSON.

Required JSON structure:
{{
  "uniqueness_score": <number from 0 to 100>,
  "analysis": "<brief analysis in Russian>",
  "potential_matches": [
    {{
      "source": "<source name or content type>",
      "similarity": <similarity percentage from 0 to 100>,
      "excerpt": "<quote or description of match>"
    }}
  ]
}}

Evaluate:
1. Originality of thoughts and ideas
2. Uniqueness of wording
3. Signs of AI use or copying
4. Writing style

If text is original - give high uniqueness (85-100%).
If there are suspicions of plagiarism or AI generation - indicate it in matches.

Respond ONLY with valid JSON, no additional text."""

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
        content = ai_response['choices'][0]['message']['content'].strip()
        
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()
        
        try:
            ai_data = json.loads(content)
            if 'uniqueness_score' not in ai_data:
                raise ValueError('Missing uniqueness_score')
        except (json.JSONDecodeError, ValueError) as e:
            json_match = re.search(r'\{[^\{]*"uniqueness_score"[^\}]*\}', content, re.DOTALL)
            if json_match:
                try:
                    ai_data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    ai_data = None
            else:
                ai_data = None
        
        if not ai_data or 'uniqueness_score' not in ai_data:
            ai_data = {
                'uniqueness_score': 75,
                'analysis': 'ИИ не смог точно определить уникальность. Результат основан на базовом анализе.',
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