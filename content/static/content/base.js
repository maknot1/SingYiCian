document.addEventListener("DOMContentLoaded", () => {
  /* ===== Mobile nav toggle ===== */
  const burger = document.querySelector(".burger");
  const navMenu = document.getElementById("navMenu");

  if (!burger || !navMenu) return;

  const isMobile = () => window.matchMedia("(max-width: 1024px)").matches;

  function closeMenu() {
    navMenu.classList.remove("active");
    document.body.classList.remove("menu-open");
    burger.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    navMenu.classList.add("active");
    document.body.classList.add("menu-open");
    burger.setAttribute("aria-expanded", "true");
  }

  function toggleMenu() {
    const isOpen = navMenu.classList.contains("active");
    if (isOpen) closeMenu();
    else openMenu();
  }

  burger.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleMenu();
  });

  // закрыть по клику вне меню
  document.addEventListener("click", (e) => {
    if (!navMenu.classList.contains("active")) return;

    const clickedInsideNav = navMenu.contains(e.target);
    const clickedBurger = burger.contains(e.target);

    if (!clickedInsideNav && !clickedBurger) closeMenu();
  });

  // закрыть по ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });

  // закрыть по клику на пункт меню - только на мобиле/планшете
  navMenu.addEventListener("click", (e) => {
    const link = e.target.closest("a");
    if (link && isMobile()) closeMenu();
  });

  // если расширили экран до десктопа - закрываем drawer и убираем overlay
  window.addEventListener("resize", () => {
    if (!isMobile()) closeMenu();
  });

  /* ===== Table of contents ===== */
  const article = document.querySelector(".article-content");
  const tocList = document.getElementById("toc-list");

  if (article && tocList) {
    const headers = article.querySelectorAll("h2, h3");
    if (headers.length) {
      headers.forEach((header, index) => {
        if (!header.id) header.id = "section-" + index;

        const li = document.createElement("li");
        li.classList.add("toc-item", "toc-" + header.tagName.toLowerCase());

        const a = document.createElement("a");
        a.href = "#" + header.id;
        a.textContent = header.textContent;

        li.appendChild(a);
        tocList.appendChild(li);
      });

      const links = tocList.querySelectorAll("a");
      const OFFSET = 120;

      window.addEventListener("scroll", () => {
        let current = null;

        headers.forEach((header) => {
          const rect = header.getBoundingClientRect();
          if (rect.top <= OFFSET) current = header.id;
        });

        links.forEach((link) => {
          link.classList.toggle(
            "active",
            current && link.getAttribute("href") === "#" + current
          );
        });
      });
    }
  }

  /* ===== Image rotator ===== */
  const images = [
    "/static/content/domik1.jpg",
    "/static/content/domik2.jpg",
    "/static/content/domik3.jpg",
    "/static/content/domik4.jpg"
  ];

  let currentIndex = 0;
  const img = document.getElementById("rotator-image");

  if (img) {
    setInterval(() => {
      img.classList.add("fade-out");

      setTimeout(() => {
        currentIndex = (currentIndex + 1) % images.length;
        img.src = images[currentIndex];
        img.classList.remove("fade-out");
      }, 600);
    }, 60000);
  }
});
