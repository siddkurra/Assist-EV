const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const selected = new Set();
const placed = new Map();
const courseInfo = new Map();
let dragging = null;

const codeOf = (c) => (c[0] && c[1] ? `${c[0]} ${c[1]}` : "");

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function getJSON(url, options) {
  const res = await fetch(url, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

function showStatus(message = "") {
  const status = $("#status");
  status.textContent = message;
  status.classList.toggle("hidden", !message);
}

function addPair() {
  const row = $("#pair-template").content.firstElementChild.cloneNode(true);
  const school = $(".school", row);
  const major = $(".major", row);

  school.addEventListener("change", async () => {
    major.length = 1;
    major.classList.add("hidden");
    if (!school.value) return;
    try {
      const data = await getJSON(`/majors/${school.value}`);
      data.majors.forEach((m) => major.add(new Option(m, m)));
      major.classList.remove("hidden");
      showStatus();
    } catch (err) {
      showStatus(err.message);
    }
  });

  $("#pairs").append(row);
}

function loadCourseInfo(code) {
  if (!courseInfo.has(code)) {
    const [subject, number] = code.split(" ");
    const url = `/course/${encodeURIComponent(subject)}/${encodeURIComponent(number)}`;
    courseInfo.set(code, getJSON(url).catch(() => null));
  }
  return courseInfo.get(code);
}

async function fillPopup(popup, code) {
  const info = await loadCourseInfo(code);
  popup.replaceChildren(el("div", "font-bold text-base mb-1", code));

  if (!info || !info.offered) {
    popup.append(el("p", "text-gray-500", "Not on the current EVC schedule."));
    return;
  }

  const { sections, formats, instructors } = info;
  popup.append(el("p", "text-gray-600 mb-2", `${sections.length} section${sections.length === 1 ? "" : "s"} · ${formats.join(", ")}`));

  if (instructors.length) {
    const shown = instructors.slice(0, 4).join("; ");
    const extra = instructors.length > 4 ? ` +${instructors.length - 4} more` : "";
    popup.append(el("p", "mb-2", `Instructors: ${shown}${extra}`));
  }

  const list = el("ul", "space-y-1");
  sections.slice(0, 4).forEach((s) => {
    list.append(el("li", "text-gray-700", `${s.section} · ${s.format} · ${s.meets} · ${s.room}`));
  });
  popup.append(list);
  if (sections.length > 4) {
    popup.append(el("p", "text-gray-400 mt-1", `+${sections.length - 4} more sections`));
  }
}

function startDrag(e, code, node) {
  dragging = code;
  node.classList.add("dragging");
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", code);
}

function endDrag(node) {
  node.classList.remove("dragging");
  dragging = null;
  $$(".drag-over").forEach((z) => z.classList.remove("drag-over"));
}

function wireZone(zone) {
  zone.addEventListener("dragover", (e) => {
    if (!dragging) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", (e) => {
    if (!zone.contains(e.relatedTarget)) zone.classList.remove("drag-over");
  });
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const code = dragging || e.dataTransfer.getData("text/plain");
    if (code && selected.has(code)) place(code, zone);
  });
}

function unplace(code) {
  const zone = placed.get(code);
  if (!zone) return;
  $$(".term-course", zone).find((n) => n.dataset.course === code)?.remove();
  placed.delete(code);
}

function place(code, zone) {
  if (placed.get(code) === zone) return;
  unplace(code);
  if (zone.classList.contains("term-zone")) {
    placed.set(code, zone);
    zone.append(termCourse(code));
  }
  renderList();
}

function termCourse(code) {
  const item = el("div", "term-course");
  item.draggable = true;
  item.dataset.course = code;
  item.addEventListener("dragstart", (e) => startDrag(e, code, item));
  item.addEventListener("dragend", () => endDrag(item));

  const remove = el("button", "term-remove", "×");
  remove.title = "Unschedule";
  remove.addEventListener("click", () => {
    unplace(code);
    renderList();
  });

  item.append(el("span", "", code), remove);
  return item;
}

function removeCourse(code) {
  unplace(code);
  selected.delete(code);
  renderList();
}

