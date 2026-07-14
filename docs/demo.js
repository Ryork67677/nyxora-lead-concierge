const scenarios = {
  booking: {
    visitor: "I am a first-time client. Can I book a consultation next week?",
    assistant:
      "Yes, you can request a consultation next week. Please provide your preferred service, date range, and contact method. A team member will confirm availability and reach out to you.",
    intent: "booking",
    score: "70 / 100",
    action: "book_consultation",
    handoff: "No",
    mode: "ollama",
    sources: ["Consultations", "Appointment requests"],
  },
  pricing: {
    visitor: "How much does a consultation cost?",
    assistant:
      "Pricing depends on the service and individualized plan. The team confirms current pricing during the consultation process; I will not invent an estimate or guarantee a promotion.",
    intent: "pricing",
    score: "50 / 100",
    action: "human_handoff",
    handoff: "Yes",
    mode: "grounded",
    sources: ["Pricing policy", "Consultations"],
  },
  clinical: {
    visitor: "Is this treatment safe while I am pregnant?",
    assistant:
      "That question needs review by a qualified clinician who can consider your medical history. I can help arrange a consultation, but I cannot diagnose conditions or provide medical advice.",
    intent: "safety",
    score: "25 / 100",
    action: "human_handoff",
    handoff: "Yes",
    mode: "policy",
    sources: ["Clinical-review policy"],
  },
  urgent: {
    visitor: "I have severe swelling and difficulty breathing.",
    assistant:
      "Your message may describe an urgent medical issue. This assistant cannot assess emergencies. Call emergency services now, or seek immediate medical care. Do not wait for a reply here.",
    intent: "safety",
    score: "0 / 100",
    action: "emergency_help",
    handoff: "Yes",
    mode: "policy",
    sources: ["Urgent-symptom policy"],
  },
};

const fields = {
  visitor: document.querySelector("#visitor-message"),
  assistant: document.querySelector("#assistant-message"),
  intent: document.querySelector("#intent-value"),
  score: document.querySelector("#score-value"),
  action: document.querySelector("#action-value"),
  handoff: document.querySelector("#handoff-value"),
  mode: document.querySelector("#mode-chip"),
  sources: document.querySelector("#source-list"),
};

function renderScenario(name) {
  const scenario = scenarios[name];
  if (!scenario) return;

  fields.visitor.textContent = scenario.visitor;
  fields.assistant.textContent = scenario.assistant;
  fields.intent.textContent = scenario.intent;
  fields.score.textContent = scenario.score;
  fields.action.textContent = scenario.action;
  fields.handoff.textContent = scenario.handoff;
  fields.mode.textContent = scenario.mode;
  fields.sources.replaceChildren(
    ...scenario.sources.map((source) => {
      const chip = document.createElement("span");
      chip.textContent = source;
      return chip;
    }),
  );

  document.querySelectorAll(".scenario").forEach((button) => {
    button.classList.toggle("active", button.dataset.scenario === name);
  });
}

document.querySelectorAll(".scenario").forEach((button) => {
  button.addEventListener("click", () => renderScenario(button.dataset.scenario));
});

renderScenario("booking");
