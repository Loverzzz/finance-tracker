const API_URL = '';
let token = localStorage.getItem('token');
let budgetChart = null;
let currentTransactions = [];

window.onload = () => {
    if (token) {
        showDashboard();
    } else {
        showAuth();
    }
};

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(registration => {
      console.log('SW registered');
    });
  });
}



function showAuth() {
    document.getElementById('auth-container').style.display = 'block';
    document.getElementById('dashboard-container').style.display = 'none';
}

function showDashboard() {
    document.getElementById('auth-container').style.display = 'none';
    document.getElementById('dashboard-container').style.display = 'block';
    fetchDashboardData();
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    showAuth();
}

async function handleAuth(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');
        token = data.access_token;
        localStorage.setItem('token', token);
        showDashboard();
    } catch (err) {
        document.getElementById('auth-error').innerText = err.message;
    }
}

async function fetchWithAuth(url, options = {}) {
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    const res = await fetch(url, options);
    if (res.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    return res;
}

async function fetchDashboardData() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    
    try {
        // Balances
        const balRes = await fetchWithAuth(`${API_URL}/dashboard/balances`);
        if(balRes.ok) {
            const balData = await balRes.json();
            document.getElementById('balance-total').innerText = formatRp(balData.total_money);
            document.getElementById('balance-mandiri').innerText = formatRp(balData.total_mandiri);
            document.getElementById('balance-cash').innerText = formatRp(balData.total_cash);
        }
        
        // Budget Status
        const budRes = await fetchWithAuth(`${API_URL}/dashboard/budget_status/${year}/${month}`);
        if(budRes.ok) {
            const budData = await budRes.json();
            updateBudgetUI(budData);
            autoSetMood(budData.status);
        }
        
        // Daily Budget
        const dailyRes = await fetchWithAuth(`${API_URL}/dashboard/daily_budget`);
        if(dailyRes.ok){
            const dailyData = await dailyRes.json();
            document.getElementById('daily-budget-val').innerText = formatRp(dailyData.daily_budget);
            document.getElementById('days-left-val').innerText = dailyData.days_left;
        }

        // Top Expenses
        const expRes = await fetchWithAuth(`${API_URL}/dashboard/top_expenses`);
        if(expRes.ok){
            const expData = await expRes.json();
            renderTopExpenses(expData);
        }

        // Recent Transactions
        const recRes = await fetchWithAuth(`${API_URL}/transactions/?limit=5`);
        if(recRes.ok){
            const recData = await recRes.json();
            renderRecentTransactions(recData);
        }
    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

function formatRp(val) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0);
}

function updateBudgetUI(data) {
    const badge = document.getElementById('budget-status-badge');
    badge.className = `badge ${data.status}`;
    let statusText = "Aman";
    if (data.status === 'potensi_over_budget') statusText = "Potensi Over Budget";
    if (data.status === 'over_budget') statusText = "Over Budget";
    badge.innerText = statusText;
    
    const remaining = Math.max(0, data.total_goal - data.total_spent);
    
    const ctx = document.getElementById('budgetChart').getContext('2d');
    if (budgetChart) budgetChart.destroy();
    
    // Default color logic
    const colorNeeds = '#f43f5e';
    const colorWants = '#f59e0b';
    const colorSavings = '#38bdf8';
    const colorRem = '#10b981';

    budgetChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Needs', 'Wants', 'Savings', 'Remaining'],
            datasets: [{
                data: [
                    data.needs_spent, 
                    data.wants_spent, 
                    data.savings_spent,
                    remaining
                ],
                backgroundColor: [colorNeeds, colorWants, colorSavings, colorRem],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { position: 'right', labels: { color: '#f8fafc', font: { family: 'Outfit'} } }
            }
        }
    });
}

function renderTopExpenses(data) {
    const list = document.getElementById('top-expenses-list');
    list.innerHTML = '';
    if(data.length === 0){
        list.innerHTML = '<li style="justify-content:center; color:#94a3b8;">No expenses this month yet.</li>';
        return;
    }
    data.forEach(item => {
        list.innerHTML += `
            <li>
                <div>
                    <span class="expense-name">${item.toko}</span>
                    <span class="expense-cat">${item.category}</span>
                </div>
                <span class="expense-amount">${formatRp(item.amount)}</span>
            </li>
        `;
    });
}

