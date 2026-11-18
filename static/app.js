// Hunch front end: plain JS. Feed -> card -> guess picker -> POST /guess -> verdict panel.
const GUESSES = [
  ["topic_affinity", "Topic affinity"],
  ["followed_account", "Followed account"],
  ["popularity", "Popularity"],
  ["recency", "Recency"],
  ["similar_users", "Similar users"],
  ["other", "Something else (e.g. a friend shared it)"],
];
const NAMES = Object.fromEntries(GUESSES);
// Each verdict is a word plus a symbol, so colour is never the only signal.
const MARKS = { "Supported": "✓", "Partly supported": "◐", "Not supported": "✕", "Not used": "○" };

// Cosmetic placeholders only: names, captions and pictures are picked from the item id.
// They play no part in ranking and carry no hint of why a post is shown
// (no likes, times, follow labels or topics, which would imply a signal).
const AUTHORS = ["Maya Ortiz", "Dev Patel", "Lena Fischer", "Tomas Reyes", "Aiko Tanaka",
                 "Noah Bennett", "Zara Hussain", "Ola Nkemelu", "Iris Lindqvist", "Sam Whitfield"];
const CAPTIONS = ["Finally finished the thing I have been putting off all week.",
                  "Sunday walk, no plan, no phone for an hour.",
                  "Found this on the way home and had to share it.",
                  "Small win today. Taking it.",
                  "Same view, different light. Never gets old.",
                  "Cleared out the shelf and found a few surprises.",
                  "Quiet morning before everything starts.",
                  "Not sure how I feel about this one. Thoughts?",
                  "Back from the weekend with far too many photos.",
                  "Something I made this week. Be kind."];
const SVG_NS = "http://www.w3.org/2000/svg";

let openCard = null; // only one picker is open at a time

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text; // textContent only, never innerHTML
  return node;
}

function showError(parent, message) {
  parent.replaceChildren(el("p", "error", message));
}

async function loadFeed() {
  const feed = document.getElementById("feed");
  try {
    const response = await fetch("/feed");
    if (!response.ok) throw new Error("status " + response.status);
    const data = await response.json();
    feed.replaceChildren(...data.feed.map((row) => buildCard(row, false)));
  } catch (err) {
    showError(feed, "The feed could not be loaded. Check that the server is running, then reload the page.");
  }
}

function buildPhoto(id) {
  const figure = el("figure", "photo");
  figure.style.setProperty("--h", String((id * 47) % 360)); // hue picked from the id
  figure.setAttribute("role", "img");
  figure.setAttribute("aria-label", "Placeholder image");
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 400 225");
  svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
  svg.setAttribute("aria-hidden", "true");
  const shape = (name, attrs, cls) => {
    const node = document.createElementNS(SVG_NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    node.setAttribute("class", cls);
    svg.append(node);
  };
  shape("rect", { width: 400, height: 225 }, "p0");
  if (id % 2 === 0) { // hills and a sun
    shape("circle", { cx: 290, cy: 70, r: 34 }, "p3");
    shape("polygon", { points: "0,225 0,150 110,90 220,160 320,110 400,170 400,225" }, "p1");
    shape("polygon", { points: "0,225 0,190 140,150 260,200 400,160 400,225" }, "p2");
  } else { // overlapping circles
    shape("circle", { cx: 130, cy: 120, r: 80 }, "p1");
    shape("circle", { cx: 230, cy: 105, r: 62 }, "p2");
    shape("circle", { cx: 300, cy: 150, r: 40 }, "p3");
  }
  figure.append(svg);
  return figure;
}

// switched = true while a signal is switched off: no guess button, and a cue shows the old rank.
function cue(item) {
  if (item.previous_rank > 10) return "new in your top 10";
  return item.previous_rank === item.rank ? "same rank" : `was #${item.previous_rank}`;
}

function buildCard(item, switched) {
  const card = el("article", "card");
  const author = AUTHORS[item.id % AUTHORS.length];
  const initials = author.split(" ").map((w) => w[0]).join("");

  const head = el("div", "post-head");
  const avatar = el("div", "avatar", initials);
  avatar.setAttribute("aria-hidden", "true");
  const who = el("div", "who");
  who.append(el("div", "author", author), el("div", "handle", "@" + author.toLowerCase().replace(" ", "")));
  const rank = el("div", "rank", "#" + item.rank);
  rank.append(el("small", "", switched ? cue(item) : "in your feed"));
  head.append(avatar, who, rank);

  const toggle = el("button", "toggle", "Why am I seeing this?");
  toggle.type = "button";
  toggle.setAttribute("aria-expanded", "false");
  const area = el("div"); // holds the picker and the verdict panel

  toggle.addEventListener("click", () => {
    const opening = toggle.getAttribute("aria-expanded") === "false";
    if (openCard && openCard !== card) closeCard(openCard);
    if (opening) {
      area.replaceChildren(buildPicker(item, area));
      toggle.setAttribute("aria-expanded", "true");
      openCard = card;
    } else {
      closeCard(card);
    }
  });
  card._close = () => { area.replaceChildren(); toggle.setAttribute("aria-expanded", "false"); };

  const actions = el("div", "actions");
  if (!switched) actions.append(toggle);
  card.append(head, el("p", "caption", CAPTIONS[item.id % CAPTIONS.length]),
              buildPhoto(item.id), actions, area);
  return card;
}

function closeCard(card) {
  card._close();
  if (openCard === card) openCard = null;
}

function buildPicker(item, area) {
  const picker = el("div", "picker");
  const panel = el("div");
  panel.setAttribute("role", "status"); // read out when the verdict appears
  picker.append(el("p", "", "I think I am seeing this because of:"));
  const choices = el("div", "choices");
  for (const [value, label] of GUESSES) {
    const button = el("button", "", label);
    button.type = "button";
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => ask(item, value, button, choices, panel));
    choices.append(button);
  }
  picker.append(choices, panel);
  return picker;
}

