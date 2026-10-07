document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messagesContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chipsContainer = document.getElementById('chipsContainer');

    // Dynamic API URL resolution:
    // If running on local frontend server (e.g. port 5500, 3000 or file://), target backend port 8080
    // If running on Vercel production deployment, target relative endpoint '/api/chat'
    const getApiEndpoint = () => {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        if (protocol === 'file:' || hostname === 'localhost' || hostname === '127.0.0.1') {
            if (window.location.port !== '8080') {
                return 'http://127.0.0.1:8080/chat';
            }
        }
        return '/api/chat';
    };

    const API_ENDPOINT = getApiEndpoint();

    const scrollToBottom = () => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    const getFormattedTime = () => {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const appendUserMessage = (text) => {
        const msgRow = document.createElement('div');
        msgRow.className = 'message-row user';
        msgRow.innerHTML = `
            <div class="msg-avatar">HR</div>
            <div class="msg-content-wrapper">
                <div class="msg-bubble">${escapeHtml(text)}</div>
                <div class="msg-time">${getFormattedTime()}</div>
            </div>
        `;
        messagesContainer.appendChild(msgRow);
        scrollToBottom();
    };

    const showTypingIndicator = () => {
        const indicatorRow = document.createElement('div');
        indicatorRow.className = 'message-row ai';
        indicatorRow.id = 'typingIndicator';
        indicatorRow.innerHTML = `
            <div class="msg-avatar">PG</div>
            <div class="msg-content-wrapper">
                <div class="msg-bubble">
                    <div class="typing-dots">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(indicatorRow);
        scrollToBottom();
    };

    const removeTypingIndicator = () => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    };

    const appendAiMessage = (text) => {
        removeTypingIndicator();

        const msgRow = document.createElement('div');
        msgRow.className = 'message-row ai';
        msgRow.innerHTML = `
            <div class="msg-avatar">PG</div>
            <div class="msg-content-wrapper">
                <div class="msg-bubble">${escapeHtml(text)}</div>
                <div class="msg-time">${getFormattedTime()}</div>
            </div>
        `;
        messagesContainer.appendChild(msgRow);
        scrollToBottom();
    };

    const escapeHtml = (unsafe) => {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    };

    const handleSendMessage = async () => {
        const question = userInput.value.trim();
        if (!question) return;

        userInput.value = '';
        sendBtn.disabled = true;

        appendUserMessage(question);
        showTypingIndicator();

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                appendAiMessage(`⚠️ Backend error (${response.status}): ${data.error || data.detail || 'Failed to fetch response'}`);
            } else if (data.error) {
                appendAiMessage("⚠️ " + data.error);
            } else if (data.answer) {
                appendAiMessage(data.answer);
            } else {
                appendAiMessage("⚠️ Empty response from backend API.");
            }
        } catch (err) {
            removeTypingIndicator();
            appendAiMessage(`❌ Connection error connecting to ${API_ENDPOINT}. Please verify the FastAPI backend server is running.`);
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    };

    sendBtn.addEventListener('click', handleSendMessage);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    chipsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('chip-btn')) {
            const promptText = e.target.getAttribute('data-prompt');
            userInput.value = promptText;
            handleSendMessage();
        }
    });
});
