document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".js-empty");
  const form = container.querySelector("form");

  form.onsubmit = (e) => {
    e.preventDefault();
    container.classList.add("load");
    const data = new FormData(e.target);

    setTimeout(() => {
      container.classList.remove("load");
      container.classList.add(!!data.get("file").name ? "success" : "error");
      e.target.reset();
    }, 2000);
  };
});
