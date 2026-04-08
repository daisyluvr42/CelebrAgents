const API = window.CELEBR_API || window.location.origin;
let currentSkill = null;
let allSkills = [];
let messages = [];
let isStreaming = false;
let createdSkillId = null;

// --- DOM refs ---
const providerSelect = document.getElementById("provider-select");
const cardGrid = document.getElementById("card-grid");
const homeView = document.getElementById("home-view");
const chatView = document.getElementById("chat-view");
const messagesEl = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const backBtn = document.getElementById("back-btn");
const clearBtn = document.getElementById("clear-btn");
const chatHeaderImg = document.getElementById("chat-header-img");
const chatHeaderName = document.getElementById("chat-header-name");
const chatHeaderProvider = document.getElementById("chat-header-provider");

// Create modal refs
const createModal = document.getElementById("create-modal");
const modalClose = document.getElementById("modal-close");
const createName = document.getElementById("create-name");
const createContext = document.getElementById("create-context");
const createStartBtn = document.getElementById("create-start-btn");
const createStepInput = document.getElementById("create-step-input");
const createStepProgress = document.getElementById("create-step-progress");
const createStepDone = document.getElementById("create-step-done");
const createOutput = document.getElementById("create-output");
const progressLabel = document.getElementById("progress-label");
const doneChatBtn = document.getElementById("done-chat-btn");
const doneTitle = document.getElementById("done-title");

function skillImage(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API}${path}`;
}

// --- Init ---
async function init() {
  const [providers, skills] = await Promise.all([
    fetch(`${API}/api/providers`).then((r) => r.json()),
    fetch(`${API}/api/skills`).then((r) => r.json()),
  ]);

  allSkills = skills;

  providers.available.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
    opt.selected = p === providers.current;
    providerSelect.appendChild(opt);
  });

  renderCards();
}

function renderCards() {
  cardGrid.innerHTML = "";

  allSkills.forEach((skill) => {
    const card = document.createElement("button");
    card.className = "skill-card";
    card.setAttribute("role", "listitem");

    const imageHtml = skill.image
      ? `<div class="card-image"><img src="${skillImage(skill.image)}" alt="${escapeHtml(skill.name)}" loading="lazy"></div>`
      : `<div class="card-image-placeholder">${skill.avatar || "&#x1f916;"}</div>`;

    const tagsHtml = (skill.tags || [])
      .map((t) => `<span class="card-tag">${escapeHtml(t)}</span>`)
      .join("");

    card.innerHTML = `
      ${imageHtml}
      <div class="card-body">
        <div class="card-name">${escapeHtml(skill.name)}</div>
        <div class="card-desc">${escapeHtml(skill.description)}</div>
        ${tagsHtml ? `<div class="card-tags">${tagsHtml}</div>` : ""}
      </div>
    `;

    card.addEventListener("click", () => enterChat(skill));
    cardGrid.appendChild(card);
  });

  // Add "Create New" card at the end
  const createCard = document.createElement("button");
  createCard.className = "create-card";
  createCard.setAttribute("role", "listitem");
  createCard.innerHTML = `
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="16"/>
      <line x1="8" y1="12" x2="16" y2="12"/>
    </svg>
    <span class="create-card-label">Create New Skill</span>
    <span class="create-card-sub">Powered by Nuwa</span>
  `;
  createCard.addEventListener("click", openCreateModal);
  cardGrid.appendChild(createCard);
}

// --- Chat ---
function enterChat(skill) {
  currentSkill = skill;
  messages = [];

  if (skill.image) {
    chatHeaderImg.src = skillImage(skill.image);
    chatHeaderImg.style.display = "block";
  } else {
    chatHeaderImg.style.display = "none";
  }
  chatHeaderName.textContent = skill.name;
  chatHeaderProvider.textContent = providerSelect.options[providerSelect.selectedIndex].text;

  homeView.classList.add("hidden");
  chatView.classList.remove("hidden");

  renderMessages();
  userInput.focus();
}

function exitChat() {
  homeView.classList.remove("hidden");
  chatView.classList.add("hidden");
  currentSkill = null;
  messages = [];
}

function renderMessages() {
  messagesEl.innerHTML = "";

  if (messages.length === 0 && currentSkill) {
    const intro = document.createElement("div");
    intro.className = "chat-intro";
    const imgHtml = currentSkill.image
      ? `<img class="intro-avatar" src="${skillImage(currentSkill.image)}" alt="${escapeHtml(currentSkill.name)}">`
      : `<div class="intro-avatar" style="display:flex;align-items:center;justify-content:center;font-size:32px;background:var(--bg-elevated);">${currentSkill.avatar || "&#x1f916;"}</div>`;
    intro.innerHTML = `
      ${imgHtml}
      <h2>${escapeHtml(currentSkill.name)}</h2>
      <p>${escapeHtml(currentSkill.description)}</p>
    `;
    messagesEl.appendChild(intro);
    return;
  }

  messages.forEach((msg, i) => {
    const bubble = document.createElement("div");
    bubble.className = `message ${msg.role}`;
    const isLastAssistant = msg.role === "assistant" && i === messages.length - 1;
    const isEmpty = !msg.content;

    if (isLastAssistant && isEmpty && isStreaming) {
      bubble.innerHTML = `<div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
    } else {
      bubble.innerHTML = `<div class="message-content">${formatContent(msg.content)}</div>`;
    }
    messagesEl.appendChild(bubble);
  });

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatContent(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br>");
}

