/*
  shorten long team member bios to a few lines, with a "read more" button
  that expands them in place. bios that already fit are left alone.
*/

{
  const onLoad = () => {
    const bodies = document.querySelectorAll(".member-bio-body");
    for (const [index, body] of bodies.entries()) {
      // collapse, and undo if nothing is actually hidden
      body.classList.add("collapsed");
      if (body.scrollHeight <= body.clientHeight + 2) {
        body.classList.remove("collapsed");
        continue;
      }

      body.id ||= `member-bio-body-${index}`;

      // toggle button after bio
      const button = document.createElement("button");
      button.className = "member-bio-more";
      button.setAttribute("aria-controls", body.id);
      button.setAttribute("aria-expanded", "false");
      button.textContent = "Read more";
      button.addEventListener("click", () => {
        const collapsed = body.classList.toggle("collapsed");
        button.setAttribute("aria-expanded", String(!collapsed));
        button.textContent = collapsed ? "Read more" : "Show less";
      });
      body.after(button);
    }
  };

  // after page loads
  window.addEventListener("load", onLoad);
}
