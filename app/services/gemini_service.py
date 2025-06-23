import google.generativeai as genai
import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class GeminiAdviceService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_advice(self, code: str, problem_description: str, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        コードと問題、テスト結果を基にアドバイスを生成
        
        Args:
            code: 提出されたコード
            problem_description: 問題の説明
            test_results: テスト実行結果
        
        Returns:
            dict: アドバイスと関連情報
        """
        try:
            prompt = self._create_advice_prompt(code, problem_description, test_results)
            
            response = self.model.generate_content(prompt)
            
            # レスポンスの解析
            advice_data = self._parse_advice_response(response.text)
            
            # トークン使用量の計算（概算）
            token_count = self._estimate_token_count(prompt + response.text)
            
            return {
                "advice": advice_data.get("advice", "アドバイスの生成に失敗しました"),
                "suggestions": advice_data.get("suggestions", []),
                "hints": advice_data.get("hints", []),
                "token_count": token_count,
                "cost_estimate": self._calculate_cost(token_count)
            }
            
        except Exception as e:
            return {
                "advice": f"アドバイス生成エラー: {str(e)}",
                "suggestions": [],
                "hints": [],
                "token_count": 0,
                "cost_estimate": 0
            }
    
    def _create_advice_prompt(self, code: str, problem_description: str, test_results: Dict[str, Any]) -> str:
        """
        アドバイス生成用のプロンプトを作成
        """
        failed_tests = [test for test in test_results.get("details", []) if test.get("status") != "passed"]
        
        prompt = f"""
あなたはプログラミング学習のメンターです。初学者向けのPython課題に対して、建設的なアドバイスを提供してください。

**重要な指針:**
1. 答えを直接教えるのではなく、自分で修正を考えられるようなヒントを提供する
2. 具体的で実行可能なアドバイスを心がける
3. 受講生の学習レベルに合わせた説明をする
4. エラーの原因を特定し、改善の方向性を示す

**問題の説明:**
{problem_description}

**提出されたコード:**
```python
{code}
```

**テスト結果:**
- 成功: {test_results.get('passed', 0)}/{test_results.get('total', 0)}
- エラー: {test_results.get('errors', [])}

**失敗したテストケース:**
{json.dumps(failed_tests, ensure_ascii=False, indent=2)}

以下のJSON形式で回答してください:
{{
    "advice": "メインのアドバイス（200字程度）",
    "suggestions": [
        "具体的な改善提案1",
        "具体的な改善提案2",
        "具体的な改善提案3"
    ],
    "hints": [
        "実装のヒント1",
        "実装のヒント2"
    ]
}}

**チート防止について:**
コードに答えが含まれている場合でも、学習に繋がるような指導をしてください。
"""
        return prompt
    
    def _parse_advice_response(self, response_text: str) -> Dict[str, Any]:
        """
        Geminiからのレスポンスを解析
        """
        try:
            # JSONブロックを抽出
            start_marker = "```json"
            end_marker = "```"
            
            if start_marker in response_text:
                start = response_text.find(start_marker) + len(start_marker)
                end = response_text.find(end_marker, start)
                json_text = response_text[start:end].strip()
            else:
                # JSONブロックがない場合は、{}で囲まれた部分を探す
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_text = response_text[start:end]
                else:
                    # JSONが見つからない場合はデフォルト値を返す
                    return {
                        "advice": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                        "suggestions": [],
                        "hints": []
                    }
            
            return json.loads(json_text)
            
        except json.JSONDecodeError:
            # JSON解析に失敗した場合は、プレーンテキストとして処理
            return {
                "advice": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "suggestions": [],
                "hints": []
            }
    
    def _estimate_token_count(self, text: str) -> int:
        """
        トークン数の概算（日本語対応）
        """
        # 簡易的な計算: 文字数 ÷ 2 （日本語の場合）
        return len(text) // 2
    
    def _calculate_cost(self, token_count: int) -> float:
        """
        コストの概算計算
        """
        # Gemini Proの料金（2024年時点の概算）
        # 入力: $0.00025 / 1K tokens
        # 出力: $0.0005 / 1K tokens
        # 簡易計算として平均を使用
        cost_per_1k_tokens = 0.000375
        return (token_count / 1000) * cost_per_1k_tokens
    
    def detect_cheating(self, code: str, problem_description: str) -> Dict[str, Any]:
        """
        チート行為の検出
        """
        try:
            prompt = f"""
以下のPythonコードを分析し、チート行為の可能性があるかを判定してください。

**問題の説明:**
{problem_description}

**提出されたコード:**
```python
{code}
```

**チェック項目:**
1. コード内に答えが直接書かれているか
2. 問題を解かずに期待される出力を直接返しているか
3. 外部からの答えのコピーの可能性があるか

以下のJSON形式で回答してください:
{{
    "is_cheating": true/false,
    "confidence": 0.0-1.0,
    "reasons": ["理由1", "理由2"],
    "recommendations": ["推奨事項1", "推奨事項2"]
}}
"""
            
            response = self.model.generate_content(prompt)
            return self._parse_advice_response(response.text)
            
        except Exception as e:
            return {
                "is_cheating": False,
                "confidence": 0.0,
                "reasons": [f"チート検出エラー: {str(e)}"],
                "recommendations": []
            }