function renderList() {
  const list = $("#course-list");
  $$(".chip", list).forEach((n) => n.remove());

  [...selected].sort().forEach((code) => {
    if (placed.has(code)) return;

    const chip = el("div", "chip");
    const label = el("span", "chip-label", code);
    label.draggable = true;
    label.addEventListener("dragstart", (e) => startDrag(e, code, label));
    label.addEventListener("dragend", () => endDrag(label));

    const popup = el("div", "course-popup", "Loading…");
    chip.addEventListener("mouseenter", () => fillPopup(popup, code), { once: true });

    const remove = el("button", "chip-remove", "×");
    remove.title = "Remove from plan";
    remove.addEventListener("click", () => removeCourse(code));

    chip.append(label, popup, remove);
    list.append(chip);
  });

  $$(".course-pill[data-course]").forEach((p) => p.classList.toggle("picked", selected.has(p.dataset.course)));
}

function renumberYears() {
  $$(".year").forEach((year, i) => {
    $(".year-title", year).textContent = `Academic Year ${i + 1}`;
  });
}

function addYear() {
  const year = $("#year-template").content.firstElementChild.cloneNode(true);
  $$(".term-zone", year).forEach(wireZone);
  $(".remove-year", year).addEventListener("click", () => {
    $$(".term-course", year).forEach((n) => placed.delete(n.dataset.course));
    year.remove();
    renumberYears();
    renderList();
  });
  $("#years").append(year);
  renumberYears();
}

function pill(course, tone, pickable) {
  const code = codeOf(course);
  const node = el("span", `course-pill inline-block text-sm px-2 py-1 m-1 rounded ${tone}`, code ? `${code}: ${course[2]}` : course[2]);
  if (pickable && code) {
    node.dataset.course = code;
    node.classList.add("cursor-pointer");
    node.title = "Click to add or remove from your plan";
    node.addEventListener("click", () => (selected.has(code) ? removeCourse(code) : (selected.add(code), renderList())));
  }
  return node;
}

function renderResults(data) {
  const results = $("#results");
  results.replaceChildren();

  for (const [title, payload] of Object.entries(data)) {
    const card = el("article", "bg-white shadow p-4 rounded");
    card.append(el("h2", "text-xl font-bold mb-4", title));
    results.append(card);

    if (!Array.isArray(payload)) {
      card.append(el("p", "text-sm text-red-600", "Couldn't load this agreement from ASSIST. Try searching again."));
      continue;
    }

    const [receiving, sending] = payload;
    if (!receiving.length) {
      card.append(el("p", "text-sm text-gray-500", "No articulation agreement on file for this major."));
      continue;
    }

    const body = el("div", "space-y-4");
    receiving.forEach((groups, i) => {
      const row = el("div", "grid grid-cols-2 gap-4 items-center");
      const recv = el("div", "bg-blue-50 p-2 rounded");
      groups.flat().forEach((c) => recv.append(pill(c, "bg-blue-200 text-blue-800", false)));
      const send = el("div", "bg-green-50 p-2 rounded");
      (sending[i] || []).forEach((c) => send.append(pill(c, "bg-green-200 text-green-800", true)));
      row.append(recv, send);
      body.append(row);
    });
    card.append(body);
  }
}

async function search() {
  const pairs = $$(".pair")
    .map((row) => ({ id: Number($(".school", row).value), major: $(".major", row).value }))
    .filter((p) => p.id && p.major);
  if (!pairs.length) return showStatus("Pick at least one school and major.");

  const button = $("#search");
  button.disabled = true;
  button.textContent = "SEARCHING…";
  showStatus();

  try {
    const data = await getJSON("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pairs),
    });

    Object.values(data)
      .filter(Array.isArray)
      .forEach(([, sending]) => sending.flat().forEach((c) => codeOf(c) && selected.add(codeOf(c))));

    renderResults(data);
    $("#planner").classList.remove("hidden");
    if (!$(".year")) addYear();
    renderList();
  } catch (err) {
    showStatus(err.message);
  } finally {
    button.disabled = false;
    button.textContent = "SEARCH";
  }
}

$("#subject").addEventListener("change", async (e) => {
  const number = $("#number");
  number.length = 1;
  if (!e.target.value) return;
  const data = await getJSON(`/numbers/${encodeURIComponent(e.target.value)}`);
  data.numbers.forEach((n) => number.add(new Option(n, n)));
});

$("#add-course").addEventListener("click", () => {
  const subject = $("#subject").value;
  const number = $("#number").value;
  if (!subject || !number) return;
  selected.add(`${subject} ${number}`);
  renderList();
});

$("#add-pair").addEventListener("click", addPair);
$("#search").addEventListener("click", search);
$("#add-year").addEventListener("click", addYear);

wireZone($("#course-list"));
addPair();
