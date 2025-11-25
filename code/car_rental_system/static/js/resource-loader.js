/**
 * 资源加载优化脚本
 * 处理CDN资源加载超时和失败的情况
 */

(function() {
    'use strict';
    
    // 资源加载超时时间（毫秒）
    const RESOURCE_TIMEOUT = 3000; // 3秒
    
    /**
     * 加载CSS资源，带超时处理
     */
    function loadCSS(href, options = {}) {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.crossOrigin = options.crossOrigin || 'anonymous';
            
            if (options.onError) {
                link.onerror = function() {
                    if (options.fallback) {
                        loadCSS(options.fallback).then(resolve).catch(reject);
                    } else {
                        reject(new Error('Failed to load CSS: ' + href));
                    }
                };
            }
            
            link.onload = function() {
                resolve(link);
            };
            
            // 超时处理
            const timeout = setTimeout(() => {
                if (options.fallback) {
                    link.remove();
                    loadCSS(options.fallback).then(resolve).catch(reject);
                } else {
                    reject(new Error('CSS load timeout: ' + href));
                }
            }, RESOURCE_TIMEOUT);
            
            link.onload = function() {
                clearTimeout(timeout);
                resolve(link);
            };
            
            document.head.appendChild(link);
        });
    }
    
    /**
     * 加载JS资源，带超时处理
     */
    function loadJS(src, options = {}) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.crossOrigin = options.crossOrigin || 'anonymous';
            
            if (options.defer) {
                script.defer = true;
            }
            
            if (options.async) {
                script.async = true;
            }
            
            if (options.onError) {
                script.onerror = function() {
                    if (options.fallback) {
                        loadJS(options.fallback, options).then(resolve).catch(reject);
                    } else {
                        reject(new Error('Failed to load JS: ' + src));
                    }
                };
            }
            
            // 超时处理
            const timeout = setTimeout(() => {
                if (options.fallback) {
                    script.remove();
                    loadJS(options.fallback, options).then(resolve).catch(reject);
                } else {
                    reject(new Error('JS load timeout: ' + src));
                }
            }, RESOURCE_TIMEOUT);
            
            script.onload = function() {
                clearTimeout(timeout);
                resolve(script);
            };
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * 检测资源加载速度
     */
    function checkResourceSpeed(url) {
        return new Promise((resolve) => {
            const startTime = performance.now();
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            
            link.onload = function() {
                const loadTime = performance.now() - startTime;
                resolve({ success: true, time: loadTime });
            };
            
            link.onerror = function() {
                resolve({ success: false, time: Infinity });
            };
            
            // 超时检测
            setTimeout(() => {
                if (!link.sheet) {
                    resolve({ success: false, time: Infinity });
                }
            }, RESOURCE_TIMEOUT);
            
            document.head.appendChild(link);
        });
    }
    
    /**
     * 优化资源加载顺序
     */
    function optimizeResourceLoading() {
        // 如果CDN加载慢，可以考虑使用本地资源
        const cdnBootstrap = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css';
        const localBootstrap = '/static/css/bootstrap.min.css';
        
        // 检测CDN速度
        checkResourceSpeed(cdnBootstrap).then(result => {
            if (!result.success || result.time > 2000) {
                // CDN加载失败或超过2秒，使用本地资源
                console.warn('CDN加载慢，建议使用本地资源');
            }
        });
    }
    
    // 导出函数
    window.ResourceLoader = {
        loadCSS: loadCSS,
        loadJS: loadJS,
        checkResourceSpeed: checkResourceSpeed,
        optimizeResourceLoading: optimizeResourceLoading
    };
    
    // 页面加载完成后优化资源
    if (document.readyState === 'complete') {
        optimizeResourceLoading();
    } else {
        window.addEventListener('load', optimizeResourceLoading);
    }
})();

