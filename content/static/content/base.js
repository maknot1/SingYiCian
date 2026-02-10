document.addEventListener("DOMContentLoaded", () => {

    /* ===== Mobile menu ===== */
    const toggle = document.querySelector(".nav-toggle");
    const menu = document.querySelector(".nav-menu");

    if (toggle && menu) {
        toggle.addEventListener("click", () => {
            menu.classList.toggle("open");
        });
    }

    /* ===== Table of contents ===== */
    const article = document.querySelector(".article-content");
    const tocList = document.getElementById("toc-list");

    if (article && tocList) {

        const headers = article.querySelectorAll("h2, h3");
        if (!headers.length) return;

        headers.forEach((header, index) => {

            // не перезаписываем существующий id
            if (!header.id) {
                header.id = "section-" + index;
            }

            const li = document.createElement("li");
            li.classList.add("toc-item");
            li.classList.add("toc-" + header.tagName.toLowerCase());

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

            headers.forEach(header => {
                const rect = header.getBoundingClientRect();
                if (rect.top <= OFFSET) {
                    current = header.id;
                }
            });

            links.forEach(link => {
                link.classList.toggle(
                    "active",
                    current && link.getAttribute("href") === "#" + current
                );
            });
        });
    }

});

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

  }, 60000); // 1 минута
}