function escapeHtml(text) {
  const el = document.createElement("span");
  el.textContent = text;
  return el.innerHTML;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || !currentSkill || isStreaming) return;

  messages.push({ role: "user", content: text });
  userInput.value = "";
  autoResize();
  messages.push({ role: "assistant", content: "" });

  isStreaming = true;
  sendBtn.disabled = true;
  userInput.disabled = true;
  renderMessages();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        skill_id: currentSkill.id,
        messages: messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
        provider: providerSelect.value,
      }),
    });

    await readStream(res, (text) => {
      messages[messages.length - 1].content += text;
      renderMessages();
    });
  } catch (err) {
    messages[messages.length - 1].content += `\n\n[Connection error: ${err.message}]`;
    renderMessages();
  }

  isStreaming = false;
  sendBtn.disabled = false;
  userInput.disabled = false;
  userInput.focus();
}

async function readStream(res, onText) {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") return;
      try {
        const parsed = JSON.parse(data);
        if (parsed.error) {
          onText(`\n[Error: ${parsed.error}]`);
        } else if (parsed.text) {
          onText(parsed.text);
        }
      } catch {}
    }
  }
}

function autoResize() {
  userInput.style.height = "auto";
  userInput.style.height = Math.min(userInput.scrollHeight, 150) + "px";
}

// --- Create Skill Modal ---
function openCreateModal() {
  createModal.classList.remove("hidden");
  createStepInput.classList.remove("hidden");
  createStepProgress.classList.add("hidden");
  createStepDone.classList.add("hidden");
  createName.value = "";
  createContext.value = "";
  createOutput.textContent = "";
  createdSkillId = null;
  createStartBtn.disabled = true;
  createName.focus();
}

function closeCreateModal() {
  createModal.classList.add("hidden");
}

async function startCreation() {
  const name = createName.value.trim();
  if (!name) return;

  // Switch to progress view
  createStepInput.classList.add("hidden");
  createStepProgress.classList.remove("hidden");
  progressLabel.textContent = `Generating ${name}'s cognitive framework...`;
  createOutput.textContent = "";
  createdSkillId = null;

  try {
    const res = await fetch(`${API}/api/skills/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        person_name: name,
        extra_context: createContext.value.trim(),
        provider: providerSelect.value,
      }),
    });

    let fullText = "";
    await readStream(res, (text) => {
      fullText += text;

      // Check for completion marker
      const marker = fullText.match(/<!-- SKILL_CREATED:(.+?) -->/);
      if (marker) {
        createdSkillId = marker[1];
        // Remove marker from display
        const displayText = fullText.replace(/\n*<!-- SKILL_CREATED:.+? -->/, "");
        createOutput.textContent = displayText;
      } else {
        createOutput.textContent = fullText;
      }
      createOutput.scrollTop = createOutput.scrollHeight;
    });

    if (createdSkillId) {
      // Reload skills and show done
      const skills = await fetch(`${API}/api/skills/reload`, { method: "POST" }).then((r) => r.json());
      allSkills = await fetch(`${API}/api/skills`).then((r) => r.json());

      createStepProgress.classList.add("hidden");
      createStepDone.classList.remove("hidden");
      doneTitle.textContent = `${name} is ready!`;
    } else {
      progressLabel.textContent = "Generation complete (check output for issues)";
    }
  } catch (err) {
    progressLabel.textContent = `Error: ${err.message}`;
  }
}

function chatWithCreatedSkill() {
  if (!createdSkillId) return;
  const skill = allSkills.find((s) => s.id === createdSkillId);
  if (skill) {
    closeCreateModal();
    renderCards();
    enterChat(skill);
  }
}

// --- Events ---
userInput.addEventListener("input", () => {
  autoResize();
  sendBtn.disabled = !userInput.value.trim();
});

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", sendMessage);
backBtn.addEventListener("click", exitChat);

clearBtn.addEventListener("click", () => {
  if (currentSkill) {
    messages = [];
    renderMessages();
    userInput.focus();
  }
});

// Create modal events
createName.addEventListener("input", () => {
  createStartBtn.disabled = !createName.value.trim();
});

createName.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && createName.value.trim()) {
    e.preventDefault();
    startCreation();
  }
});

createStartBtn.addEventListener("click", startCreation);
modalClose.addEventListener("click", closeCreateModal);
createModal.addEventListener("click", (e) => {
  if (e.target === createModal) closeCreateModal();
});
doneChatBtn.addEventListener("click", chatWithCreatedSkill);

init();
