(function () {
    if (window.__wtLoaded) {
        // If already initialized, update current user and connect if needed
        return;
    }
    window.__wtLoaded = true;

    let ws = null;
    let reconnectTimer = null;
    let lastRenderedDate = null;
    let isConnected = false;
    let unreadCount = 0;
    let isChatPopupOpen = false;

    // Default user state: null until explicitly set on authenticated login
    window.wtCurrentUser = window.wtCurrentUser || null;

    // Public setter called from Anvil Python: anvil.js.call('setWtCurrentUser', user_dict)
    window.setWtCurrentUser = function (profile) {
        if (!profile || !profile.email) return;
        window.wtCurrentUser = Object.assign({}, profile);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "join",
                user: window.wtCurrentUser
            }));
        } else {
            connectWebSocket();
        }
    };

    // Public disconnect called on logout
    window.disconnectWtChat = function () {
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        const activeWs = ws || window.__wtWs;
        if (activeWs) {
            try {
                if (activeWs.readyState === WebSocket.OPEN) {
                    activeWs.send(JSON.stringify({ type: "logout" }));
                }
                activeWs.close(1000, "User logged out");
            } catch (e) {
                console.error("Error closing WT websocket:", e);
            }
            ws = null;
            window.__wtWs = null;
        }
        window.wtCurrentUser = null;
        isConnected = false;
        clearUnreadCount();
        const els = initElements();
        if (els.onlineText) {
            els.onlineText.textContent = "Offline";
        }
        if (els.statusDot) {
            els.statusDot.classList.add("offline");
        }
    };

    function getMyEmail() {
        return ((window.wtCurrentUser && window.wtCurrentUser.email) || "").toLowerCase().trim();
    }

    function getLocalLastReadId(email) {
        const userEmail = (email || getMyEmail()).toLowerCase().trim();
        if (!userEmail) return 0;
        try {
            return parseInt(localStorage.getItem("wt_last_read_" + userEmail) || "0", 10) || 0;
        } catch (e) {
            return 0;
        }
    }

    function setLocalLastReadId(msgId, email) {
        const userEmail = (email || getMyEmail()).toLowerCase().trim();
        if (!userEmail || !msgId) return;
        const current = getLocalLastReadId(userEmail);
        const newId = Math.max(current, parseInt(msgId, 10) || 0);
        try {
            localStorage.setItem("wt_last_read_" + userEmail, newId.toString());
        } catch (e) {}
        return newId;
    }

    function getHighestMessageId() {
        const els = initElements();
        if (!els.body) return 0;
        const rows = els.body.querySelectorAll(".wt-message-row[data-msg-id]");
        let maxId = 0;
        rows.forEach(r => {
            const id = parseInt(r.getAttribute("data-msg-id"), 10) || 0;
            if (id > maxId) maxId = id;
        });
        return maxId;
    }

    function sendMarkRead(maxId) {
        const myEmail = getMyEmail();
        const idToMark = maxId || getHighestMessageId();
        if (!myEmail || !idToMark) return;
        setLocalLastReadId(idToMark, myEmail);
        const activeWs = (ws && ws.readyState === WebSocket.OPEN) ? ws : (window.__wtWs && window.__wtWs.readyState === WebSocket.OPEN ? window.__wtWs : null);
        if (activeWs) {
            try {
                activeWs.send(JSON.stringify({
                    type: "mark_read",
                    last_read_id: parseInt(idToMark, 10),
                    user_email: myEmail
                }));
            } catch (e) {}
        }
    }

    function recalculateUnreadCount(customLastReadId) {
        const myEmail = getMyEmail();
        if (!myEmail) {
            clearUnreadCount();
            return;
        }
        if (checkIsChatOpen()) {
            clearUnreadCount();
            return;
        }

        const effectiveLastRead = typeof customLastReadId === "number" ? customLastReadId : getLocalLastReadId(myEmail);
        const els = initElements();
        if (!els.body) return;

        const rows = els.body.querySelectorAll(".wt-message-row[data-msg-id]");
        let unread = 0;
        rows.forEach(r => {
            const isOutgoing = r.classList.contains("wt-message-outgoing");
            if (isOutgoing) return;
            const msgId = parseInt(r.getAttribute("data-msg-id"), 10) || 0;
            if (effectiveLastRead > 0) {
                if (msgId > effectiveLastRead) {
                    unread++;
                }
            } else {
                const createdAt = r.getAttribute("data-created-at");
                if (createdAt) {
                    const msgTime = new Date(createdAt).getTime();
                    if (!isNaN(msgTime) && (Date.now() - msgTime) < 24 * 3600 * 1000) {
                        unread++;
                    }
                }
            }
        });

        unreadCount = unread;
        updateBadgeDisplay();
    }

    // Sync chat popup visibility state from Anvil: anvil.js.call('setWtChatOpenStatus', True/False)
    window.setWtChatOpenStatus = function (isOpen) {
        isChatPopupOpen = !!isOpen;
        if (isChatPopupOpen) {
            clearUnreadCount();
            const maxId = getHighestMessageId();
            if (maxId > 0) {
                sendMarkRead(maxId);
            }
            if (typeof window.scrollWtChatToBottom === "function") {
                window.scrollWtChatToBottom();
            } else {
                scrollToBottom();
            }
        }
    };

    function checkIsChatOpen() {
        if (isChatPopupOpen) return true;
        const popup = document.querySelector(".anvil-role-live-assistant-popup");
        if (popup) {
            const style = window.getComputedStyle(popup);
            if (style.display !== "none" && style.visibility !== "hidden" && popup.offsetParent !== null) {
                return true;
            }
        }
        return false;
    }

    // Unread message badge on floating action button
    function getOrCreateBadge() {
        const fabContainer = document.querySelector(".anvil-role-fab, .anvil-role-fab-active, .anvil-role-fab-thinking");
        if (!fabContainer) return null;

        let badge = document.getElementById("wtUnreadBadge");
        if (badge && fabContainer.contains(badge)) {
            return badge;
        }
        if (badge) {
            badge.remove();
        }

        badge = document.createElement("span");
        badge.id = "wtUnreadBadge";
        badge.className = "wt-unread-badge";
        fabContainer.appendChild(badge);
        return badge;
    }

    function updateBadgeDisplay() {
        const badge = getOrCreateBadge();
        if (!badge) {
            // If the FAB container is not yet attached in the DOM, retry shortly
            if (unreadCount > 0 && !window._wtBadgeRetryTimer) {
                window._wtBadgeRetryTimer = setTimeout(() => {
                    window._wtBadgeRetryTimer = null;
                    updateBadgeDisplay();
                }, 250);
            }
            return;
        }

        if (unreadCount > 0 && !checkIsChatOpen()) {
            badge.textContent = unreadCount > 99 ? "99+" : unreadCount;
            badge.style.display = "flex";
        } else {
            badge.textContent = "";
            badge.style.display = "none";
        }
    }

    function incrementUnreadCount() {
        unreadCount++;
        updateBadgeDisplay();
    }

    function clearUnreadCount() {
        unreadCount = 0;
        updateBadgeDisplay();
    }

    window.clearWtUnreadCount = clearUnreadCount;
    window.incrementWtUnreadCount = incrementUnreadCount;
    window.getWtUnreadCount = function () { return unreadCount; };
    window.updateWtBadgeDisplay = updateBadgeDisplay;
    window.updateBadgeDisplay = updateBadgeDisplay;
    window.sendWtMarkRead = sendMarkRead;
    window.recalculateWtUnreadCount = recalculateUnreadCount;

    function getWsUrl() {
        if (window.WT_WS_URL) return window.WT_WS_URL;
        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const host = window.location.hostname || "127.0.0.1";
        const port = window.WT_WS_PORT || "8765";
        return `${protocol}${host}:${port}`;
    }

    function initElements() {
        const body = document.getElementById("wtMessagesBody");
        const input = document.getElementById("wtInputMessage");
        const sendBtn = document.getElementById("wtBtnSend");
        const refreshBtn = document.getElementById("wtBtnRefresh");
        const closeBtn = document.getElementById("wtBtnClose");
        const statusDot = document.getElementById("wtStatusDot");
        const onlineText = document.getElementById("wtOnlineText");
        const emptyState = document.getElementById("wtEmptyState");

        return { body, input, sendBtn, refreshBtn, closeBtn, statusDot, onlineText, emptyState };
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function computeInitials(email) {
        if (!email) return "U";
        const clean = email.split("@")[0];
        const parts = clean.split(/[._\-+]/).filter(Boolean);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        } else if (parts.length === 1 && parts[0].length >= 2) {
            return parts[0].substring(0, 2).toUpperCase();
        } else if (parts.length === 1) {
            return parts[0][0].toUpperCase();
        }
        return "U";
    }

    function isSelf(msg) {
        if (!window.wtCurrentUser || !window.wtCurrentUser.email) return false;
        const myEmail = (window.wtCurrentUser.email || "").toLowerCase().trim();
        const msgEmail = (msg.sender_email || "").toLowerCase().trim();
        return !!(myEmail && msgEmail && myEmail === msgEmail);
    }

    function scrollToBottom() {
        const body = document.getElementById("wtMessagesBody");
        if (!body) return;
        requestAnimationFrame(() => {
            body.scrollTop = body.scrollHeight;
            if (body.lastElementChild) {
                try {
                    body.lastElementChild.scrollIntoView({ block: "end", inline: "nearest", behavior: "auto" });
                } catch (e) {}
            }
        });
    }

    // Expose scroll function globally with staggered triggers to ensure full render completion
    window.scrollWtChatToBottom = function () {
        scrollToBottom();
        setTimeout(scrollToBottom, 50);
        setTimeout(scrollToBottom, 150);
        setTimeout(scrollToBottom, 300);
    };

    function isWithin15Minutes(createdAt) {
        if (!createdAt) return false;
        const createdMs = new Date(createdAt).getTime();
        if (isNaN(createdMs)) return false;
        const elapsedSec = (Date.now() - createdMs) / 1000;
        // Allow up to 15 minutes, with 2-minute margin for any minor clock discrepancy
        return elapsedSec >= -120 && elapsedSec <= 15 * 60;
    }

    function normalizeDateGroup(dateGroup, createdAt) {
        if (!dateGroup && !createdAt) return "Today";
        if (dateGroup === "Today" || dateGroup === "Yesterday") {
            return dateGroup;
        }
        // If already contains a 4-digit year (e.g. "Tue, Sep 29, 2026"), return as is
        if (dateGroup && /\b\d{4}\b/.test(dateGroup)) {
            return dateGroup;
        }
        if (createdAt) {
            const d = new Date(createdAt);
            if (!isNaN(d.getTime())) {
                const today = new Date();
                const isToday = d.toDateString() === today.toDateString();
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                const isYesterday = d.toDateString() === yesterday.toDateString();
                if (isToday) return "Today";
                if (isYesterday) return "Yesterday";
                const options = { weekday: "short", month: "short", day: "numeric", year: "numeric" };
                return d.toLocaleDateString("en-US", options);
            }
        }
        if (dateGroup) {
            const year = createdAt ? new Date(createdAt).getFullYear() : new Date().getFullYear();
            return `${dateGroup}, ${year}`;
        }
        return "Today";
    }

    function createDatePill(dateGroup) {
        const div = document.createElement("div");
        div.className = "wt-date-separator";
        div.innerHTML = `
            <span class="wt-date-pill">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                ${escapeHtml(dateGroup)}
            </span>
        `;
        return div;
    }

    function renderMessage(msg) {
        if (!msg) return;
        const els = initElements();
        if (!els.body) return;

        // Deduplication guard: ignore if a message with this unique ID is already rendered
        if (msg.id && els.body.querySelector(`.wt-message-row[data-msg-id="${msg.id}"]`)) {
            return;
        }

        if (els.emptyState) {
            els.emptyState.style.display = "none";
        }

        const dateGroup = normalizeDateGroup(msg.date_group, msg.created_at);
        if (dateGroup !== lastRenderedDate) {
            els.body.appendChild(createDatePill(dateGroup));
            lastRenderedDate = dateGroup;
        }

        const self = isSelf(msg);
        const row = document.createElement("div");
        row.className = `wt-message-row ${self ? "wt-message-outgoing" : "wt-message-incoming"}`;
        if (msg.id) {
            row.setAttribute("data-msg-id", msg.id);
        }
        row.setAttribute("data-created-at", msg.created_at || "");
        row.setAttribute("data-raw-msg", msg.message || "");

        const escapedMsg = escapeHtml(msg.message).replace(/\n/g, "<br>");
        const timeStr = escapeHtml(msg.time || "");
        const isEdited = !!msg.is_edited;
        const canEdit = self && isWithin15Minutes(msg.created_at);

        if (self) {
            const roleName = escapeHtml(msg.role_name || (window.wtCurrentUser && window.wtCurrentUser.role_name) || "");
            const email = escapeHtml((window.wtCurrentUser && window.wtCurrentUser.email) || msg.sender_email || "You");

            row.innerHTML = `
                <div class="wt-outgoing-header">
                    <span class="wt-self-name">${email} (You)</span>
                    ${roleName ? `<span class="wt-role-badge">${roleName}</span>` : ""}
                </div>
                <div class="wt-bubble-outgoing">
                    <div class="wt-bubble-content">${escapedMsg}</div>
                    <div class="wt-bubble-meta wt-meta-outgoing">
                        ${canEdit ? `
                        <button type="button" class="wt-edit-btn" title="Edit message" aria-label="Edit message">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 20h9"></path>
                                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                            </svg>
                        </button>` : ""}
                        <span class="wt-edited-label" style="${isEdited ? '' : 'display:none;'}">edited</span>
                        <span class="wt-time-outgoing">${timeStr}</span>
                    </div>
                </div>
            `;
        } else {
            const senderEmail = escapeHtml(msg.sender_email || "User");
            const initials = escapeHtml(msg.initials || computeInitials(senderEmail));
            const roleName = escapeHtml(msg.role_name || "");

            row.innerHTML = `
                <div class="wt-incoming-header">
                    <div class="wt-avatar">${initials}</div>
                    <span class="wt-sender-name">${senderEmail}</span>
                    ${roleName ? `<span class="wt-role-badge">${roleName}</span>` : ""}
                </div>
                <div class="wt-bubble-incoming">
                    <div class="wt-bubble-content">${escapedMsg}</div>
                    <div class="wt-bubble-meta wt-meta-incoming">
                        <span class="wt-edited-label" style="${isEdited ? '' : 'display:none;'}">edited</span>
                        <span class="wt-time-incoming">${timeStr}</span>
                    </div>
                </div>
            `;
        }

        els.body.appendChild(row);
        scrollToBottom();
    }

    function startEditMessage(row) {
        if (!row) return;
        const msgId = row.getAttribute("data-msg-id");
        const createdAt = row.getAttribute("data-created-at");

        if (!isWithin15Minutes(createdAt)) {
            const btn = row.querySelector(".wt-edit-btn");
            if (btn) btn.remove();
            return;
        }

        const bubble = row.querySelector(".wt-bubble-outgoing");
        if (!bubble) return;
        if (bubble.querySelector(".wt-edit-mode-container")) return;

        const contentEl = bubble.querySelector(".wt-bubble-content");
        const metaEl = bubble.querySelector(".wt-bubble-meta");
        const rawMsg = row.getAttribute("data-raw-msg") || (contentEl ? contentEl.innerText : "");

        if (contentEl) contentEl.style.display = "none";
        if (metaEl) metaEl.style.display = "none";

        const editContainer = document.createElement("div");
        editContainer.className = "wt-edit-mode-container";
        editContainer.innerHTML = `
            <textarea class="wt-edit-input" rows="2"></textarea>
            <div class="wt-edit-actions">
                <button type="button" class="wt-edit-cancel-btn" title="Cancel (Esc)" aria-label="Cancel">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <button type="button" class="wt-edit-save-btn" title="Done" aria-label="Done">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="9 12 11 14 15 10"></polyline>
                    </svg>
                </button>
            </div>
        `;
        bubble.appendChild(editContainer);

        const textarea = editContainer.querySelector(".wt-edit-input");
        const cancelBtn = editContainer.querySelector(".wt-edit-cancel-btn");
        const saveBtn = editContainer.querySelector(".wt-edit-save-btn");

        textarea.value = rawMsg;
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);

        function cancel() {
            editContainer.remove();
            if (contentEl) contentEl.style.display = "";
            if (metaEl) metaEl.style.display = "flex";
        }

        function save() {
            const newText = textarea.value.trim();
            if (!newText) {
                textarea.focus();
                return;
            }
            if (newText === rawMsg.trim()) {
                cancel();
                return;
            }
            if (!isWithin15Minutes(createdAt)) {
                alert("This message can no longer be edited as 15 minutes have passed.");
                cancel();
                const btn = row.querySelector(".wt-edit-btn");
                if (btn) btn.remove();
                return;
            }

            const activeWs = (ws && ws.readyState === WebSocket.OPEN) ? ws : (window.__wtWs && window.__wtWs.readyState === WebSocket.OPEN ? window.__wtWs : null);
            if (activeWs) {
                saveBtn.disabled = true;
                saveBtn.style.opacity = "0.6";

                // Safety timeout: if no response from server within 6 seconds, re-enable
                const safetyTimer = setTimeout(() => {
                    if (saveBtn) {
                        saveBtn.disabled = false;
                        saveBtn.style.opacity = "1";
                    }
                }, 6000);
                saveBtn._safetyTimer = safetyTimer;

                const myEmail = (window.wtCurrentUser && window.wtCurrentUser.email) || "";
                activeWs.send(JSON.stringify({
                    type: "edit_message",
                    message_id: parseInt(msgId, 10),
                    new_text: newText,
                    sender_email: myEmail
                }));
            } else {
                alert("Chat server is offline. Could not save edited message.");
                cancel();
            }
        }

        cancelBtn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            cancel();
        });

        saveBtn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            save();
        });

        textarea.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
                e.preventDefault();
                cancel();
            } else if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                save();
            }
        });
    }

    function handleMessageEdited(msg) {
        if (!msg || !msg.id) return;
        const els = initElements();
        if (!els.body) return;

        const row = els.body.querySelector(`.wt-message-row[data-msg-id="${msg.id}"]`);
        if (!row) return;

        row.setAttribute("data-raw-msg", msg.message || "");

        const editContainer = row.querySelector(".wt-edit-mode-container");
        if (editContainer) {
            editContainer.remove();
        }

        const bubble = row.querySelector(".wt-bubble-outgoing, .wt-bubble-incoming");
        if (!bubble) return;

        let contentEl = bubble.querySelector(".wt-bubble-content");
        if (!contentEl) {
            contentEl = document.createElement("div");
            contentEl.className = "wt-bubble-content";
            bubble.prepend(contentEl);
        }
        contentEl.style.display = "";
        contentEl.innerHTML = escapeHtml(msg.message).replace(/\n/g, "<br>");

        const editedLabel = bubble.querySelector(".wt-edited-label");
        if (editedLabel) {
            editedLabel.style.display = "inline";
        }

        const metaEl = bubble.querySelector(".wt-bubble-meta");
        if (metaEl) {
            metaEl.style.display = "flex";
        }
    }

    function checkExpiredEditButtons() {
        const rows = document.querySelectorAll(".wt-message-outgoing[data-created-at]");
        rows.forEach(row => {
            const createdAt = row.getAttribute("data-created-at");
            if (!isWithin15Minutes(createdAt)) {
                const btn = row.querySelector(".wt-edit-btn");
                if (btn) btn.remove();
                const editContainer = row.querySelector(".wt-edit-mode-container");
                if (editContainer) {
                    editContainer.remove();
                    const contentEl = row.querySelector(".wt-bubble-content");
                    const metaEl = row.querySelector(".wt-bubble-meta");
                    if (contentEl) contentEl.style.display = "";
                    if (metaEl) metaEl.style.display = "flex";
                }
            }
        });
    }

    function stopRefreshSpin() {
        const els = initElements();
        if (els.refreshBtn) {
            els.refreshBtn.classList.remove("spinning");
        }
    }

    function renderHistory(messages, serverLastReadId) {
        const els = initElements();
        if (!els.body) return;

        // Clear existing message rows
        els.body.innerHTML = "";
        lastRenderedDate = null;

        if (!messages || messages.length === 0) {
            const empty = document.createElement("div");
            empty.id = "wtEmptyState";
            empty.className = "wt-empty-state";
            empty.innerHTML = `
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span>No messages yet. Send a message to start!</span>
            `;
            els.body.appendChild(empty);
            setTimeout(stopRefreshSpin, 400);
            return;
        }

        messages.forEach(msg => renderMessage(msg));
        scrollToBottom();
        setTimeout(stopRefreshSpin, 400);

        // Process unread messages received while logged out / offline
        const myEmail = getMyEmail();
        if (myEmail) {
            const sLastRead = typeof serverLastReadId === "number" ? serverLastReadId : 0;
            const lLastRead = getLocalLastReadId(myEmail);
            const effectiveLastRead = Math.max(sLastRead, lLastRead);

            // Synchronize local storage if server has newer read marker
            if (sLastRead > lLastRead) {
                setLocalLastReadId(sLastRead, myEmail);
            }

            if (checkIsChatOpen()) {
                // If chat is open, user is viewing the messages now
                clearUnreadCount();
                const maxId = getHighestMessageId();
                if (maxId > 0) {
                    sendMarkRead(maxId);
                }
            } else {
                // Chat is closed: compute unread messages newer than effectiveLastRead
                let unread = 0;
                messages.forEach(msg => {
                    if (isSelf(msg)) return;
                    const msgId = parseInt(msg.id, 10) || 0;
                    if (effectiveLastRead > 0) {
                        if (msgId > effectiveLastRead) {
                            unread++;
                        }
                    } else {
                        // First-time baseline: count unread messages from the last 24 hours
                        if (msg.created_at) {
                            const msgTime = new Date(msg.created_at).getTime();
                            if (!isNaN(msgTime) && (Date.now() - msgTime) < 24 * 3600 * 1000) {
                                unread++;
                            }
                        }
                    }
                });

                unreadCount = unread;
                updateBadgeDisplay();
            }
        }
    }

    // Public method callable from Anvil Python or fallback
    window.renderWtHistoryFromAnvil = function (messages, serverLastReadId) {
        renderHistory(messages, serverLastReadId);
    };

    function connectWebSocket() {
        // Do not connect if there is no logged-in user with an email
        if (!window.wtCurrentUser || !window.wtCurrentUser.email) {
            return;
        }

        if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
            return;
        }
        if (window.__wtWs && (window.__wtWs.readyState === WebSocket.CONNECTING || window.__wtWs.readyState === WebSocket.OPEN)) {
            ws = window.__wtWs;
            return;
        }

        const url = getWsUrl();
        const els = initElements();
        if (els.onlineText) els.onlineText.textContent = "Connecting...";
        if (els.statusDot) {
            els.statusDot.classList.add("offline");
        }

        try {
            ws = new WebSocket(url);
            window.__wtWs = ws;
        } catch (e) {
            scheduleReconnect();
            return;
        }

        ws.onopen = function () {
            isConnected = true;
            if (reconnectTimer) clearTimeout(reconnectTimer);
            if (els.statusDot) els.statusDot.classList.remove("offline");

            // Join with current user
            if (window.wtCurrentUser && window.wtCurrentUser.email) {
                ws.send(JSON.stringify({
                    type: "join",
                    user: window.wtCurrentUser
                }));
            }
        };

        ws.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                const els = initElements();

                if (data.type === "history") {
                    renderHistory(data.messages, data.last_read_id);
                } else if (data.type === "message") {
                    renderMessage(data.message);

                    if (isSelf(data.message)) {
                        // User sent this message, update read marker
                        if (data.message.id) {
                            sendMarkRead(data.message.id);
                        }
                        clearUnreadCount();
                    } else {
                        // Incoming message from another user
                        if (!checkIsChatOpen()) {
                            incrementUnreadCount();
                        } else {
                            if (data.message.id) {
                                sendMarkRead(data.message.id);
                            }
                            clearUnreadCount();
                        }
                    }
                } else if (data.type === "reads_updated") {
                    const myEmail = getMyEmail();
                    if (data.user_email && data.user_email.toLowerCase() === myEmail) {
                        const newReadId = parseInt(data.last_read_id, 10) || 0;
                        setLocalLastReadId(newReadId, myEmail);
                        if (checkIsChatOpen()) {
                            clearUnreadCount();
                        } else {
                            recalculateUnreadCount(newReadId);
                        }
                    }
                } else if (data.type === "message_edited") {
                    handleMessageEdited(data.message);
                } else if (data.type === "error") {
                    console.warn("WT server error:", data.message);
                    alert(data.message || "An error occurred.");
                    const saveBtns = document.querySelectorAll(".wt-edit-save-btn");
                    saveBtns.forEach(b => {
                        if (b._safetyTimer) clearTimeout(b._safetyTimer);
                        b.disabled = false;
                        b.style.opacity = "1";
                    });
                } else if (data.type === "presence") {
                    const count = typeof data.online_count === "number" ? data.online_count : 0;
                    if (els.onlineText) {
                        els.onlineText.textContent = `${count} member${count === 1 ? "" : "s"} online`;
                    }
                    if (els.statusDot) {
                        if (count > 0) {
                            els.statusDot.classList.remove("offline");
                        } else {
                            els.statusDot.classList.add("offline");
                        }
                    }
                }
            } catch (err) {
                console.error("WT chat message parsing error:", err);
            }
        };

        ws.onerror = function () {
            isConnected = false;
            const els = initElements();
            if (els.statusDot) els.statusDot.classList.add("offline");
            if (els.onlineText) els.onlineText.textContent = "Offline (Reconnecting...)";
        };

        ws.onclose = function () {
            isConnected = false;
            const els = initElements();
            if (els.statusDot) els.statusDot.classList.add("offline");
            if (els.onlineText) els.onlineText.textContent = "Offline";
            scheduleReconnect();
        };
    }

    function scheduleReconnect() {
        if (reconnectTimer) clearTimeout(reconnectTimer);
        // Do not attempt reconnect if logged out
        if (!window.wtCurrentUser || !window.wtCurrentUser.email) {
            return;
        }
        reconnectTimer = setTimeout(() => {
            connectWebSocket();
        }, 3000);
    }

    function sendMessage() {
        const els = initElements();
        if (!els.input) return;
        const text = els.input.value.trim();
        if (!text) return;

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            alert("Chat server is currently offline. Please ensure the WebSocket server is running.");
            return;
        }

        ws.send(JSON.stringify({
            type: "message",
            text: text
        }));

        clearUnreadCount();
        const maxId = getHighestMessageId();
        if (maxId > 0) {
            sendMarkRead(maxId);
        }

        els.input.value = "";
        els.input.focus();
    }

    function refreshMessages() {
        const els = initElements();
        if (els.refreshBtn) {
            els.refreshBtn.classList.add("spinning");
        }

        // 1. If WebSocket is connected, request history from WS server
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "get_history" }));
        } else {
            // Reconnect websocket
            connectWebSocket();
        }

        // 2. Also trigger Anvil backend refresh callback for dual synchronization
        if (typeof window.onWtChatRefresh === "function") {
            try {
                window.onWtChatRefresh();
            } catch (err) {
                console.error("Error in onWtChatRefresh:", err);
            }
        }

        // 3. Fallback safety timer: stop spinning after 1.5s
        setTimeout(stopRefreshSpin, 1500);
    }

    // Expose refresh function globally
    window.refreshWtChat = refreshMessages;

    // Attach document-level event delegation so buttons ALWAYS work
    if (!window.__wtEventsBound) {
        window.__wtEventsBound = true;

        document.addEventListener("click", function (e) {
            const refreshBtn = e.target.closest("#wtBtnRefresh");
            if (refreshBtn) {
                e.preventDefault();
                refreshMessages();
                return;
            }

            const closeBtn = e.target.closest("#wtBtnClose");
            if (closeBtn) {
                e.preventDefault();
                window.setWtChatOpenStatus(false);
                window.dispatchEvent(new CustomEvent("wt-close-chat"));
                if (typeof window.onWtChatClose === "function") {
                    window.onWtChatClose();
                }
                return;
            }

            const sendBtn = e.target.closest("#wtBtnSend");
            if (sendBtn) {
                e.preventDefault();
                sendMessage();
                return;
            }

            const fab = e.target.closest(".anvil-role-fab, .anvil-role-fab-active");
            if (fab) {
                clearUnreadCount();
                const maxId = getHighestMessageId();
                if (maxId > 0) {
                    sendMarkRead(maxId);
                }
                if (typeof window.scrollWtChatToBottom === "function") {
                    window.scrollWtChatToBottom();
                }
            }

            const editBtn = e.target.closest(".wt-edit-btn");
            if (editBtn) {
                e.preventDefault();
                e.stopPropagation();
                const row = editBtn.closest(".wt-message-row");
                if (row) {
                    startEditMessage(row);
                }
                return;
            }
        });

        // Periodic timer to remove pencil icon once 15 minutes have elapsed
        setInterval(checkExpiredEditButtons, 15000);

        document.addEventListener("keydown", function (e) {
            if (e.target && e.target.id === "wtInputMessage") {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            }
        });

        // Clean disconnect on tab/window close
        window.addEventListener("beforeunload", function () {
            if (ws && ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(JSON.stringify({ type: "leave" }));
                    ws.close();
                } catch (e) {}
            }
        });
    }

    // Auto-initialize badge when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            getOrCreateBadge();
            if (window.wtCurrentUser && window.wtCurrentUser.email) {
                connectWebSocket();
            }
        });
    } else {
        getOrCreateBadge();
        if (window.wtCurrentUser && window.wtCurrentUser.email) {
            connectWebSocket();
        }
    }

    // Export function to re-init if mounted dynamically
    window.initWtChat = function () {
        getOrCreateBadge();
        if (window.wtCurrentUser && window.wtCurrentUser.email) {
            connectWebSocket();
        }
    };
})();
