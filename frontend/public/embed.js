;(function () {
  const ATTR_KEY = 'data-embed-key'
  function createWidget(host) {
    const shadow = host.attachShadow({ mode: 'open' })
    const style = document.createElement('style')
    style.textContent = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.box {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 420px;
  height: 600px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(0);
  z-index: 2147483647;
  color: #2d3748;
  font-size: 14px;
  line-height: 1.5;
}

.box *, .box *::before, .box *::after {
  box-sizing: border-box;
}

.box.opening {
  animation: slideInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(100px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.head {
  padding: 20px 24px 16px;
  background: #2d3748;
  color: white;
  position: relative;
  border-radius: 20px 20px 0 0;
}

.head-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-title::before {
  content: '';
  width: 20px;
  height: 20px;
  background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+CiAgPHBhdGggZD0iTTEyIDhWNEg4Ii8+CiAgPHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjEyIiB4PSI0IiB5PSI4IiByeD0iMiIvPgogIDxwYXRoIGQ9Ik0yIDE0aDIiLz4KICA8cGF0aCBkPSJNMjAgMTRoMiIvPgogIDxwYXRoIGQ9Ik0xNSAxM3YyIi8+CiAgPHBhdGggZD0iTTkgMTN2MiIvPgo8L3N2Zz4=');
  background-repeat: no-repeat;
  background-size: contain;
  display: inline-block;
}

.head-subtitle {
  font-size: 13px;
  opacity: 0.8;
  margin: 4px 0 0 32px;
  font-weight: 400;
}

.head-close {
  position: absolute;
  right: 16px;
  top: 16px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  font-weight: 600;
  cursor: pointer;
  line-height: 1;
  font-size: 16px;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.head-close:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.messages {
  flex: 1;
  padding: 20px 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #f7fafc;
  scrollbar-width: thin;
  scrollbar-color: rgba(74, 85, 104, 0.2) transparent;
}

.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background: rgba(74, 85, 104, 0.2);
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: rgba(74, 85, 104, 0.3);
}

.msg {
  display: flex;
  margin-bottom: 4px;
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.msg.user {
  justify-content: flex-end;
}

.msg.ai {
  justify-content: flex-start;
}

.bubble {
  max-width: 85%;
  padding: 14px 16px;
  border-radius: 18px;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.5;
  position: relative;
}

.msg.user .bubble {
  background: #4a5568;
  color: white;
  border-bottom-right-radius: 6px;
  box-shadow: 0 4px 12px rgba(74, 85, 104, 0.3);
}

.msg.ai .bubble {
  background: rgba(74, 85, 104, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  color: #2d3748;
}

.foot {
  display: flex;
  gap: 12px;
  padding: 20px 16px;
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 0 0 20px 20px;
}

.foot .input-wrap {
  flex: 1;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  transition: all 0.2s ease;
  display: flex;
  align-items: stretch;
  min-height: 44px;
}

.foot textarea {
  flex: 1;
  border: none;
  padding: 12px 16px;
  font: inherit;
  font-size: 14px;
  color: #2d3748;
  background: transparent;
  outline: none;
  resize: none;
  height: 66px;
  overflow-y: auto;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.4;
  scrollbar-gutter: stable;
  padding-right: 18px;
  background-clip: padding-box;
}

.foot .input-wrap:focus-within {
  border-color: #4a5568;
  background: white;
  box-shadow: 0 0 0 3px rgba(74, 85, 104, 0.1);
}

.foot textarea::placeholder {
  color: #a0aec0;
}

/* Textarea scrollbar adjustments (WebKit) */
.foot textarea::-webkit-scrollbar { width: 8px; }
.foot textarea::-webkit-scrollbar-track { margin: 6px; border-radius: 8px; background: transparent; }
.foot textarea::-webkit-scrollbar-thumb { background: rgba(74, 85, 104, 0.3); border-radius: 8px; }
.foot textarea::-webkit-scrollbar-thumb:hover { background: rgba(74, 85, 104, 0.45); cursor: pointer; }
/* Default cursor for text editing */
.foot textarea { cursor: text; }

.foot button {
  border: none;
  background: #4a5568;
  color: white;
  border-radius: 14px;
  padding: 12px 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  min-width: 64px;
  height: 44px;
  align-self: flex-end;
  box-shadow: 0 4px 12px rgba(74, 85, 104, 0.3);
}

.foot button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(74, 85, 104, 0.4);
  background: #2d3748;
}

.foot button:active:not(:disabled) {
  transform: translateY(0);
}

.foot button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 4px 12px rgba(74, 85, 104, 0.2);
}

.typing {
  font-size: 13px;
  color: #718096;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.typing::after {
  content: '';
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #4a5568;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Markdown styles */
.bubble h1, .bubble h2, .bubble h3 {
  margin: 0.6em 0 0.4em;
  font-weight: 600;
  color: inherit;
}

.bubble h1 { font-size: 19px; }
.bubble h2 { font-size: 17px; }
.bubble h3 { font-size: 16px; }

.bubble p {
  margin: 0.4em 0;
  line-height: 1.6;
}

.bubble code {
  background: rgba(74, 85, 104, 0.1);
  border: 1px solid rgba(74, 85, 104, 0.2);
  border-radius: 6px;
  padding: 2px 6px;
  font-family: 'JetBrains Mono', 'SF Mono', Monaco, Consolas, monospace;
  font-size: 13px;
}

.msg.user .bubble code {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.95);
}

.bubble pre {
  background: #222;
  color: #f7fafc;
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
  box-shadow: 0 4px 12px rgba(45, 55, 72, 0.3);
}

.bubble pre code {
  background: transparent;
  border: none;
  padding: 0;
  color: inherit;
  font-size: 13px;
}

.bubble ul, .bubble ol {
  margin: 0.8em 0;
  padding-left: 20px;
}

.bubble li {
  margin: 0.3em 0;
  line-height: 1.5;
}

.bubble a {
  color: #2d3748;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.bubble a:hover {
  color: #4a5568;
  text-decoration: underline;
}

.msg.user .bubble a {
  color: rgba(255, 255, 255, 0.9);
}

.msg.user .bubble a:hover {
  color: white;
}

.bubble blockquote {
  border-left: 4px solid #4a5568;
  margin: 0.6em 0;
  padding: 0.4em 1em;
  color: #4a5568;
  background: rgba(74, 85, 104, 0.05);
  border-radius: 0 8px 8px 0;
}

.msg.user .bubble blockquote {
  border-left-color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
}

.bubble hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 1em 0;
}


/* Toggle button */
.toggle {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #4a5568;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 10px 25px rgba(74, 85, 104, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  cursor: pointer;
  font-size: 24px;
  z-index: 2147483647;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.toggle:hover {
  transform: scale(1.1) translateY(-2px);
  box-shadow: 
    0 15px 35px rgba(74, 85, 104, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.3);
  background: #2d3748;
}

.toggle:active {
  transform: scale(1.05);
}

.toggle.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 
      0 10px 25px rgba(74, 85, 104, 0.4),
      0 0 0 0 rgba(74, 85, 104, 0.7);
  }
  70% {
    box-shadow: 
      0 10px 25px rgba(74, 85, 104, 0.4),
      0 0 0 10px rgba(74, 85, 104, 0);
  }
  100% {
    box-shadow: 
      0 10px 25px rgba(74, 85, 104, 0.4),
      0 0 0 0 rgba(74, 85, 104, 0);
  }
}

/* Responsive design */
@media (max-width: 480px) {
  .box {
    right: 16px;
    bottom: 16px;
    left: 16px;
    width: auto;
    height: 500px;
  }
  
  .toggle {
    right: 16px;
    bottom: 16px;
    width: 50px;
    height: 50px;
    font-size: 22px;
  }
}

/* Welcome message styles */
.welcome-message {
  background: rgba(74, 85, 104, 0.05);
  border: 1px solid rgba(74, 85, 104, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #4a5568;
  line-height: 1.5;
}

.welcome-message strong {
  color: #2d3748;
  font-weight: 600;
}

/* Error message styles */
.error-message {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #dc2626;
  line-height: 1.5;
  animation: fadeInUp 0.3s ease-out;
}

.error-message strong {
  color: #b91c1c;
  font-weight: 600;
}

.error-message .error-title {
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-message .error-title::before {
  content: '⚠️';
  font-size: 16px;
}

.error-message .error-details {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 6px;
}

.error-message .error-retry {
  margin-top: 12px;
  text-align: center;
}

.error-message .retry-btn {
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.error-message .retry-btn:hover {
  background: #b91c1c;
  transform: translateY(-1px);
}

.warning-message {
  background: rgba(245, 158, 11, 0.05);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #d97706;
  line-height: 1.5;
  animation: fadeInUp 0.3s ease-out;
}

.warning-message strong {
  color: #b45309;
  font-weight: 600;
}

.warning-message .warning-title {
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.warning-message .warning-title::before {
  content: '⏰';
  font-size: 16px;
}
`
    const container = document.createElement('div')

    const box = document.createElement('div')
    box.className = 'box'
    box.innerHTML = `
      <div class="head">
        <div class="head-title">AI サポートデスク</div>
        <div class="head-subtitle">24時間いつでも対応可能！</div>
        <button class="head-close" aria-label="閉じる">✕</button>
      </div>
      <div class="messages">
        <div class="welcome-message">
          <strong>こんにちは！</strong><br>ご質問やお困りごとがございましたら、お気軽にお声がけください。
        </div>
      </div>
      <div class="foot">
        <div class="input-wrap">
          <textarea placeholder="ご質問をお聞かせください...&#10;Shift+Enterで改行"></textarea>
        </div>
        <button>送信</button>
      </div>
    `

    const toggleBtn = document.createElement('button')
    toggleBtn.className = 'toggle pulse'
    toggleBtn.setAttribute('aria-label', 'チャットを開く')
    toggleBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 8V4H8"/>
      <rect width="16" height="12" x="4" y="8" rx="2"/>
      <path d="M2 14h2"/>
      <path d="M20 14h2"/>
      <path d="M15 13v2"/>
      <path d="M9 13v2"/>
    </svg>`

    container.appendChild(box)
    container.appendChild(toggleBtn)
    shadow.append(style, container)

    const messages = box.querySelector('.messages')
    const textarea = box.querySelector('.foot textarea')
    const sendBtn = box.querySelector('.foot button')
    const headClose = box.querySelector('.head-close')

    // ===== Markdown library loader (marked + DOMPurify) =====
    const MARKED_URL = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js'
    const PURIFY_URL =
      'https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js'
    function loadScript(src) {
      return new Promise((resolve, reject) => {
        const s = document.createElement('script')
        s.src = src
        s.async = true
        s.crossOrigin = 'anonymous'
        s.onload = () => resolve()
        s.onerror = () => reject(new Error('Failed to load ' + src))
        document.head.appendChild(s)
      })
    }
    loadScript(MARKED_URL).catch(() => {})
    loadScript(PURIFY_URL).catch(() => {})

    function escapeHtml(s) {
      return (s || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\"/g, '&quot;')
        .replace(/'/g, '&#39;')
    }

    function preprocessMarkdown(text) {
      let s = String(text || '')
      s = s
        .trim()
        .replace(/^```\s*(?:markdown|md)\s*\n([\s\S]*?)\n```\s*$/i, '$1')
      s = s.replace(/^(?:markdown|md)\s*\n/i, '')
      return s
    }

    function simpleRenderMarkdown(md) {
      let s = preprocessMarkdown(md)
      s = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      s = s.replace(
        /```\s*([a-z0-9+-]*)\n([\s\S]*?)```/gi,
        function (_, lang, code) {
          const langLabel = lang
            ? `<div style=\"font-size:12px;color:#9ca3af;margin-bottom:4px\">${lang}</div>`
            : ''
          return `${langLabel}<pre><code>${code.replace(/\n$/, '')}</code></pre>`
        }
      )
      s = s.replace(/`([^`]+?)`/g, '<code>$1</code>')
      s = s.replace(/^\s*[-*_]{3,}\s*$/gm, '<hr/>')
      s = s.replace(/^>\s?(.+)$/gm, '<blockquote>$1</blockquote>')
      s = s
        .replace(/^###\s+(.+)$/gm, '<h3>$1</h3>')
        .replace(/^##\s+(.+)$/gm, '<h2>$1</h2>')
        .replace(/^#\s+(.+)$/gm, '<h1>$1</h1>')
      s = s.replace(
        /\[([^\]]+)\]\((https?:[^\s)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
      )
      s = s
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      if (/^\s*[-*]\s+/m.test(s)) {
        s = s.replace(/^(?:[-*])\s+(.+)$/gm, '<li>$1</li>')
        s = s.replace(/(<li>[^<]*<\/li>\n?)+/g, function (block) {
          const items = block.trim().replace(/\n/g, '')
          return '<ul>' + items + '</ul>'
        })
      }
      if (/^\s*\d+\.\s+/m.test(s)) {
        s = s.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
        s = s.replace(/(<li>[^<]*<\/li>\n?)+/g, function (block) {
          const items = block.trim().replace(/\n/g, '')
          return '<ol>' + items + '</ol>'
        })
      }
      s = s
        .split(/\n{2,}/)
        .map(p => {
          if (/^\s*<(h\d|ul|ol|pre|blockquote|hr|table|div)/.test(p)) return p
          return '<p>' + p.replace(/\n/g, '<br/>') + '</p>'
        })
        .join('\n')
      return s
    }

    function renderMarkdown(md) {
      const s = preprocessMarkdown(md)
      try {
        if (window.marked) {
          const html = window.marked.parse(s)
          if (window.DOMPurify) return window.DOMPurify.sanitize(html)
          return html
        }
      } catch {}
      return simpleRenderMarkdown(s)
    }

    function appendMessage(role, html) {
      const wrap = document.createElement('div')
      wrap.className = 'msg ' + (role === 'user' ? 'user' : 'ai')
      const b = document.createElement('div')
      b.className = 'bubble'
      if (role === 'user') {
        b.innerHTML = html.replace(/\n/g, '<br>')
      } else {
        b.innerHTML = html
      }
      wrap.appendChild(b)
      messages.appendChild(wrap)
      messages.scrollTop = messages.scrollHeight
      return b
    }

    function appendErrorMessage(errorType, title, details, showRetry = false) {
      const errorDiv = document.createElement('div')
      errorDiv.className =
        errorType === 'warning' ? 'warning-message' : 'error-message'

      let retryButton = ''
      if (showRetry) {
        retryButton =
          '<div class="error-retry"><button class="retry-btn" onclick="location.reload()">再読み込み</button></div>'
      }

      errorDiv.innerHTML = `
        <div class="${errorType === 'warning' ? 'warning-title' : 'error-title'}">${escapeHtml(title)}</div>
        <div class="${errorType === 'warning' ? 'warning-details' : 'error-details'}">${escapeHtml(details)}</div>
        ${retryButton}
      `

      messages.appendChild(errorDiv)
      messages.scrollTop = messages.scrollHeight
      return errorDiv
    }

    function showTyping() {
      const el = appendMessage(
        'ai',
        '<span class="typing">回答を生成しています</span>'
      )
      return {
        remove() {
          el.parentElement && el.parentElement.remove()
        },
      }
    }

    function getErrorMessage(status, responseText) {
      switch (status) {
        case 401:
          return {
            type: 'error',
            title: '認証エラー',
            details:
              '埋め込みキーが無効です。サイト管理者にお問い合わせください。',
            showRetry: false,
          }
        case 429:
          return {
            type: 'warning',
            title: 'アクセス制限',
            details:
              'リクエストが集中しています。しばらく時間をおいてから再度お試しください。',
            showRetry: true,
          }
        case 402:
          return {
            type: 'warning',
            title: '利用上限到達',
            details: '本日の利用上限に達しました。明日再度ご利用ください。',
            showRetry: false,
          }
        case 403:
          return {
            type: 'error',
            title: 'アクセス拒否',
            details: 'このサイトからのアクセスは許可されていません。',
            showRetry: false,
          }
        case 500:
        case 502:
        case 503:
        case 504:
          return {
            type: 'error',
            title: 'サーバーエラー',
            details:
              'サーバーで問題が発生しています。しばらく時間をおいてから再度お試しください。',
            showRetry: true,
          }
        default:
          let errorMsg = 'エラーが発生しました。もう一度お試しください。'
          try {
            const errorData = JSON.parse(responseText)
            if (errorData.detail) {
              errorMsg = errorData.detail
            } else if (errorData.message) {
              errorMsg = errorData.message
            }
          } catch {}

          return {
            type: 'error',
            title: 'エラー',
            details: errorMsg,
            showRetry: true,
          }
      }
    }

    function renderFeedback(bubbleEl, apiBase, key, messageId) {
      const wrap = document.createElement('div')
      wrap.style.marginTop = '8px'
      wrap.innerHTML = `
        <div style="display:flex;gap:8px;align-items:center">
          <span style="font-size:12px;color:#718096">この回答は役に立ちましたか？</span>
          <button class="retry-btn">はい</button>
          <button class="retry-btn" style="background:#6b7280">いいえ</button>
        </div>`
      const [yesBtn, noBtn] = wrap.querySelectorAll('button')
      const isTestEnv = host.getAttribute('data-is-test') === 'true'
      const send = async resolved => {
        try {
          const headers = {
            'Content-Type': 'application/json',
            'x-embed-key': key,
          }
          if (isTestEnv) {
            headers['x-test-environment'] = 'true'
          }
          await fetch(`${apiBase}/api/v1/embed/docs/feedback`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ message_id: messageId, resolved }),
          })
        } catch {}
        wrap.innerHTML = `<span style="font-size:12px;color:#718096">ご回答ありがとうございました</span>`
      }
      yesBtn.onclick = () => send(true)
      noBtn.onclick = () => send(false)
      bubbleEl.appendChild(wrap)
    }

    const key = host.getAttribute(ATTR_KEY) || ''
    const apiBase = host.getAttribute('data-api-base') || window.location.origin
    const isTest = host.getAttribute('data-is-test') === 'true'
    // AbortController（現在のリクエストのキャンセル制御）
    let currentController = null
    // タイムアウト（初回バイト/ハートビート）
    const FIRST_BYTE_TIMEOUT_MS = 40000
    const HEARTBEAT_TIMEOUT_MS = 20000

    async function ask(q) {
      appendMessage('user', escapeHtml(q))
      let typing = showTyping()
      sendBtn.disabled = true
      textarea.disabled = true
      // 既存のストリームがあれば中断
      if (currentController) {
        try {
          currentController.abort()
        } catch {}
      }
      let controller = new AbortController()
      currentController = controller
      const { signal } = controller

      // タイムアウト管理（tryの外で宣言し、catch/finallyからも触れるように）
      let timedOut = false
      let gotFirstByte = false
      let toFirstByteTimer = null
      let heartbeatTimer = null
      const clearTimers = () => {
        if (toFirstByteTimer) {
          clearTimeout(toFirstByteTimer)
          toFirstByteTimer = null
        }
        if (heartbeatTimer) {
          clearTimeout(heartbeatTimer)
          heartbeatTimer = null
        }
      }
      const bumpHeartbeat = () => {
        if (!gotFirstByte) return
        if (heartbeatTimer) clearTimeout(heartbeatTimer)
        heartbeatTimer = setTimeout(() => {
          timedOut = true
          try {
            controller.abort()
          } catch {}
        }, HEARTBEAT_TIMEOUT_MS)
      }
      toFirstByteTimer = setTimeout(() => {
        timedOut = true
        try {
          controller.abort()
        } catch {}
      }, FIRST_BYTE_TIMEOUT_MS)

      // 匿名 client_id と session_id の生成・維持（localStorage）
      const CID_KEY = 'tuukaa:client_id'
      const SID_KEY = 'tuukaa:session_id'
      function getOrCreateId(k) {
        try {
          let v = localStorage.getItem(k)
          if (!v) {
            v =
              (crypto.randomUUID && crypto.randomUUID().replace(/-/g, '')) ||
              Math.random().toString(36).slice(2)
            localStorage.setItem(k, v)
          }
          return v
        } catch {
          return Math.random().toString(36).slice(2)
        }
      }
      let clientId = getOrCreateId(CID_KEY)
      let sessionId = getOrCreateId(SID_KEY)

      const messageId =
        (crypto.randomUUID && crypto.randomUUID().replace(/-/g, '')) ||
        String(Date.now())

      try {
        const headers = {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          'x-embed-key': key,
        }
        if (isTest) {
          headers['x-test-environment'] = 'true'
        }

        const res = await fetch(`${apiBase}/api/v1/embed/docs/ask`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            question: q,
            top_k: 10,
            client_id: clientId,
            session_id: sessionId,
            message_id: messageId,
          }),
          signal,
        })

        if (
          res.ok &&
          res.headers.get('content-type')?.includes('text/event-stream')
        ) {
          typing.remove()
          let aiText = ''
          const aiBubble = appendMessage('ai', '')
          const reader = res.body.getReader()
          const dec = new TextDecoder()
          let buf = ''
          while (true) {
            const { value, done } = await reader.read()
            if (done) break
            if (!gotFirstByte) {
              gotFirstByte = true
              if (toFirstByteTimer) {
                clearTimeout(toFirstByteTimer)
                toFirstByteTimer = null
              }
            }
            bumpHeartbeat()
            buf += dec.decode(value, { stream: true })
            const parts = buf.split('\n\n')
            buf = parts.pop()
            for (const rec of parts) {
              let eventName = null
              const dataLines = []
              for (const line of rec.split('\n')) {
                if (line.startsWith('event:')) eventName = line.slice(6).trim()
                else if (line.startsWith('data:'))
                  dataLines.push(line.slice(5).trimStart())
                // ":" で始まるSSEコメント（ハートビート）は無視
              }
              const dataStr = dataLines.join('\n')
              if (eventName === 'citations') {
                // citations情報は無視（参考文書を表示しない）
              } else {
                aiText += dataStr ? dataStr + '\n' : ''
                aiBubble.innerHTML = renderMarkdown(aiText)
              }
            }
          }
          clearTimers()
          renderFeedback(aiBubble, apiBase, key, messageId)
        } else if (!res.ok) {
          typing.remove()
          const responseText = await res.text().catch(() => '')
          const errorInfo = getErrorMessage(res.status, responseText)
          appendErrorMessage(
            errorInfo.type,
            errorInfo.title,
            errorInfo.details,
            errorInfo.showRetry
          )
        } else {
          typing.remove()
          const json = await res.json().catch(() => ({}))
          const answer = json && json.answer ? String(json.answer) : ''
          const html = renderMarkdown(answer)
          const bubble = appendMessage('ai', html)
          // フィードバックUIを表示
          renderFeedback(bubble, apiBase, key, messageId)
        }
      } catch (e) {
        typing.remove()
        // Network errors or CORS issues
        if (e.name === 'AbortError') {
          // ユーザーキャンセル／タイムアウト
          if (typeof timedOut === 'boolean' && timedOut) {
            appendErrorMessage(
              'warning',
              'タイムアウト',
              '一定時間応答がなく接続を中断しました。もう一度お試しください。',
              false
            )
          }
        } else if (e.name === 'TypeError' && e.message.includes('fetch')) {
          appendErrorMessage(
            'error',
            'ネットワークエラー',
            'サーバーに接続できません。ネットワーク接続またはCORS設定を確認してください。',
            true
          )
        } else {
          appendErrorMessage(
            'error',
            '予期しないエラー',
            'エラーが発生しました。もう一度お試しください。',
            true
          )
        }
      } finally {
        clearTimers()
        if (currentController === controller) {
          currentController = null
          sendBtn.disabled = false
          textarea.disabled = false
          textarea.focus()
        }
      }
    }

    sendBtn.addEventListener('click', () => {
      const q = (textarea.value || '').trim()
      if (!q) return
      textarea.value = ''
      ask(q)
    })

    textarea.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        e.stopPropagation()
        sendBtn.click()
      }
    })

    function updateScrollbarCursor(e) {
      const rect = textarea.getBoundingClientRect()
      const dx = rect.right - e.clientX
      const nearScrollbar = dx >= 0 && dx <= 12
      const scrollable = textarea.scrollHeight > textarea.clientHeight
      textarea.style.cursor = nearScrollbar && scrollable ? 'pointer' : 'text'
    }
    textarea.addEventListener('mousemove', updateScrollbarCursor)
    textarea.addEventListener('mouseleave', () => {
      textarea.style.cursor = 'text'
    })

    let open = false
    function setOpen(v) {
      open = !!v
      if (open) {
        box.classList.add('opening')
        toggleBtn.classList.remove('pulse')
      }
      box.style.display = open ? 'flex' : 'none'

      const botIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 8V4H8"/>
        <rect width="16" height="12" x="4" y="8" rx="2"/>
        <path d="M2 14h2"/>
        <path d="M20 14h2"/>
        <path d="M15 13v2"/>
        <path d="M9 13v2"/>
      </svg>`

      toggleBtn.style.display = open ? 'none' : 'flex'
      toggleBtn.innerHTML = open ? '✕' : botIcon
      toggleBtn.setAttribute(
        'aria-label',
        open ? 'チャットを閉じる' : 'チャットを開く'
      )

      if (open) {
        setTimeout(() => {
          textarea.focus()
        }, 300)
      }
    }

    toggleBtn.addEventListener('click', () => setOpen(true))
    headClose.addEventListener('click', () => setOpen(false))
    setOpen(false)
  }

  window.addEventListener('DOMContentLoaded', () => {
    const script = document.querySelector('script[data-embed-key]')
    if (!script) return
    const host = document.createElement('div')
    host.setAttribute(
      'data-embed-key',
      script.getAttribute('data-embed-key') || ''
    )
    const apiBase = script.getAttribute('data-api-base')
    if (apiBase) host.setAttribute('data-api-base', apiBase)
    const isTest = script.getAttribute('data-is-test')
    if (isTest) host.setAttribute('data-is-test', isTest)
    script.insertAdjacentElement('afterend', host)
    createWidget(host)
  })
})()
