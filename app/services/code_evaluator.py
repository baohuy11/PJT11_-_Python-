import json
import docker
import tempfile
import os
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

load_dotenv()

class CodeEvaluator:
    def __init__(self):
        self.client = docker.from_env()
        self.timeout = int(os.getenv("SANDBOX_TIMEOUT", 30))
    
    def evaluate_code(self, code: str, test_cases: str) -> Tuple[Dict[str, Any], bool]:
        """
        提出されたコードをテストケースで評価
        
        Args:
            code: 提出されたPythonコード
            test_cases: テストケース（JSON形式）
        
        Returns:
            tuple: (テスト結果, 全テスト通過フラグ)
        """
        try:
            test_data = json.loads(test_cases)
            results = {
                "passed": 0,
                "total": len(test_data),
                "details": [],
                "errors": []
            }
            
            all_passed = True
            
            for i, test_case in enumerate(test_data):
                result = self._run_test_case(code, test_case, i)
                results["details"].append(result)
                
                if result["status"] == "passed":
                    results["passed"] += 1
                else:
                    all_passed = False
                    if result.get("error"):
                        results["errors"].append(result["error"])
            
            return results, all_passed
            
        except Exception as e:
            return {
                "passed": 0,
                "total": 0,
                "details": [],
                "errors": [f"評価エラー: {str(e)}"]
            }, False
    
    def _run_test_case(self, code: str, test_case: Dict[str, Any], case_num: int) -> Dict[str, Any]:
        """
        単一のテストケースを実行
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # テスト用のPythonファイルを作成
                test_code = self._create_test_code(code, test_case)
                test_file = os.path.join(temp_dir, "test_code.py")
                
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(test_code)
                
                # Dockerコンテナでコードを実行
                result = self._run_in_container(temp_dir, case_num)
                return result
                
        except Exception as e:
            return {
                "case_num": case_num,
                "status": "error",
                "error": f"テストケース実行エラー: {str(e)}",
                "expected": test_case.get("expected"),
                "actual": None
            }
    
    def _create_test_code(self, user_code: str, test_case: Dict[str, Any]) -> str:
        """
        テスト実行用のPythonコードを生成
        """
        test_template = f"""
import sys
import json
import traceback

# ユーザーのコード
{user_code}

# テストケースの実行
try:
    # 入力データの設定
    test_input = {json.dumps(test_case.get('input', []))}
    expected = {json.dumps(test_case.get('expected'))}
    
    # 関数の実行（関数名は動的に決定する必要がある）
    # ここでは簡単な例として、mainという関数があることを想定
    if 'main' in globals():
        if isinstance(test_input, list):
            actual = main(*test_input)
        else:
            actual = main(test_input)
    else:
        # mainがない場合は、コード全体を実行して結果を取得
        actual = None
    
    # 結果の比較
    if actual == expected:
        result = {{"status": "passed", "expected": expected, "actual": actual}}
    else:
        result = {{"status": "failed", "expected": expected, "actual": actual}}
    
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc(),
        "expected": expected,
        "actual": None
    }}
    print(json.dumps(error_result))
"""
        return test_template
    
    def _run_in_container(self, volume_path: str, case_num: int) -> Dict[str, Any]:
        """
        Dockerコンテナ内でコードを実行
        """
        try:
            container = self.client.containers.run(
                "python:3.9-slim",
                f"python /app/test_code.py",
                volumes={volume_path: {"bind": "/app", "mode": "ro"}},
                remove=True,
                timeout=self.timeout,
                capture_output=True,
                text=True
            )
            
            if container.returncode == 0:
                try:
                    result = json.loads(container)
                    result["case_num"] = case_num
                    return result
                except json.JSONDecodeError:
                    return {
                        "case_num": case_num,
                        "status": "error",
                        "error": "出力の解析に失敗しました",
                        "raw_output": container
                    }
            else:
                return {
                    "case_num": case_num,
                    "status": "error",
                    "error": "コード実行エラー",
                    "stderr": container
                }
                
        except docker.errors.ContainerError as e:
            return {
                "case_num": case_num,
                "status": "error",
                "error": f"コンテナエラー: {str(e)}"
            }
        except Exception as e:
            return {
                "case_num": case_num,
                "status": "error",
                "error": f"実行エラー: {str(e)}"
            }
    
    def check_code_safety(self, code: str) -> Tuple[bool, List[str]]:
        """
        コードの安全性をチェック
        
        Returns:
            tuple: (安全フラグ, 警告リスト)
        """
        warnings = []
        is_safe = True
        
        # 危険な関数やモジュールのチェック
        dangerous_patterns = [
            "import os",
            "import subprocess",
            "import sys",
            "exec(",
            "eval(",
            "open(",
            "__import__",
            "globals()",
            "locals()"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                warnings.append(f"危険な可能性のあるコード: {pattern}")
                is_safe = False
        
        return is_safe, warnings