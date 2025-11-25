// 租车管理系统主要JavaScript功能

// 页面加载处理 - 优化版本，不等待外部资源
(function() {
    'use strict';
    
    // 立即初始化关键功能，不等待DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        // DOM已经加载完成，立即初始化
        initAll();
    }
    
    function initAll() {
        // 初始化所有功能
        initSidebarToggle();
        initConfirmDialogs();
        initFormValidation();
        initAjaxLoading();
        initTooltips();
        initDataTables();
        initPageLoader();
        initDismissButtons();
        
        // 添加页面加载完成标记
        document.body.classList.add('page-loaded');
    }
})();

// 页面加载器初始化
function initPageLoader() {
    const pageLoader = document.getElementById('pageLoader');
    const pageContent = document.querySelector('.page-content-wrapper') || document.querySelector('.page-content');
    
    if (pageLoader && pageContent) {
        // 页面加载完成后隐藏加载器并显示内容
        function hideLoader() {
            setTimeout(function() {
                if (pageLoader) {
                    pageLoader.classList.add('hidden');
                }
                if (pageContent) {
                    pageContent.classList.add('page-loaded');
                    pageContent.style.opacity = '1';
                }
            }, 100);
        }
        
        // 如果页面已经加载完成（从缓存加载）
        if (document.readyState === 'complete') {
            hideLoader();
        } else {
            // 等待页面完全加载
            window.addEventListener('load', hideLoader);
        }
    }
}

// 页面跳转前的处理
document.addEventListener('click', function(e) {
    const link = e.target.closest('a[href]');
    
    // 排除下拉菜单、模态框、工具提示等交互元素
    if (link && 
        !link.hasAttribute('target') && 
        !link.hasAttribute('data-ajax') && 
        !link.hasAttribute('data-confirm') &&
        !link.hasAttribute('data-bs-toggle') && // 排除Bootstrap下拉菜单等
        !link.closest('.dropdown-menu') && // 排除下拉菜单内的链接
        !link.closest('.modal') && // 排除模态框内的链接
        !link.closest('[data-bs-toggle="dropdown"]') && // 排除下拉菜单触发器
        link.hostname === window.location.hostname &&
        link.href !== window.location.href) {
        
        // 显示加载器
        const pageLoader = document.getElementById('pageLoader');
        const pageContent = document.querySelector('.page-content, .page-content-wrapper');
        
        if (pageLoader && pageContent) {
            // 添加过渡效果
            pageContent.style.transition = 'opacity 0.15s ease-out';
            pageContent.style.opacity = '0';
            
            // 显示加载器（延迟一点，让内容先淡出）
            setTimeout(function() {
                if (pageLoader) {
                    pageLoader.classList.remove('hidden');
                }
            }, 50);
        }
    }
});

// 侧边栏折叠/展开功能
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    
    // 如果当前页面没有侧边栏，直接跳过
    if (!sidebar || !mainContent) {
        return;
    }
    
    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', function() {
            // 检查是否在移动端
            if (window.innerWidth <= 768) {
                // 移动端：切换显示/隐藏
                sidebar.classList.toggle('show');
                mainContent.classList.toggle('mobile-open');
            } else {
                // 桌面端：折叠/展开
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            }
            
            // 保存状态到localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }
    
    if (sidebar && mainContent) {
    // 恢复侧边栏状态
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true' && window.innerWidth > 768) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
        }
    }
    
    // 窗口大小改变时处理
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && sidebar && mainContent) {
            sidebar.classList.remove('show');
            mainContent.classList.remove('mobile-open');
        }
    });
}

// 确认对话框功能
function initConfirmDialogs() {
    // 为所有带有data-confirm属性的链接和按钮添加确认对话框
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-confirm]');
        if (target) {
            e.preventDefault();
            const message = target.getAttribute('data-confirm') || '确定要执行此操作吗？';
            const form = target.closest('form');
            
            showConfirmDialog(message, function() {
                if (form) {
                    form.submit();
                } else {
                    window.location.href = target.href;
                }
            });
        }
    });
}

// 显示确认对话框
function showConfirmDialog(message, callback) {
    if (!window.bootstrap || !window.bootstrap.Modal) {
        if (window.confirm(message)) {
            if (callback) callback();
        }
        return;
    }
    
    // 创建确认对话框的HTML
    const confirmDialog = document.createElement('div');
    confirmDialog.className = 'modal fade';
    confirmDialog.id = 'confirmDialog';
    confirmDialog.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                        确认操作
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times me-1"></i>取消
                    </button>
                    <button type="button" class="btn btn-primary" id="confirmButton">
                        <i class="fas fa-check me-1"></i>确定
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(confirmDialog);
    
    // 显示对话框
    const modal = new bootstrap.Modal(confirmDialog);
    modal.show();
    
    // 绑定确认按钮事件
    confirmDialog.querySelector('#confirmButton').addEventListener('click', function() {
        modal.hide();
        if (callback) callback();
    });
    
    // 清理
    confirmDialog.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(confirmDialog);
    });
}

