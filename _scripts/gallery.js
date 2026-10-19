/*
  home page photo slideshow: advances every few seconds, with previous/next,
  dots to jump to a photo, and a pause button. starts paused for people who
  have asked their system for reduced motion. without javascript, the first
  photo just shows on its own.
*/

{
  const delay = 6000;

  const onLoad = () => {
    for (const gallery of document.querySelectorAll(".gallery")) {
      const slides = [...gallery.querySelectorAll(".gallery-slide")];
      if (slides.length < 2) continue;

      const caption = gallery.querySelector(".gallery-caption");
      const dots = [...gallery.querySelectorAll(".gallery-dot")];
      const pause = gallery.querySelector(".gallery-pause");
      let current = 0;
      let playing = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      let timer;

      const show = (index) => {
        current = (index + slides.length) % slides.length;
        slides.forEach((slide, i) => {
          slide.classList.toggle("active", i === current);
          slide.setAttribute("aria-hidden", String(i !== current));
        });
        dots.forEach((dot, i) => {
          if (i === current) dot.setAttribute("aria-current", "true");
          else dot.removeAttribute("aria-current");
        });
        caption.textContent = slides[current].dataset.caption;
      };

      const restart = () => {
        clearInterval(timer);
        if (playing) timer = setInterval(() => show(current + 1), delay);
      };

      const setPlaying = (value) => {
        playing = value;
        pause.setAttribute("aria-label", playing ? "Pause slideshow" : "Play slideshow");
        pause.innerHTML = `<i class="fa-solid fa-${playing ? "pause" : "play"}" aria-hidden="true"></i>`;
        restart();
      };

      for (const arrow of gallery.querySelectorAll(".gallery-arrow")) {
        arrow.addEventListener("click", () => {
          show(current + Number(arrow.dataset.dir));
          restart();
        });
        arrow.hidden = false;
      }
      dots.forEach((dot) =>
        dot.addEventListener("click", () => {
          show(Number(dot.dataset.index));
          restart();
        })
      );
      pause.addEventListener("click", () => setPlaying(!playing));
      gallery.querySelector(".gallery-controls").hidden = false;

      setPlaying(playing);
    }
  };

  // after page loads
  window.addEventListener("load", onLoad);
}
