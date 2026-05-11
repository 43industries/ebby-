/* EBBY chat widget
 * Self-mounting floating chat bubble that talks to the EBBY Bot API.
 *
 * Configure the API base by setting `window.EBBY_API` BEFORE this
 * script loads, e.g.:
 *
 *   <script>window.EBBY_API = "https://ebby-bot.onrender.com";</script>
 *   <script src="https://ebby-bot.onrender.com/widget/ebby-chat.js" defer></script>
 *
 * If `window.EBBY_API` is not set, the widget falls back to the origin
 * that served this script (so when the widget and the API are hosted
 * together it just works).
 */
(function () {
  if (window.__EBBY_WIDGET_LOADED__) return;
  window.__EBBY_WIDGET_LOADED__ = true;

  var DEFAULT_API = (function () {
    try {
      var src = document.currentScript && document.currentScript.src;
      if (src) {
        var u = new URL(src);
        return u.origin;
      }
    } catch (e) {}
    return "";
  })();

  var API_BASE = (window.EBBY_API || DEFAULT_API || "").replace(/\/+$/, "");

  var SESSION_KEY = "ebby_chat_session_id";
  var sessionId = (function () {
    try {
      var existing = localStorage.getItem(SESSION_KEY);
      if (existing) return existing;
      var fresh =
        "s_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(SESSION_KEY, fresh);
      return fresh;
    } catch (e) {
      return "s_" + Date.now().toString(36);
    }
  })();

  var WELCOME =
    "Hi! I'm the EBBY assistant. Ask me about our services, pricing, or how we work, " +
    "or tell me about your project and I'll set up a quote.";

  function injectStyles() {
    if (document.getElementById("ebby-chat-styles")) return;
    var css = `
      #ebby-chat-root, #ebby-chat-root * { box-sizing: border-box; }
      #ebby-chat-root {
        position: fixed; bottom: 24px; right: 24px;
        z-index: 2147483000;
        font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        color: #e2e8f0;
      }
      #ebby-chat-bubble {
        width: 60px; height: 60px; border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: #fff; border: none; cursor: pointer;
        box-shadow: 0 12px 30px rgba(99,102,241,0.45);
        display: flex; align-items: center; justify-content: center;
        transition: transform .2s ease, box-shadow .2s ease;
      }
      #ebby-chat-bubble:hover { transform: translateY(-2px) scale(1.04); }
      #ebby-chat-bubble svg { width: 26px; height: 26px; }
      #ebby-chat-panel {
        position: absolute; bottom: 76px; right: 0;
        width: min(380px, calc(100vw - 32px));
        height: min(560px, calc(100vh - 120px));
        background: rgba(18,18,26,0.96);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        box-shadow: 0 24px 60px rgba(0,0,0,0.45);
        display: none; flex-direction: column; overflow: hidden;
      }
      #ebby-chat-panel.open { display: flex; animation: ebbyChatIn .18s ease-out; }
      @keyframes ebbyChatIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      .ebby-header {
        padding: 14px 16px;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: #fff; display: flex; align-items: center; gap: 10px;
      }
      .ebby-header .ebby-avatar {
        width: 32px; height: 32px; border-radius: 8px;
        background: rgba(255,255,255,0.18);
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-family: 'Space Grotesk', Inter, sans-serif;
      }
      .ebby-header .ebby-title { font-weight: 600; font-size: 15px; }
      .ebby-header .ebby-sub { font-size: 11px; opacity: .8; }
      .ebby-header .ebby-close {
        margin-left: auto; background: transparent; border: none;
        color: #fff; cursor: pointer; opacity: .85; padding: 4px;
      }
      .ebby-header .ebby-close:hover { opacity: 1; }
      .ebby-messages {
        flex: 1; overflow-y: auto; padding: 16px;
        display: flex; flex-direction: column; gap: 10px;
        background: #0f0f17;
      }
      .ebby-msg {
        max-width: 85%; padding: 10px 14px; border-radius: 14px;
        font-size: 14px; line-height: 1.45; white-space: pre-wrap;
        word-wrap: break-word;
      }
      .ebby-msg.bot {
        align-self: flex-start;
        background: #1a1a25;
        border: 1px solid rgba(255,255,255,0.06);
        color: #e2e8f0; border-top-left-radius: 4px;
      }
      .ebby-msg.user {
        align-self: flex-end;
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: #fff; border-top-right-radius: 4px;
      }
      .ebby-typing {
        align-self: flex-start; display: inline-flex; gap: 4px;
        padding: 12px 14px; background: #1a1a25;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; border-top-left-radius: 4px;
      }
      .ebby-typing span {
        width: 6px; height: 6px; border-radius: 50%;
        background: #818cf8; opacity: .6;
        animation: ebbyBlink 1.2s infinite ease-in-out;
      }
      .ebby-typing span:nth-child(2) { animation-delay: .15s; }
      .ebby-typing span:nth-child(3) { animation-delay: .3s; }
      @keyframes ebbyBlink {
        0%, 80%, 100% { transform: scale(0.7); opacity: .4; }
        40%           { transform: scale(1.0); opacity: 1; }
      }
      .ebby-input {
        display: flex; gap: 8px; padding: 12px;
        border-top: 1px solid rgba(255,255,255,0.06);
        background: #12121a;
      }
      .ebby-input textarea {
        flex: 1; resize: none; background: #0a0a0f;
        color: #e2e8f0; border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 10px 12px;
        font-size: 14px; font-family: inherit;
        max-height: 120px; line-height: 1.4;
      }
      .ebby-input textarea:focus { outline: none; border-color: #6366f1; }
      .ebby-input button {
        background: #6366f1; color: #fff; border: none;
        border-radius: 10px; padding: 0 14px; cursor: pointer;
        font-weight: 600; font-size: 14px;
        transition: background .15s ease;
      }
      .ebby-input button:hover:not(:disabled) { background: #4f46e5; }
      .ebby-input button:disabled { opacity: .5; cursor: not-allowed; }
      .ebby-foot {
        text-align: center; font-size: 10px; color: #64748b;
        padding: 6px 0 8px; background: #12121a;
      }
    `;
    var style = document.createElement("style");
    style.id = "ebby-chat-styles";
    style.textContent = css;
    document.head.appendChild(style);
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var k in attrs) {
        if (k === "class") node.className = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else node.setAttribute(k, attrs[k]);
      }
    }
    (children || []).forEach(function (c) {
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  function build() {
    injectStyles();

    var root = el("div", { id: "ebby-chat-root" });

    var bubble = el("button", {
      id: "ebby-chat-bubble",
      "aria-label": "Open EBBY chat",
      html:
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" ' +
        'stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    });

    var panel = el("div", { id: "ebby-chat-panel", role: "dialog", "aria-label": "EBBY chat" });

    var header = el("div", { class: "ebby-header" }, [
      el("div", { class: "ebby-avatar" }, ["E"]),
      el("div", {}, [
        el("div", { class: "ebby-title" }, ["EBBY Assistant"]),
        el("div", { class: "ebby-sub" }, ["Usually replies in seconds"]),
      ]),
    ]);
    var closeBtn = el("button", {
      class: "ebby-close",
      "aria-label": "Close chat",
      html:
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
        '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    });
    header.appendChild(closeBtn);

    var messages = el("div", { class: "ebby-messages", id: "ebby-messages" });

    var input = el("textarea", {
      rows: "1",
      placeholder: "Ask about services, pricing, or your project...",
      "aria-label": "Type a message",
    });
    var sendBtn = el("button", { type: "button" }, ["Send"]);
    var inputBar = el("div", { class: "ebby-input" }, [input, sendBtn]);
    var foot = el("div", { class: "ebby-foot" }, ["Powered by EBBY"]);

    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(inputBar);
    panel.appendChild(foot);
    root.appendChild(panel);
    root.appendChild(bubble);
    document.body.appendChild(root);

    function appendMessage(role, text) {
      var node = el("div", { class: "ebby-msg " + role }, [text]);
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
      return node;
    }

    function appendTyping() {
      var t = el("div", { class: "ebby-typing", id: "ebby-typing" }, [
        el("span"),
        el("span"),
        el("span"),
      ]);
      messages.appendChild(t);
      messages.scrollTop = messages.scrollHeight;
      return t;
    }

    var initialized = false;
    function openPanel() {
      panel.classList.add("open");
      if (!initialized) {
        appendMessage("bot", WELCOME);
        initialized = true;
      }
      setTimeout(function () { input.focus(); }, 50);
    }
    function closePanel() { panel.classList.remove("open"); }

    bubble.addEventListener("click", function () {
      panel.classList.contains("open") ? closePanel() : openPanel();
    });
    closeBtn.addEventListener("click", closePanel);

    function autosize() {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 120) + "px";
    }
    input.addEventListener("input", autosize);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        send();
      }
    });
    sendBtn.addEventListener("click", send);

    var sending = false;
    async function send() {
      if (sending) return;
      var text = input.value.trim();
      if (!text) return;
      if (!API_BASE) {
        appendMessage("bot", "Chat is not configured (missing API base URL).");
        return;
      }
      sending = true;
      sendBtn.disabled = true;
      appendMessage("user", text);
      input.value = "";
      autosize();
      var typing = appendTyping();
      try {
        var resp = await fetch(API_BASE + "/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: text }),
        });
        var data = await resp.json().catch(function () { return {}; });
        typing.remove();
        if (!resp.ok) {
          appendMessage(
            "bot",
            "Sorry, something went wrong. Please try again or use the contact form."
          );
        } else {
          appendMessage("bot", data.reply || "...");
        }
      } catch (err) {
        typing.remove();
        appendMessage(
          "bot",
          "I can't reach the server right now. Please check your connection and try again."
        );
      } finally {
        sending = false;
        sendBtn.disabled = false;
        input.focus();
      }
    }

    window.EbbyChat = {
      open: openPanel,
      close: closePanel,
      reset: function () {
        try { localStorage.removeItem(SESSION_KEY); } catch (e) {}
        location.reload();
      },
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