function renderRecentTransactions(data) {
    currentTransactions = data;
    const list = document.getElementById('recent-transactions-list');
    list.innerHTML = '';
    if(data.length === 0){
        list.innerHTML = '<li style="justify-content:center; color:#94a3b8;">No recent transactions.</li>';
        return;
    }
    data.forEach(item => {
        let title = item.toko;
        if(item.tipe_kirim === 'Transfer') title += ' 🔃';
        const color = item.tipe_kirim === 'Pemasukan' ? '#10b981' : (item.tipe_kirim === 'Transfer' ? '#8b5cf6' : '#f43f5e');
        const sign = item.tipe_kirim === 'Pemasukan' ? '+' : (item.tipe_kirim === 'Transfer' ? '' : '-');
        
        list.innerHTML += `
            <li style="display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1;">
                    <span class="expense-name">${title}</span>
                    <span class="expense-cat">${item.category}</span>
                    <div style="font-size:0.8rem; color:#94a3b8;">${item.tanggal_struk} (${item.method})</div>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="expense-amount" style="color: ${color}; margin-right: 15px;">
                        ${sign}${formatRp(item.amount)}
                    </span>
                    <button class="icon-btn" style="width:35px; height:35px; font-size:0.9rem;" onclick="editTransaction(${item.id})"><i class="fa-solid fa-pen"></i></button>
                    <button class="icon-btn" style="width:35px; height:35px; font-size:0.9rem; background:rgba(239, 68, 68, 0.2); color:#ef4444;" onclick="deleteTransaction(${item.id})"><i class="fa-solid fa-trash"></i></button>
                </div>
            </li>
        `;
    });
}

function autoSetMood(status) {
    let emoji = '😎'; 
    let text = 'Aman';
    if (status === 'potensi_over_budget') { emoji = '😐'; text = 'Hati-hati'; }
    if (status === 'over_budget') { emoji = '😡'; text = 'Bahaya!'; }
    
    document.getElementById('current-mood-val').innerText = `${emoji} ${text}`;
    
    const btns = document.querySelectorAll('.mood-btn');
    btns.forEach(b => {
        if(b.innerText.includes(emoji)) {
            b.style.filter = 'grayscale(0%)';
            b.style.transform = 'scale(1.3)';
        } else {
            b.style.filter = 'grayscale(100%)';
            b.style.transform = 'scale(1)';
        }
    });
}

// Modals
function openTransactionModal() { 
    document.getElementById('transaction-form').reset();
    document.getElementById('t_id').value = '';
    document.getElementById('t_method').disabled = false;
    document.getElementById('transaction-modal-title').innerText = 'Record Transaction';
    document.getElementById('transaction-modal').style.display = 'flex'; 
}

function editTransaction(id) {
    const t = currentTransactions.find(x => x.id === id);
    if(!t) return;
    
    document.getElementById('transaction-modal-title').innerText = 'Edit Transaction';
    document.getElementById('t_id').value = t.id;
    document.getElementById('t_tipe_kirim').value = t.tipe_kirim;
    document.getElementById('t_tipe_kirim').dispatchEvent(new Event('change'));
    
    document.getElementById('t_tanggal_struk').value = t.tanggal_struk;
    document.getElementById('t_toko').value = t.toko;
    document.getElementById('t_total_item').value = t.total_item;
    document.getElementById('t_category').value = t.category;
    document.getElementById('t_method').value = t.method;
    document.getElementById('t_amount').value = t.amount;
    
    document.getElementById('transaction-modal').style.display = 'flex';
}

async function deleteTransaction(id) {
    if(!confirm('Are you sure you want to delete this transaction?')) return;
    try {
        const res = await fetchWithAuth(`${API_URL}/transactions/${id}`, { method: 'DELETE' });
        if(res.ok) {
            fetchDashboardData();
        } else {
            alert('Failed to delete transaction.');
        }
    } catch(err) { alert(err.message); }
}

function closeTransactionModal() { document.getElementById('transaction-modal').style.display = 'none'; }
function openBudgetModal() { 
    const now = new Date();
    document.getElementById('b_month').value = now.getMonth() + 1;
    document.getElementById('b_year').value = now.getFullYear();
    document.getElementById('budget-modal').style.display = 'flex'; 
}
function closeBudgetModal() { document.getElementById('budget-modal').style.display = 'none'; }

