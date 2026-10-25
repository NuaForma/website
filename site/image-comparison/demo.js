"use strict";

const demoImage = document.querySelector("#comparison-result");
const demoButtons = [...document.querySelectorAll("[data-comparison]")];
const results = {
  "all-pixels": { file: "all-pixels.png", regions: "3", percent: "0.09875%", policy: "No exclusions · per-pixel tolerance 0.1", alt: "Actual image with red outlines around the changed date and two changed amounts." },
  "exclude-date": { file: "exclude-date.png", regions: "2", percent: "0.06387%", policy: "Date excluded · per-pixel tolerance 0.1", alt: "Actual image with a green outline around the excluded date and red outlines around the two changed amounts." }
};
demoButtons.forEach(button => button.addEventListener("click", () => {
  const selected = results[button.dataset.comparison];
  if (!selected) return;
  demoButtons.forEach(other => other.setAttribute("aria-pressed", String(other === button)));
  demoImage.src = selected.file;
  demoImage.alt = selected.alt;
  document.querySelector("#comparison-regions").textContent = selected.regions;
  document.querySelector("#comparison-percent").textContent = selected.percent;
  document.querySelector("#comparison-policy").textContent = selected.policy;
}));
