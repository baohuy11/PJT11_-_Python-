// 管理者ページのJavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadProblemsForAdmin();
    loadSubmissions();
    setupEventListeners();
});

function setupEventListeners() {
    // 問題作成フォーム
    document.getElementById('problemForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createProblem();
    });

    // 問題フィルター
    document.getElementById('problemFilter').addEventListener('change', function() {
        const problemId = this.value;
        loadSubmissions(problemId || null);
    });
}

async function createProblem() {
    const title = document.getElementById('problemTitleInput').value;
    const description = document.getElementById('problemDescInput').value;
    const testCases = document.getElementById('testCasesInput').value;
    const expectedOutput = document.getElementById('expectedOutputInput').value;
    const difficulty = document.getElementById('difficultySelect').value;

    try {
        // テストケースのJSONバリデーション
        JSON.parse(testCases);
        
        const response = await fetch('/api/problems/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                description: description,
                test_cases: testCases,
                expected_output: expectedOutput,
                difficulty: difficulty
            })
        });

        if (response.ok) {
            showAlert('問題が作成されました', 'success');
            document.getElementById('problemForm').reset();
            loadProblemsForAdmin();
            loadProblemsForFilter();
        } else {
            const error = await response.json();
            throw new Error(error.detail || '問題の作成に失敗しました');
        }
    } catch (error) {
        if (error instanceof SyntaxError) {
            showAlert('テストケースのJSON形式が正しくありません', 'danger');
        } else {
            console.error('問題作成エラー:', error);
            showAlert('問題の作成に失敗しました: ' + error.message, 'danger');
        }
    }
}

