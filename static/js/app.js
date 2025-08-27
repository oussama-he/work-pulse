document.querySelectorAll(".expand-btn").forEach((expandButton) => {
  // check if the text is clipped, otherwise remove the button and return
  if (
    expandButton.previousElementSibling.scrollHeight <=
    expandButton.previousElementSibling.clientHeight
  ) {
    expandButton.remove();
    return;
  }

  expandButton.addEventListener("click", () => {
    if (!expandButton.dataset.expand) {
      expandButton.previousElementSibling.classList.remove("text-clip");
      expandButton.dataset.expand = "true";
      expandButton.textContent = "Show less";
    } else {
      expandButton.previousElementSibling.classList.add("text-clip");
      delete expandButton.dataset.expand;
      expandButton.textContent = "Show more";
    }
  });
});


function renderChart(element, config) {
    window.ApexCharts &&
        new ApexCharts(element, config).render();
}
