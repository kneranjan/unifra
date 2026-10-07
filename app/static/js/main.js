// Hero Word Rotator
const words = document.querySelectorAll(".rotator .word");
if (words.length > 0) {
  let wordIndex = 0;
  setInterval(() => {
    words[wordIndex].classList.remove("is-active");
    wordIndex = (wordIndex + 1) % words.length;
    words[wordIndex].classList.add("is-active");
  }, 2200);
}

// Hero Dashboard Carousel
const slides = [...document.querySelectorAll(".dash-card")];
if (slides.length > 0) {
  let slide = 0;
  function showSlide(next) {
    slides[slide].classList.remove("is-active");
    slide = (next + slides.length) % slides.length;
    slides[slide].classList.add("is-active");
  }
  document.querySelectorAll(".circle-btn").forEach((btn) => {
    btn.addEventListener("click", () => showSlide(slide + Number(btn.dataset.dir)));
  });
  setInterval(() => showSlide(slide + 1), 6000);
}

// Navigation Dropdown Menus
document.querySelectorAll(".nav-drop").forEach((btn) => {
  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    const li = btn.parentElement;
    const open = li.classList.contains("open");
    document.querySelectorAll(".nav-links li").forEach((item) => item.classList.remove("open"));
    document.querySelectorAll(".nav-drop").forEach((b) => b.setAttribute("aria-expanded", "false"));
    if (!open) {
      li.classList.add("open");
      btn.setAttribute("aria-expanded", "true");
    }
  });
});
document.addEventListener("click", () => {
  document.querySelectorAll(".nav-links li").forEach((item) => item.classList.remove("open"));
});

// Mobile Hamburger Drawer
const drawer = document.querySelector(".mobile-drawer");
const hamburger = document.querySelector(".hamburger");
if (hamburger && drawer) {
  hamburger.addEventListener("click", () => {
    const open = drawer.classList.toggle("is-open");
    if (open) drawer.removeAttribute("hidden");
    else drawer.setAttribute("hidden", "");
    hamburger.setAttribute("aria-expanded", String(open));
  });
}

// Tab Switching
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => {
      t.classList.remove("is-active");
      t.setAttribute("aria-selected", "false");
    });
    tab.classList.add("is-active");
    tab.setAttribute("aria-selected", "true");
    const id = tab.dataset.tab;
    document.querySelectorAll(".panel").forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.panel === id);
    });
  });
});

// Modal Dialogs
document.querySelectorAll('a[href^="#"]').forEach((link) => {
  const href = link.getAttribute("href");
  if (href && href.length > 1) {
    const id = href.slice(1);
    const dialog = document.getElementById(id);
    if (dialog && dialog.tagName === "DIALOG") {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        dialog.showModal();
      });
    }
  }
});

// Search Button
const searchBtn = document.querySelector(".search-btn");
if (searchBtn) {
  searchBtn.addEventListener("click", () => {
    const query = window.prompt("Search Unifra Discovered Hosts & Traces");
    if (query) {
      fetch(`/hosts/${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
          if (data && data.ip) {
            window.alert(`Host Found: ${data.ip} (${data.hostname || 'No hostname'})\nOS: ${data.os_guess || 'Unknown'}\nVendor: ${data.vendor || 'Unknown'}`);
          } else {
            window.alert(`No exact host match for "${query}". Check live topology at /topology/view`);
          }
        })
        .catch(() => {
          window.alert(`Searching Unifra live discovery for "${query}"…`);
        });
    }
  });
}

// Chatbot Interactive Widget Logic
const fab = document.getElementById("chatbot-fab");
const widget = document.getElementById("chatbot-widget");
const closeBtn = document.getElementById("chatbot-close");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("chat-send");
const chatMessages = document.getElementById("chat-messages");

if (fab && widget) {
  fab.addEventListener("click", () => {
    widget.classList.toggle("hidden");
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      widget.classList.add("hidden");
    });
  }

  async function handleSend() {
    const text = chatInput.value.trim();
    if (!text) return;

    // Append User Message
    const userMsg = document.createElement("div");
    userMsg.className = "chat-msg user";
    userMsg.textContent = text;
    chatMessages.appendChild(userMsg);

    chatInput.value = "";
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const lower = text.toLowerCase();
    const botMsg = document.createElement("div");
    botMsg.className = "chat-msg bot";

    if (lower.includes("host") || lower.includes("ip") || lower.includes("device")) {
      try {
        const res = await fetch("/hosts/");
        const hosts = await res.json();
        if (Array.isArray(hosts) && hosts.length > 0) {
          botMsg.textContent = `Unifra has discovered ${hosts.length} live host(s) on your network. Top host: ${hosts[0].ip} (${hosts[0].hostname || 'Unknown'}). You can view full topology at /topology/view!`;
        } else {
          botMsg.textContent = "Unifra Discovery Agent is currently scanning local subnets via Nmap and PySNMP. Discovered hosts will appear live at /hosts/.";
        }
      } catch (e) {
        botMsg.textContent = "Unifra Discovery Agent scans local networks (IPs, MACs, Open Ports, SNMP data) with read-only outbound credentials.";
      }
    } else if (lower.includes("container") || lower.includes("docker") || lower.includes("k8s")) {
      try {
        const res = await fetch("/containers/");
        const containers = await res.json();
        if (Array.isArray(containers) && containers.length > 0) {
          botMsg.textContent = `Unifra Docker SDK detected ${containers.length} container(s). First container: ${containers[0].name} (${containers[0].state}).`;
        } else {
          botMsg.textContent = "Unifra tracks Docker containers & Kubernetes pods in real time via local Docker SDK integration.";
        }
      } catch (e) {
        botMsg.textContent = "Unifra Docker SDK integration tracks local container topologies and maps them to host IPs.";
      }
    } else if (lower.includes("cost") || lower.includes("aws") || lower.includes("pricing")) {
      botMsg.textContent = "Unifra's Cost Agent continuously monitors AWS APIs & billing, recommending auto-scaling and spot instances to save up to 40% on hybrid infra spend.";
    } else if (lower.includes("agent") || lower.includes("agno") || lower.includes("sre")) {
      botMsg.textContent = "Unifra operates 4 specialized AI Agents (Cost, Health, API Perf, and Correlation) orchestrated via Agno for real-time root-cause analysis & automated control.";
    } else if (lower.includes("security") || lower.includes("access") || lower.includes("snmp")) {
      botMsg.textContent = "Unifra discovery agents require only read-only access (SNMP, read-only SSH/Docker/K8s). Outbound-only traffic with zero open inbound firewall ports!";
    } else {
      botMsg.textContent = "Unifra unifies your hybrid infrastructure—cloud, on-prem, and edge sensors—into a single OpenTelemetry-powered AI platform. How else can I assist your team?";
    }

    chatMessages.appendChild(botMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  if (sendBtn) sendBtn.addEventListener("click", handleSend);
  if (chatInput) {
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleSend();
    });
  }
}