async function loadProblemsForAdmin() {
    try {
        const response = await fetch('/api/problems/');
        const problems = await response.json();
        
        const problemsList = document.getElementById('problemsList');
        
        if (problems.length === 0) {
            problemsList.innerHTML = '<p class="text-muted">問題がありません</p>';
            return;
        }
        
        let html = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>タイトル</th>
                            <th>難易度</th>
                            <th>作成日</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        problems.forEach(problem => {
            const createdAt = new Date(problem.created_at).toLocaleDateString('ja-JP');
            html += `
                <tr>
                    <td>${problem.id}</td>
                    <td>${problem.title}</td>
                    <td><span class="problem-difficulty difficulty-${problem.difficulty}">${problem.difficulty}</span></td>
                    <td>${createdAt}</td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="viewProblem(${problem.id})">詳細</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteProblem(${problem.id})">削除</button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        problemsList.innerHTML = html;
        
        // フィルター用の問題リストも更新
        loadProblemsForFilter();
        
    } catch (error) {
        console.error('問題読み込みエラー:', error);
        showAlert('問題の読み込みに失敗しました', 'danger');
    }
}

async function loadProblemsForFilter() {
    try {
        const response = await fetch('/api/problems/');
        const problems = await response.json();
        
        const filter = document.getElementById('problemFilter');
        filter.innerHTML = '<option value="">すべての問題</option>';
        
        problems.forEach(problem => {
            const option = document.createElement('option');
            option.value = problem.id;
            option.textContent = problem.title;
            filter.appendChild(option);
        });
    } catch (error) {
        console.error('フィルター用問題読み込みエラー:', error);
    }
}

async function deleteProblem(problemId) {
    if (!confirm('この問題を削除しますか？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/problems/${problemId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('問題が削除されました', 'success');
            loadProblemsForAdmin();
            loadProblemsForFilter();
        } else {
            throw new Error('削除に失敗しました');
        }
    } catch (error) {
        console.error('問題削除エラー:', error);
        showAlert('問題の削除に失敗しました', 'danger');
    }
}

async function viewProblem(problemId) {
    try {
        const response = await fetch(`/api/problems/${problemId}`);
        const problem = await response.json();
        
        let testCases = '';
        try {
            const parsed = JSON.parse(problem.test_cases);
            testCases = JSON.stringify(parsed, null, 2);
        } catch {
            testCases = problem.test_cases;
        }
        
        const content = `
            <h5>${problem.title}</h5>
            <p><strong>難易度:</strong> ${problem.difficulty}</p>
            <p><strong>説明:</strong></p>
            <p>${problem.description}</p>
            <p><strong>テストケース:</strong></p>
            <pre class="code-block">${testCases}</pre>
            <p><strong>期待される出力:</strong></p>
            <pre class="code-block">${problem.expected_output}</pre>
        `;
        
        document.getElementById('submissionDetails').innerHTML = content;
        const modal = new bootstrap.Modal(document.getElementById('submissionModal'));
        modal.show();
        
    } catch (error) {
        console.error('問題詳細読み込みエラー:', error);
        showAlert('問題詳細の読み込みに失敗しました', 'danger');
    }
}

async function loadSubmissions(problemId = null) {
    try {
        let url = '/api/submissions/';
        if (problemId) {
            url += `?problem_id=${problemId}`;
        }
        
        const response = await fetch(url);
        const submissions = await response.json();
        
        const submissionsList = document.getElementById('submissionsList');
        
        if (submissions.length === 0) {
            submissionsList.innerHTML = '<p class="text-muted">提出がありません</p>';
            return;
        }
        
        let html = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>学生名</th>
                            <th>問題ID</th>
                            <th>状態</th>
                            <th>提出日時</th>
                            <th>コスト</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        submissions.forEach(submission => {
            const submittedAt = new Date(submission.created_at).toLocaleString('ja-JP');
            const statusClass = `status-${submission.status}`;
            
            html += `
                <tr>
                    <td>${submission.id}</td>
                    <td>${submission.student_name}</td>
                    <td>${submission.problem_id}</td>
                    <td><span class="submission-status ${statusClass}">${submission.status}</span></td>
                    <td>${submittedAt}</td>
                    <td>${submission.cost} tokens</td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="viewSubmission(${submission.id})">詳細</button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        submissionsList.innerHTML = html;
        
    } catch (error) {
        console.error('提出読み込みエラー:', error);
        showAlert('提出の読み込みに失敗しました', 'danger');
    }
}

async function viewSubmission(submissionId) {
    try {
        const [submissionResponse, adviceResponse] = await Promise.all([
            fetch(`/api/submissions/${submissionId}`),
            fetch(`/api/submissions/${submissionId}/advice`).catch(() => null)
        ]);
        
        const submission = await submissionResponse.json();
        let advice = null;
        
        if (adviceResponse && adviceResponse.ok) {
            advice = await adviceResponse.json();
        }
        
        let content = `
            <div class="row">
                <div class="col-md-6">
                    <h6>提出情報</h6>
                    <p><strong>学生名:</strong> ${submission.student_name}</p>
                    <p><strong>問題ID:</strong> ${submission.problem_id}</p>
                    <p><strong>状態:</strong> ${submission.status}</p>
                    <p><strong>提出日時:</strong> ${new Date(submission.created_at).toLocaleString('ja-JP')}</p>
                    <p><strong>コスト:</strong> ${submission.cost} tokens</p>
                </div>
                <div class="col-md-6">
                    <h6>提出されたコード</h6>
                    <pre class="code-block">${submission.code}</pre>
                </div>
            </div>
        `;
        
        if (advice) {
            content += `
                <hr>
                <div class="row">
                    <div class="col-12">
                        <h6>テスト結果</h6>
                        <p>通過: ${advice.test_results.passed} / ${advice.test_results.total}</p>
                        
                        <h6>アドバイス</h6>
                        <div class="alert alert-info">${advice.advice}</div>
                        
                        ${advice.suggestions.length > 0 ? `
                            <h6>改善提案</h6>
                            <ul>
                                ${advice.suggestions.map(s => `<li>${s}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        document.getElementById('submissionDetails').innerHTML = content;
        const modal = new bootstrap.Modal(document.getElementById('submissionModal'));
        modal.show();
        
    } catch (error) {
        console.error('提出詳細読み込みエラー:', error);
        showAlert('提出詳細の読み込みに失敗しました', 'danger');
    }
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