document.getElementById('t_tipe_kirim').addEventListener('change', function(e) {
    const type = e.target.value;
    const catSelect = document.getElementById('t_category');
    const methodSelect = document.getElementById('t_method');
    
    if (type === 'Transfer') {
        catSelect.innerHTML = `
            <option value="Tarik Tunai">Tarik Tunai (Mandiri ➡️ Cash)</option>
            <option value="Setor Tunai">Setor Tunai (Cash ➡️ Mandiri)</option>
        `;
        methodSelect.disabled = true;
    } else {
        catSelect.innerHTML = `
            <option value="Needs">Needs</option>
            <option value="Wants">Wants</option>
            <option value="Savings">Savings</option>
            ${type === 'Pemasukan' ? '<option value="Income">Income (Pemasukan)</option>' : ''}
        `;
        methodSelect.disabled = false;
    }
});

document.getElementById('b_mode').addEventListener('change', async function(e) {
    const isPercent = e.target.value === 'percentage';
    document.getElementById('b_income_info').style.display = isPercent ? 'block' : 'none';
    
    document.querySelector('label[for="b_needs"]').innerText = isPercent ? 'Needs Target (%)' : 'Needs Target (Rp)';
    document.querySelector('label[for="b_wants"]').innerText = isPercent ? 'Wants Target (%)' : 'Wants Target (Rp)';
    document.querySelector('label[for="b_savings"]').innerText = isPercent ? 'Savings Target (%)' : 'Savings Target (Rp)';
    
    if (isPercent) {
        const m = document.getElementById('b_month').value;
        const y = document.getElementById('b_year').value;
        if (m && y) {
            try {
                const res = await fetchWithAuth(`${API_URL}/dashboard/income/${y}/${m}`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('b_total_income_val').innerText = formatRp(data.total_income);
                    document.getElementById('b_total_income_val').dataset.val = data.total_income;
                }
            } catch(e) {}
        }
    }
});

['b_month', 'b_year'].forEach(id => {
    document.getElementById(id).addEventListener('change', () => {
        if (document.getElementById('b_mode').value === 'percentage') {
            document.getElementById('b_mode').dispatchEvent(new Event('change'));
        }
    });
});

async function submitTransaction(e) {
    e.preventDefault();
    const data = {
        tipe_kirim: document.getElementById('t_tipe_kirim').value,
        tanggal_struk: document.getElementById('t_tanggal_struk').value,
        toko: document.getElementById('t_toko').value,
        total_item: parseInt(document.getElementById('t_total_item').value),
        category: document.getElementById('t_category').value,
        method: document.getElementById('t_method').disabled ? 'Mandiri' : document.getElementById('t_method').value,
        amount: parseFloat(document.getElementById('t_amount').value)
    };
    
    try {
        const t_id = document.getElementById('t_id').value;
        const url = t_id ? `${API_URL}/transactions/${t_id}` : `${API_URL}/transactions/`;
        const method = t_id ? 'PUT' : 'POST';

        const res = await fetchWithAuth(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            closeTransactionModal();
            fetchDashboardData();
            document.getElementById('transaction-form').reset();
        } else {
            const err = await res.json();
            alert('Error: ' + JSON.stringify(err));
        }
    } catch(err) { alert('Failed to save transaction: ' + err.message); }
}

async function submitBudget(e) {
    e.preventDefault();
    const mode = document.getElementById('b_mode').value;
    let n = parseFloat(document.getElementById('b_needs').value);
    let w = parseFloat(document.getElementById('b_wants').value);
    let s = parseFloat(document.getElementById('b_savings').value);
    
    if (mode === 'percentage') {
        const totalIncome = parseFloat(document.getElementById('b_total_income_val').dataset.val || 0);
        n = (n / 100) * totalIncome;
        w = (w / 100) * totalIncome;
        s = (s / 100) * totalIncome;
    }

    const data = {
        month: parseInt(document.getElementById('b_month').value),
        year: parseInt(document.getElementById('b_year').value),
        needs_target_amount: n,
        wants_target_amount: w,
        savings_target_amount: s
    };
    try {
        const res = await fetchWithAuth(`${API_URL}/budgets/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            closeBudgetModal();
            fetchDashboardData();
        } else {
            const err = await res.json();
            alert('Error: ' + JSON.stringify(err));
        }
    } catch(err) { alert('Failed to save budget'); }
}