async function ask(item, guess, button, choices, panel) {
  for (const b of choices.children) b.setAttribute("aria-pressed", String(b === button));
  panel.replaceChildren(el("p", "status", "Testing your theory…"));
  try {
    const response = await fetch("/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: item.id, guess }),
    });
    if (!response.ok) throw new Error("status " + response.status);
    panel.replaceChildren(buildVerdict(await response.json()));
  } catch (err) {
    showError(panel, "That guess could not be tested. Try again, or reload the page.");
  }
}

function buildVerdict(result) {
  const box = el("div", "verdict");
  const heading = el("h3");
  heading.append(el("span", "mark", MARKS[result.verdict]), "Verdict: " + result.verdict);
  box.append(heading);

  if (result.before_rank !== null) {
    const shift = el("p", "shift", `#${result.before_rank} → #${result.after_rank}`);
    shift.append(el("small", "", "rank before and after switching this signal off"));
    box.append(shift);
  }
  box.append(el("p", "", result.message));

  const driver = result.strongest_driver;
  if (driver) {
    box.append(el("p", "driver",
      `Strongest driver: ${NAMES[driver.signal]} (#${driver.rank_before} → #${driver.rank_after})`));
  }
  if (result.guess !== "other") { // "something else" maps to no signal, so there is nothing to switch off
    const sw = el("button", "switch", "Switch this signal off for my feed");
    sw.type = "button";
    sw.addEventListener("click", () => switchOff(result));
    box.append(sw);
  }
  return box;
}

async function switchOff(result) {
  const banner = document.getElementById("banner");
  banner.replaceChildren(el("p", "status", "Re-ranking your feed…"));
  try {
    const response = await fetch("/switch_off", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ signal: result.guess, item_id: result.item_id }),
    });
    if (!response.ok) throw new Error("status " + response.status);
    const data = await response.json();
    openCard = null;
    document.getElementById("feed").replaceChildren(...data.feed.map((row) => buildCard(row, true)));
    banner.replaceChildren(buildBanner(data));
    banner.scrollIntoView({ block: "start" });
  } catch (err) {
    showError(banner, "The feed could not be re-ranked. Try again, or reload the page.");
  }
}

function buildBanner(data) {
  const box = el("section", "banner");
  box.append(el("h2", "", `Feed re-ranked with ${NAMES[data.signal]} switched off`));
  box.append(el("p", "", "Each post shows where it was before. To test another theory, reset first."));
  const reset = el("button", "reset", "Reset");
  reset.type = "button";
  reset.addEventListener("click", () => {
    document.getElementById("banner").replaceChildren();
    openCard = null;
    loadFeed();
  });
  box.append(reset);

  const check = data.consistency;
  if (check) {
    box.append(el("h3", "", "Do your other verdicts for this post change?"));
    const list = el("ul", "consistency");
    for (const row of check.rows) {
      const flag = row.changed ? "changed" : "unchanged";
      list.append(el("li", row.changed ? "changed" : "", `${NAMES[row.signal]}: ${row.before} → ${row.after} (${flag})`));
    }
    box.append(list);
    box.append(el("p", "note", "This only compares the verdicts before and after. It does not show that any verdict is correct."));
  }
  return box;
}

loadFeed();
