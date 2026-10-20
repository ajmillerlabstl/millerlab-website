/*
  click a photo in a grid (e.g. the photos page) to see it bigger, with its
  caption. previous/next buttons and arrow keys move through the grid; esc,
  the close button, or clicking outside the photo closes it.
*/

{
  const onLoad = () => {
    // photos in grids that don't already link somewhere
    const figures = [...document.querySelectorAll(".grid .figure")].filter(
      (figure) => !figure.querySelector(".figure-image[href]")
    );
    if (!figures.length) return;

    const dialog = document.createElement("dialog");
    dialog.className = "lightbox";
    dialog.setAttribute("aria-label", "Photo viewer");
    dialog.innerHTML = `
      <button class="lightbox-close" aria-label="Close"><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
      <button class="lightbox-arrow" data-dir="-1" aria-label="Previous photo"><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>
      <figure>
        <img alt="">
        <figcaption><span class="lightbox-caption"></span><span class="lightbox-count"></span></figcaption>
      </figure>
      <button class="lightbox-arrow" data-dir="1" aria-label="Next photo"><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></button>
    `;
    document.body.append(dialog);

    const image = dialog.querySelector("img");
    const caption = dialog.querySelector(".lightbox-caption");
    const count = dialog.querySelector(".lightbox-count");
    let current = 0;

    const show = (index) => {
      current = (index + figures.length) % figures.length;
      const figure = figures[current];
      const source = figure.querySelector("img");
      image.src = source.currentSrc || source.src;
      image.alt = source.alt;
      caption.textContent = figure.querySelector(".figure-caption")?.textContent.trim() || "";
      count.textContent = `${current + 1} / ${figures.length}`;
    };

    figures.forEach((figure, index) => {
      const link = figure.querySelector(".figure-image");
      link.setAttribute("role", "button");
      link.setAttribute("tabindex", "0");
      link.style.cursor = "zoom-in";
      const open = (event) => {
        event.preventDefault();
        show(index);
        dialog.showModal();
      };
      link.addEventListener("click", open);
      link.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") open(event);
      });
    });

    for (const arrow of dialog.querySelectorAll(".lightbox-arrow"))
      arrow.addEventListener("click", () => show(current + Number(arrow.dataset.dir)));
    dialog.querySelector(".lightbox-close").addEventListener("click", () => dialog.close());

    // click outside photo closes
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });

    dialog.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") show(current - 1);
      if (event.key === "ArrowRight") show(current + 1);
    });

    // stop page scrolling behind the viewer
    dialog.addEventListener("close", () => document.body.style.removeProperty("overflow"));
    new MutationObserver(() => {
      if (dialog.open) document.body.style.overflow = "hidden";
    }).observe(dialog, { attributes: true, attributeFilter: ["open"] });
  };

  // after page loads
  window.addEventListener("load", onLoad);
}
