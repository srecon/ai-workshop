import os
import json
import requests
from typing import Dict, Optional
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.gemini_model = None
        self.openai_client = None
        self.omlx_client = None

        # Get Ollama configuration from .env
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.ollama_url = ollama_url.rstrip('/')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')

        print(f"Ollama configured with URL: {self.ollama_url}")
        print(f"Ollama model: {self.ollama_model}")

        # Get oMLX configuration from .env
        omlx_url = os.getenv('OMLX_URL', 'http://127.0.0.1:8000/v1')
        self.omlx_url = omlx_url.rstrip('/v1').rstrip('/')
        print(f"oMLX configured with URL: {self.omlx_url}")

        # Initialize Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                print("Gemini initialized successfully")
            except Exception as e:
                print(f"Error initializing Gemini: {e}")

        # Initialize OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                print("OpenAI initialized successfully")
            except Exception as e:
                print(f"Error initializing OpenAI: {e}")

        # Initialize oMLX (OpenAI-compatible)
        omlx_key = os.getenv('OMLX_API_KEY', 'sk-omlx')
        try:
            self.omlx_client = OpenAI(
                api_key=omlx_key,
                base_url=self.omlx_url,
            )
            print("oMLX initialized successfully")
        except Exception as e:
            print(f"Error initializing oMLX: {e}")
    
    def analyze_portfolio(self, metrics: Dict, provider: str = 'omlx') -> str:
        """Analyze portfolio using specified LLM"""
        # Build anonymized prompt
        prompt = self._build_analysis_prompt(metrics)

        print(f"Analyzing with provider: {provider}")

        if provider == 'omlx' and self.omlx_client:
            return self._call_omlx(prompt)
        elif provider == 'gemini' and self.gemini_model:
            return self._call_gemini(prompt)
        elif provider == 'openai' and self.openai_client:
            return self._call_openai(prompt)
        elif provider == 'ollama':
            return self._call_ollama(prompt)
        else:
            return f"Error: {provider} provider not configured. Please check API keys or Ollama setup."
    
    def _build_analysis_prompt(self, metrics: Dict) -> str:
        """Build anonymized prompt for LLM"""
        # Safely get values with defaults
        net_worth = metrics.get('net_worth', 0)
        monthly_cashflow = metrics.get('monthly_cashflow', 0)
        total_liabilities = metrics.get('total_liabilities', 0)
        total_income = metrics.get('total_income', 0)
        total_expenses = metrics.get('total_expenses', 0)
        
        # Get asset allocation safely
        allocation = metrics.get('asset_allocation', {})
        foundation = allocation.get('foundation', 0)
        growth = allocation.get('growth', 0)
        high_risk = allocation.get('high_risk', 0)
        
        # Get risk info safely
        risk = metrics.get('risk', {})
        risk_score = risk.get('score', 0)
        risk_level = risk.get('level', 'Unknown')
        high_risk_pct = risk.get('high_risk_percentage', 0)
        foundation_pct = risk.get('foundation_percentage', 0)
        
        prompt = f"""Ты профессиональный финансовый советник. Проанализируй этот анонимизированный портфель и дай 3-5 практических рекомендаций.

ПОКАЗАТЕЛИ ПОРТФЕЛЯ:
- Чистая стоимость (Net Worth): ₽{net_worth:,.0f}
- Ежемесячный денежный поток: ₽{monthly_cashflow:,.0f}
- Общие обязательства: ₽{total_liabilities:,.0f}

РАСПРЕДЕЛЕНИЕ АКТИВОВ:
- Фундаментальные активы (Недвижимость, Депозиты, Металлы): ₽{foundation:,.0f}
- Ростовые активы (Акции, Бизнес): ₽{growth:,.0f}
- Высокорисковые активы (Криптовалюта): ₽{high_risk:,.0f}

ПРОФИЛЬ РИСКА:
- Оценка риска: {risk_score}/10 ({risk_level})
- Доля высокорисковых активов: {high_risk_pct:.1f}%
- Фундаментальная подушка: {foundation_pct:.1f}%

ДОХОДЫ И РАСХОДЫ:
- Ежемесячный доход: ₽{total_income:,.0f}
- Ежемесячные расходы: ₽{total_expenses:,.0f}

На основе этих данных предоставь:
1. Рекомендации по диверсификации
2. Советы по управлению рисками
3. Предложения по оптимизации денежного потока
4. Конкретные шаги для роста капитала
5. Любые тревожные сигналы или проблемы

Дай ответ на русском языке, практичный и конкретный."""
        
        return prompt
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Ошибка при вызове Gemini: {str(e)}"
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при вызове OpenAI: {str(e)}"
    
    def _call_omlx(self, prompt: str) -> str:
        """Call oMLX (OpenAI-compatible API)"""
        try:
            response = self.omlx_client.chat.completions.create(
                model=os.getenv('OMLX_MODEL', 'Qwen3.6-35B-A3B-MLX-4bit'),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                top_p=0.8,
                max_tokens=8192,
                timeout=600,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при вызове oMLX: {str(e)}"

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama"""
        try:
            # First, test if Ollama is reachable
            print(f"Attempting to connect to Ollama at {self.ollama_url}")
            
            # Check if Ollama is running and has the model
            list_response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            print(f"Ollama tags response: {list_response.status_code}")
            
            if list_response.status_code == 200:
                models = list_response.json().get('models', [])
                available_models = [m['name'] for m in models]
                print(f"Available models: {available_models}")
                
                # Check if our model is available
                model_available = any(self.ollama_model in m for m in available_models)
                if not model_available:
                    return f"""Модель '{self.ollama_model}' не найдена. Доступные модели: {', '.join(available_models[:5])}

Пожалуйста, установите модель командой: ollama pull {self.ollama_model}"""
            
            # Make the generation request
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1000
                    }
                },
                timeout=60
            )
            
            print(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Нет ответа от Ollama')
            else:
                return f"Ошибка Ollama: статус {response.status_code}\n{response.text}"
                
        except requests.exceptions.ConnectionError:
            return f"""Не удалось подключиться к Ollama по адресу {self.ollama_url}

Пожалуйста, проверьте:
1. Запущен ли Ollama: в терминале выполните 'ollama serve'
2. Правильный ли порт указан в файле .env: OLLAMA_URL={self.ollama_url}
3. Установлена ли модель: ollama pull {self.ollama_model}

Текущий порт из .env: {self.ollama_url}"""
        except requests.exceptions.Timeout:
            return f"Таймаут при подключении к Ollama. Убедитесь, что Ollama отвечает на {self.ollama_url}"
        except Exception as e:
            return f"Неожиданная ошибка при вызове Ollama: {str(e)}"
    
    def ask_followup(self, question: str, context: Dict, provider: str = 'omlx') -> str:
        """Ask follow-up questions about portfolio"""
        prompt = f"""На основе этого контекста портфеля:
{json.dumps(context, indent=2, ensure_ascii=False)}

Вопрос пользователя: {question}

Дай подробный, практичный ответ, фокусируясь на личных финансах и инвестиционной стратегии в контексте российского рубля."""

        if provider == 'omlx' and self.omlx_client:
            return self._call_omlx(prompt)
        elif provider == 'gemini' and self.gemini_model:
            return self._call_gemini(prompt)
        elif provider == 'openai' and self.openai_client:
            return self._call_openai(prompt)
        elif provider == 'ollama':
            return self._call_ollama(prompt)
        else:
            return f"Провайдер {provider} не настроен"