// メインページのJavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadProblems();
    setupEventListeners();
});

function setupEventListeners() {
    // 問題選択時の処理
    document.getElementById('problemSelect').addEventListener('change', function() {
        const problemId = this.value;
        if (problemId) {
            loadProblemDetails(problemId);
        } else {
            document.getElementById('problemDisplay').style.display = 'none';
        }
    });

    // フォーム送信時の処理
    document.getElementById('submissionForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitCode();
    });
}

async function loadProblems() {
    try {
        const response = await fetch('/api/problems/');
        const problems = await response.json();
        
        const select = document.getElementById('problemSelect');
        select.innerHTML = '<option value="">問題を選択してください</option>';
        
        problems.forEach(problem => {
            const option = document.createElement('option');
            option.value = problem.id;
            option.textContent = `${problem.title} (${problem.difficulty})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('問題の読み込みに失敗しました:', error);
        showAlert('問題の読み込みに失敗しました', 'danger');
    }
}

async function loadProblemDetails(problemId) {
    try {
        const response = await fetch(`/api/problems/${problemId}`);
        const problem = await response.json();
        
        document.getElementById('problemTitle').textContent = problem.title;
        document.getElementById('problemDescription').textContent = problem.description;
        document.getElementById('problemDisplay').style.display = 'block';
    } catch (error) {
        console.error('問題詳細の読み込みに失敗しました:', error);
        showAlert('問題詳細の読み込みに失敗しました', 'danger');
    }
}

async function submitCode() {
    const problemId = document.getElementById('problemSelect').value;
    const studentName = document.getElementById('studentName').value;
    const code = document.getElementById('codeInput').value;
    
    if (!problemId) {
        showAlert('問題を選択してください', 'warning');
        return;
    }
    
    // 送信ボタンの状態を変更
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('submitSpinner');
    const originalText = submitBtn.textContent;
    
    submitBtn.disabled = true;
    spinner.classList.remove('d-none');
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>評価中...';
    
    try {
        // コードを提出
        const response = await fetch('/api/submissions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                problem_id: parseInt(problemId),
                student_name: studentName,
                code: code
            })
        });
        
        const submission = await response.json();
        
        if (response.ok) {
            showAlert('コードを提出しました。評価をお待ちください...', 'success');
            
            // 評価結果を待つ
            await waitForEvaluation(submission.id);
        } else {
            throw new Error(submission.detail || '提出に失敗しました');
        }
    } catch (error) {
        console.error('提出エラー:', error);
        showAlert('提出に失敗しました: ' + error.message, 'danger');
    } finally {
        // 送信ボタンを元に戻す
        submitBtn.disabled = false;
        spinner.classList.add('d-none');
        submitBtn.textContent = originalText;
    }
}

async function waitForEvaluation(submissionId) {
    const maxAttempts = 30; // 最大30回（約30秒）
    let attempts = 0;
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/api/submissions/${submissionId}`);
            const submission = await response.json();
            
            if (submission.status === 'evaluated') {
                await loadAdvice(submissionId);
                return true;
            } else if (submission.status === 'error') {
                showAlert('評価中にエラーが発生しました', 'danger');
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('状態確認エラー:', error);
            return false;
        }
    };
    
    const poll = async () => {
        const completed = await checkStatus();
        if (completed || attempts >= maxAttempts) {
            if (attempts >= maxAttempts) {
                showAlert('評価に時間がかかっています。しばらく待ってから再度確認してください。', 'warning');
            }
            return;
        }
        
        attempts++;
        setTimeout(poll, 1000); // 1秒後に再チェック
    };
    
    poll();
}

async function loadAdvice(submissionId) {
    try {
        const response = await fetch(`/api/submissions/${submissionId}/advice`);
        const advice = await response.json();
        
        displayResults(advice);
    } catch (error) {
        console.error('アドバイス読み込みエラー:', error);
        showAlert('アドバイスの読み込みに失敗しました', 'danger');
    }
}

function displayResults(advice) {
    // テスト結果の表示
    const testResults = advice.test_results;
    const testResultsDiv = document.getElementById('testResults');
    
    let testHtml = `
        <div class="row mb-3">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h5 class="card-title">テスト通過率</h5>
                        <h2 class="text-${testResults.passed === testResults.total ? 'success' : 'warning'}">
                            ${testResults.passed} / ${testResults.total}
                        </h2>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    if (testResults.details && testResults.details.length > 0) {
        testHtml += '<h6>詳細結果:</h6>';
        testResults.details.forEach((test, index) => {
            const statusClass = test.status === 'passed' ? 'test-passed' : 
                               test.status === 'failed' ? 'test-failed' : 'test-error';
            
            testHtml += `
                <div class="${statusClass}">
                    <strong>テストケース ${index + 1}:</strong> ${test.status}
                    ${test.expected !== undefined ? `<br><small>期待値: ${JSON.stringify(test.expected)}</small>` : ''}
                    ${test.actual !== undefined ? `<br><small>実際の値: ${JSON.stringify(test.actual)}</small>` : ''}
                    ${test.error ? `<br><small class="text-danger">エラー: ${test.error}</small>` : ''}
                </div>
            `;
        });
    }
    
    testResultsDiv.innerHTML = testHtml;
    
    // アドバイスの表示
    document.getElementById('adviceContent').textContent = advice.advice;
    
    // 改善提案の表示
    const suggestionsSection = document.getElementById('suggestionsSection');
    const suggestionsList = document.getElementById('suggestionsList');
    
    if (advice.suggestions && advice.suggestions.length > 0) {
        suggestionsList.innerHTML = '';
        advice.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
        suggestionsSection.style.display = 'block';
    } else {
        suggestionsSection.style.display = 'none';
    }
    
    // コスト情報の表示
    document.getElementById('costInfo').textContent = 
        `使用コスト: ${advice.cost} トークン`;
    
    // 結果カードを表示
    document.getElementById('resultCard').style.display = 'block';
    
    // 結果カードまでスクロール
    document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth' });
}

function showAlert(message, type) {
    // 既存のアラートを削除
    const existingAlert = document.querySelector('.alert-dismissible');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 新しいアラートを作成
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // ページの上部に挿入
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 3秒後に自動で消す
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}