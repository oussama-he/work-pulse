document.querySelectorAll(".expand-btn").forEach((expandButton) => {
  // check if the text is clipped, otherwise remove the button and return
  const textClipElement = expandButton.previousElementSibling;
  if (
    textClipElement.scrollHeight <=
    textClipElement.clientHeight
  ) {
    expandButton.remove();
    return;
  }

  const expandButtonHandler = () => {
    if (!expandButton.dataset.expand) {
      textClipElement.classList.remove("text-clip");
      expandButton.dataset.expand = "true";
      expandButton.textContent = "Show less";
    } else {
      textClipElement.classList.add("text-clip");
      delete expandButton.dataset.expand;
      expandButton.textContent = "Show more";
    }
  }
  expandButton.addEventListener("click", () => {
    expandButtonHandler();
  });

  // add the ability to select text without expanding/collapsing textClipElement
  textClipElement.addEventListener("mousedown", event => {
    const { clientX: x1, clientY: y1 } = event;

    textClipElement.addEventListener("mouseup", event => {
      const { clientX: x2, clientY: y2 } = event;

      if (x1 === x2 && y1 === y2) {
        expandButtonHandler();
      }
    }, { once: true });
  });
});
