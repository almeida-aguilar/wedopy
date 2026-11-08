document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar toggle
  const toggleBtn = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".site-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });

    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Active link detection
  const currentPath = window.location.pathname;
  const sidebarLinks = document.querySelectorAll(".sidebar-links a");
  sidebarLinks.forEach((link) => {
    const href = link.getAttribute("href");
    if (href && (currentPath.endsWith(href) || currentPath.endsWith(href + "/") || (href !== "/" && currentPath.includes(href)))) {
      link.classList.add("active");
    }
  });

  // Code copy buttons
  document.querySelectorAll("pre").forEach((pre) => {
    const container = document.createElement("div");
    container.className = "code-container";
    pre.parentNode.insertBefore(container, pre);
    container.appendChild(pre);

    const button = document.createElement("button");
    button.className = "copy-button";
    button.textContent = "Copiar";
    button.setAttribute("aria-label", "Copiar código al portapapeles");
    container.appendChild(button);

    button.addEventListener("click", async () => {
      const code = pre.querySelector("code") ? pre.querySelector("code").innerText : pre.innerText;
      try {
        await navigator.clipboard.writeText(code);
        button.textContent = "¡Copiado!";
        setTimeout(() => {
          button.textContent = "Copiar";
        }, 2000);
      } catch (err) {
        console.error("Error al copiar:", err);
      }
    });
  });

  // Sidebar filter
  const searchInput = document.querySelector("#sidebar-filter");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      sidebarLinks.forEach((link) => {
        const text = link.textContent.toLowerCase();
        const li = link.closest("li");
        if (!li) return;
        if (!query || text.includes(query)) {
          li.style.display = "";
        } else {
          li.style.display = "none";
        }
      });
    });
  }
});
