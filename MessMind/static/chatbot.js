// MessMind Assistant — floating chat widget.
// Drop-in: include this script on any logged-in page; it builds its own
// markup/styles and talks to the /chatbot endpoint.
(function () {
    const STYLE = `
        @keyframes mmPulse {
            0% { box-shadow: 0 8px 24px rgba(249,115,22,0.4), 0 0 0 0 rgba(249,115,22,0.45); }
            70% { box-shadow: 0 8px 24px rgba(249,115,22,0.4), 0 0 0 12px rgba(249,115,22,0); }
            100% { box-shadow: 0 8px 24px rgba(249,115,22,0.4), 0 0 0 0 rgba(249,115,22,0); }
        }
        @keyframes mmMsgIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        #mm-chat-toggle {
            position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 9999;
            width: 56px; height: 56px; border-radius: 50%; border: none;
            background: linear-gradient(135deg, #f97316, #fb923c);
            color: #fff; font-size: 1.6rem; cursor: pointer;
            box-shadow: 0 8px 24px rgba(249, 115, 22, 0.4);
            display: flex; align-items: center; justify-content: center;
            transition: transform 0.2s ease;
            animation: mmPulse 2.5s ease-out infinite;
        }
        #mm-chat-toggle:hover { transform: scale(1.08); animation-play-state: paused; }

        #mm-chat-panel {
            position: fixed; bottom: 5.5rem; right: 1.5rem; z-index: 9999;
            width: 330px; max-height: 460px; display: flex; flex-direction: column;
            background: rgba(255, 250, 243, 0.98); border: 1px solid rgba(249, 115, 22, 0.25);
            border-radius: 14px; box-shadow: 0 12px 40px rgba(120, 72, 32, 0.22);
            overflow: hidden; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            opacity: 0; visibility: hidden; pointer-events: none;
            transform: scale(0.92) translateY(10px); transform-origin: bottom right;
            transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s;
        }
        #mm-chat-panel.open {
            opacity: 1; visibility: visible; pointer-events: auto;
            transform: scale(1) translateY(0);
        }

        #mm-chat-header {
            background: rgba(249, 115, 22, 0.12); padding: 0.9rem 1rem;
            display: flex; align-items: center; justify-content: space-between;
            border-bottom: 1px solid rgba(249, 115, 22, 0.25);
        }
        #mm-chat-header span { color: #2d2a26; font-weight: 600; font-size: 0.95rem; }
        #mm-chat-close {
            background: none; border: none; color: #78716c; font-size: 1.1rem;
            cursor: pointer; line-height: 1;
        }
        #mm-chat-close:hover { color: #2d2a26; }

        #mm-chat-messages {
            flex: 1; overflow-y: auto; padding: 1rem; display: flex;
            flex-direction: column; gap: 0.6rem; min-height: 220px; max-height: 320px;
        }
        .mm-msg { max-width: 85%; padding: 0.55rem 0.8rem; border-radius: 10px;
            font-size: 0.85rem; line-height: 1.4; white-space: pre-line;
            animation: mmMsgIn 0.25s ease; }
        .mm-msg.bot { align-self: flex-start; background: rgba(249, 115, 22, 0.1);
            border: 1px solid rgba(249, 115, 22, 0.25); color: #2d2a26; }
        .mm-msg.user { align-self: flex-end; background: #f97316; color: #fff; }
        .mm-msg.typing { color: #78716c; font-style: italic; }

        @media (prefers-reduced-motion: reduce) {
            #mm-chat-toggle { animation: none; }
            .mm-msg { animation: none; }
        }

        #mm-chat-input-row {
            display: flex; border-top: 1px solid rgba(249, 115, 22, 0.2);
            padding: 0.6rem; gap: 0.5rem; background: rgba(255, 248, 240, 0.9);
        }
        #mm-chat-input {
            flex: 1; background: #fffaf3; border: 1px solid rgba(120, 113, 108, 0.3);
            border-radius: 8px; padding: 0.5rem 0.7rem; color: #2d2a26; font-size: 0.85rem;
        }
        #mm-chat-input:focus { outline: none; border-color: #f97316; }
        #mm-chat-send {
            background: #f97316; border: none; border-radius: 8px; color: #fff;
            padding: 0.5rem 0.9rem; cursor: pointer; font-size: 0.85rem;
        }
        #mm-chat-send:hover { background: #ea580c; }
    `;

    function buildWidget() {
        const styleTag = document.createElement('style');
        styleTag.textContent = STYLE;
        document.head.appendChild(styleTag);

        const toggle = document.createElement('button');
        toggle.id = 'mm-chat-toggle';
        toggle.title = 'MessMind Assistant';
        toggle.innerHTML = '💬';

        const panel = document.createElement('div');
        panel.id = 'mm-chat-panel';
        panel.innerHTML = `
            <div id="mm-chat-header">
                <span>🤖 MessMind Assistant</span>
                <button id="mm-chat-close">✕</button>
            </div>
            <div id="mm-chat-messages"></div>
            <div id="mm-chat-input-row">
                <input id="mm-chat-input" type="text" placeholder="Ask about menu, timings, polls..." autocomplete="off" />
                <button id="mm-chat-send">Send</button>
            </div>
        `;

        document.body.appendChild(toggle);
        document.body.appendChild(panel);

        const messagesEl = panel.querySelector('#mm-chat-messages');
        const inputEl = panel.querySelector('#mm-chat-input');
        const sendBtn = panel.querySelector('#mm-chat-send');
        const closeBtn = panel.querySelector('#mm-chat-close');

        let greeted = false;
        const history = []; // {role: 'user'|'assistant', content: string}

        function addMessage(text, sender) {
            const bubble = document.createElement('div');
            bubble.className = 'mm-msg ' + sender;
            bubble.textContent = text;
            messagesEl.appendChild(bubble);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return bubble;
        }

        async function sendMessage() {
            const text = inputEl.value.trim();
            if (!text) return;
            addMessage(text, 'user');
            inputEl.value = '';

            const typing = addMessage('typing...', 'bot typing');

            try {
                const res = await fetch('/chatbot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, history: history })
                });
                const data = await res.json();
                typing.remove();
                if (data.success) {
                    addMessage(data.reply, 'bot');
                    history.push({ role: 'user', content: text });
                    history.push({ role: 'assistant', content: data.reply });
                    // Keep only the last few turns — enough context, small payload.
                    while (history.length > 12) history.shift();
                } else {
                    addMessage(data.message || "Sorry, I couldn't process that.", 'bot');
                }
            } catch (err) {
                typing.remove();
                addMessage("I'm having trouble connecting right now. Please try again.", 'bot');
            }
        }

        toggle.addEventListener('click', () => {
            panel.classList.toggle('open');
            if (panel.classList.contains('open')) {
                if (!greeted) {
                    addMessage("Hi! I'm the MessMind Assistant 🤖. Ask me about today's menu, mess timings, notices, complaints, or polls.", 'bot');
                    greeted = true;
                }
                inputEl.focus();
            }
        });

        closeBtn.addEventListener('click', () => panel.classList.remove('open'));

        sendBtn.addEventListener('click', sendMessage);
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', buildWidget);
    } else {
        buildWidget();
    }
})();