// 表单验证增强
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // 添加实时验证
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
        
        // 表单提交验证
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// 验证单个字段
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');
    
    // 清除之前的错误
    clearFieldError(field);
    
    // 必填字段验证
    if (required && !value) {
        showFieldError(field, '此字段为必填项');
        return false;
    }
    
    // 特定类型验证
    switch (type) {
        case 'email':
            if (value && !isValidEmail(value)) {
                showFieldError(field, '请输入有效的邮箱地址');
                return false;
            }
            break;
        case 'tel':
            if (value && !isValidPhone(value)) {
                showFieldError(field, '请输入有效的手机号码');
                return false;
            }
            break;
        case 'number':
            if (value && isNaN(value)) {
                showFieldError(field, '请输入有效的数字');
                return false;
            }
            break;
    }
    
    return true;
}

// 显示字段错误
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

// 清除字段错误
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

// 验证整个表单
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// 邮箱验证
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 手机号验证
function isValidPhone(phone) {
    const re = /^1[3-9]\d{9}$/;
    return re.test(phone);
}

// Ajax加载状态
function initAjaxLoading() {
    // 为所有表单添加加载状态
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                showButtonLoading(submitBtn);
            }
        });
    });
    
    // 为所有Ajax链接添加加载状态
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-ajax]');
        if (target) {
            e.preventDefault();
            const originalText = target.textContent;
            showElementLoading(target);
            
            // 模拟Ajax请求
            setTimeout(() => {
                hideElementLoading(target, originalText);
                if (target.href) {
                    window.location.href = target.href;
                }
            }, 1000);
        }
    });
}

// 显示按钮加载状态
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="loading me-1"></span>处理中...';
    button.setAttribute('data-original-text', originalText);
}

// 隐藏按钮加载状态
function hideButtonLoading(button) {
    const originalText = button.getAttribute('data-original-text');
    button.disabled = false;
    button.innerHTML = originalText;
    button.removeAttribute('data-original-text');
}

// 显示元素加载状态
function showElementLoading(element) {
    if (element.tagName === 'BUTTON') {
        showButtonLoading(element);
    } else {
        element.style.opacity = '0.6';
        element.style.pointerEvents = 'none';
    }
}

// 隐藏元素加载状态
function hideElementLoading(element, originalText) {
    if (element.tagName === 'BUTTON') {
        hideButtonLoading(element);
    } else {
        element.style.opacity = '';
        element.style.pointerEvents = '';
        if (originalText) {
            element.textContent = originalText;
        }
    }
}

// 初始化工具提示
function initTooltips() {
    if (!window.bootstrap || !window.bootstrap.Tooltip) return;
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 关闭按钮
function initDismissButtons() {
    document.addEventListener('click', function(e) {
        const button = e.target.closest('[data-dismiss="alert"]');
        if (button) {
            const alert = button.closest('.alert');
            if (alert) {
                alert.remove();
            }
        }
    });
}

// 初始化数据表格
function initDataTables() {
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        // 如果有分页、搜索等功能，可以在这里初始化DataTables
        // 暂时只添加基础功能
        table.addEventListener('click', function(e) {
            const target = e.target.closest('tr');
            if (target && target.dataset.href) {
                window.location.href = target.dataset.href;
            }
        });
    });
}

// 通用Ajax请求函数
function ajaxRequest(url, method = 'GET', data = null, callback = null) {
    const options = {
        method: method,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    fetch(url, options)
        .then(response => response.json())
        .then(data => {
            if (callback) callback(data);
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('请求失败，请重试', 'danger');
        });
}

// 显示警告消息
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // 自动关闭
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, duration);
}

// 创建警告消息容器
function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// 实时费用计算
function calculateRentalCost(startDate, endDate, dailyRate) {
    if (!startDate || !endDate || !dailyRate) return 0;
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const timeDiff = end.getTime() - start.getTime();
    const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
    
    return Math.max(daysDiff, 1) * dailyRate;
}

// 格式化货币
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 搜索功能
function initSearch() {
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const targetTable = document.querySelector(this.dataset.search);
            if (targetTable) {
                filterTable(targetTable, this.value);
            }
        });
    });
}

// 表格搜索过滤
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

// 导出功能
function exportTable(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => {
            return '"' + cell.textContent.replace(/"/g, '""') + '"';
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename || 'data.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// 页面可见性变化处理
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // 页面隐藏时的处理
        console.log('Page hidden');
    } else {
        // 页面显示时的处理
        console.log('Page visible');
        // 可以在这里刷新数据
    }
});

// 错误处理
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    showAlert('系统发生错误，请刷新页面重试', 'danger');
});

// 未处理的Promise拒绝
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showAlert('网络请求失败，请检查网络连接', 'warning');
});