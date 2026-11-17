/* Real saved-run adapter for the Stitch visual prototype. No synthetic verdicts are displayed. */
let demoCases = [];
let demoCase = null;
let replaySteps = [];
let replayIndex = 0;
let replayTimer = null;
let caseRequest = 0;
let liveController = null;
let liveAvailable = false;
let livePrecedents = 'bundled_excerpts';

const byId = id => document.getElementById(id);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, ch =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const nice = value => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, x => x.toUpperCase());
const norm = value => String(value || '').toLowerCase().replace(/\s+/g, ' ').trim();
const defectSummary = (defects, contested) => `${defects} potential defect${defects === 1 ? '' : 's'} · ${contested} contested`;

function setText(id, value) { const el = byId(id); if (el) el.textContent = value; }
function findQuoteParagraph(quote) {
  const target = norm(quote);
  if (!target || !demoCase) return null;
  const fragments = target.split(/\.\.\.|…/).map(x => x.trim()).filter(x => x.length > 15);
  const found = demoCase.paragraphs.find(p => {
    const text = norm(p.text);
    return text.includes(target) || (fragments.length && fragments.every(x => text.includes(x)));
  });
  return found ? found.n : null;
}

function showParagraph(n) {
  document.querySelectorAll('#judgment-viewport .para-block').forEach(el =>
    el.classList.remove('ring-2', 'ring-primary', 'bg-surface-container-high'));
  const el = byId(`demo-para-${n}`);
  if (el) {
    el.classList.add('ring-2', 'ring-primary', 'bg-surface-container-high');
    el.scrollIntoView({behavior:'smooth', block:'center'});
  }
}
window.demoShowParagraph = showParagraph;

function renderParagraphs(paragraphs) {
  byId('judgment-viewport').innerHTML = paragraphs.map(p => `<div id="demo-para-${p.n}" class="para-block rounded-lg p-3 mb-2 bg-surface-container/50"><div class="flex gap-3"><span class="text-outline font-code-citation">¶${p.n}</span><p class="text-on-surface leading-relaxed">${escapeHtml(p.text)}</p></div></div>`).join('');
}

function quoteBlock(finding) {
  const quotes = (finding.evidence || []).filter(e => e.source === 'record' && e.quote);
  if (!quotes.length) return '';
  return quotes.map(e => {
    const para = findQuoteParagraph(e.quote);
    const location = para === null ? 'Source paragraph not located' : `Jump to ¶${para}`;
    return `<button type="button" class="block w-full text-left mt-2 p-2 rounded bg-surface-container-highest text-on-surface hover:text-primary" ${para === null ? 'disabled' : `onclick="demoShowParagraph(${para})"`}>
      “${escapeHtml(e.quote)}” <span class="block text-xs text-primary">${location}</span></button>`;
  }).join('');
}

function findingCard(finding, preliminary=false) {
  const status = {defect:'Potential defect', contested:'Contested', cant_tell:'Cannot tell', no_defect:'No defect identified'}[finding.verdict] || finding.verdict;
  const colour = {defect:'text-error', contested:'text-secondary', cant_tell:'text-outline', no_defect:'text-tertiary'}[finding.verdict] || 'text-on-surface';
  const missing = (finding.missing_facts || []).length ? `<p class="mt-2 text-xs text-outline">Missing: ${escapeHtml(finding.missing_facts.join(', '))}</p>` : '';
  return `<article class="check-card rounded-xl border border-surface-container-high p-3 bg-surface-container-low mb-2" data-defect="${escapeHtml(finding.type)}">
    <div class="flex justify-between gap-2"><strong>${escapeHtml(nice(finding.type))}</strong><span class="${colour} font-bold text-xs">${escapeHtml(status)}${preliminary ? ' · provisional' : ''}</span></div>
    <div class="text-xs text-on-surface-variant mt-1">${escapeHtml(finding.provision || 'Section not specified')}</div>
    ${finding.note ? `<p class="mt-2 text-sm">${escapeHtml(finding.note)}</p>` : ''}${missing}
    ${preliminary ? '' : quoteBlock(finding)}
  </article>`;
}

function renderFindings(findings, preliminary=false) {
  const order = {defect:0, contested:1, cant_tell:2, no_defect:3};
  const sorted = [...findings].sort((a,b) => (order[a.verdict] ?? 4) - (order[b.verdict] ?? 4));
  byId('case-checks-container').innerHTML = sorted.map(f => findingCard(f, preliminary)).join('');
}

function renderLiveFactsPanel(facts) {
  let panel = byId('demo-facts-panel');
  if (!panel) {
    panel = document.createElement('details');
    panel.id = 'demo-facts-panel';
    panel.className = 'rounded-xl border border-surface-container-high bg-surface-container-low p-3 mb-3';
    byId('case-checks-container').before(panel);
  }
  panel.classList.remove('hidden');
  const rows = [
    ['Provision', f => f?.provision],
    ['Financial years', f => f?.financial_years],
    ['Notice date', f => f?.notices?.[0]?.date],
    ['Hearing date given', f => f?.notices?.[0]?.hearing_date_given],
    ['Hearing date', f => f?.notices?.[0]?.hearing_date],
    ['Order date', f => f?.order?.date],
  ];
  const value = node => node?.value === null || node?.value === undefined ? 'Unknown' : Array.isArray(node.value) ? node.value.join(', ') : String(node.value);
  const body = rows.map(([label, get]) => {
    const node = get(facts);
    const para = node?.quote ? findQuoteParagraph(node.quote) : null;
    const quote = node?.quote ? (para === null
      ? escapeHtml(node.quote.slice(0, 130))
      : `<button type="button" class="text-left text-primary hover:underline" onclick="demoShowParagraph(${para})">${escapeHtml(node.quote.slice(0, 130))} · ¶${para}</button>`)
      : 'No quote supplied';
    return `<tr class="border-b border-surface-container-high"><td class="p-2">${escapeHtml(label)}</td><td class="p-2">${escapeHtml(value(node))}</td><td class="p-2 text-xs text-outline">${quote}</td></tr>`;
  }).join('');
  panel.innerHTML = `<summary class="cursor-pointer font-semibold">Inspect Gemini-extracted facts</summary>
    <p class="text-xs text-outline my-2">Live preview only. Quotes were checked for literal presence in the pasted judgment; a match does not establish the legal conclusion.</p>
    <div class="overflow-x-auto"><table class="min-w-[480px] w-full text-left text-xs"><thead><tr class="border-b border-surface-container-high"><th class="p-2">Fact</th><th class="p-2">Gemini value</th><th class="p-2">Source quote</th></tr></thead><tbody>${body}</tbody></table></div>`;
}

function renderCheckerComparison() {
  const control = byId('rq1-btn-nc')?.closest('.bg-surface-container-low');
  if (!control) return;
  control.classList.toggle('hidden', !demoCase.comparison);
  const plainPanel = byId('rq1-plain-panel');
  plainPanel.classList.add('hidden');
  if (!demoCase.comparison) {
    byId('case-checks-container').classList.remove('hidden');
    return;
  }
  const shared = demoCase.comparison.input.record;
  const plain = demoCase.comparison.plain.findings || [];
  control.innerHTML = `<div><strong class="text-sm">Compare the checker approaches</strong><p class="text-xs text-on-surface-variant mt-1">Both receive the same human-checked facts. The difference shown here comes from planning, tools, statutory checks and verification.</p><p class="text-xs text-outline mt-1">Provision: ${escapeHtml(shared.provision?.value || 'unknown')} · Financial years: ${escapeHtml((shared.financial_years?.value || []).join(', ') || 'unknown')}</p></div><div class="inline-flex flex-wrap p-0.5 bg-surface-container rounded-lg border border-surface-container-high/60"><button id="rq1-btn-nc" onclick="toggleRQ1View('nc')" type="button" class="px-2 py-1 rounded text-xs">NoticeCheck pipeline</button><button id="rq1-btn-plain" onclick="toggleRQ1View('plain')" type="button" class="px-2 py-1 rounded text-xs">Plain Qwen3-8B</button><button id="rq1-btn-side" onclick="toggleRQ1View('side')" type="button" class="px-2 py-1 rounded text-xs">Compare both</button></div>`;
  plainPanel.innerHTML = `<h4 class="font-semibold text-secondary">Plain Qwen3-8B · same fact record, no NoticeCheck tools</h4>${plain.map(f => findingCard(f)).join('')}`;
  toggleRQ1View = mode => {
    const panel = byId('rq1-plain-panel');
    const checks = byId('case-checks-container');
    panel.classList.toggle('hidden', mode === 'nc');
    checks.classList.toggle('hidden', mode === 'plain');
    if (mode !== 'plain') renderFindings(demoCase.main.findings);
    const tally = findings => ({defects: findings.filter(f => f.verdict === 'defect').length,
                                contested: findings.filter(f => f.verdict === 'contested').length});
    const nc = tally(demoCase.main.findings);
    const baseline = tally(plain);
    setText('summary-defect-badge', mode === 'side'
      ? `NoticeCheck: ${defectSummary(nc.defects, nc.contested)} · Plain Qwen: ${defectSummary(baseline.defects, baseline.contested)}`
      : defectSummary(mode === 'plain' ? baseline.defects : nc.defects, mode === 'plain' ? baseline.contested : nc.contested));
    setText('summary-text', mode === 'plain'
      ? 'Plain Qwen3-8B assessed the same human-checked facts without NoticeCheck tools. Compare its saved findings with the pipeline output.'
      : 'The same human-checked facts were given to both checkers. The replay below follows NoticeCheck’s saved planning, tools, checks and verification.');
    for (const key of ['nc','plain','side']) {
      const button = byId(`rq1-btn-${key}`);
      button?.classList.toggle('bg-primary-container', key === mode);
      button?.classList.toggle('text-on-primary-container', key === mode);
      button?.classList.toggle('text-on-surface-variant', key !== mode);
    }
  };
  toggleRQ1View('nc');
}

function showCase(detail) {
  demoCase = detail;
  renderParagraphs(detail.paragraphs);
  const headerBadge = document.querySelector('header .uppercase span:last-child');
  if (headerBadge) headerBadge.textContent = 'Real saved Qwen runs';
  const replayControl = byId('demo-replay-control');
  replayControl.querySelector('strong').textContent = 'Recorded Qwen run · step by step';
  replayControl.querySelectorAll('button').forEach(button => button.classList.remove('hidden'));
  byId('demo-facts-panel')?.classList.add('hidden');
  const sourceHeader = byId('judgment-panel-title')?.parentElement?.parentElement;
  if (sourceHeader) {
    const linkHost = sourceHeader.lastElementChild;
    linkHost.replaceChildren();
    const link = document.createElement('a');
    link.href = detail.source_pdf_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'text-primary hover:underline';
    link.textContent = 'Open source PDF ↗';
    linkHost.append(link);
  }
  if (!byId('demo-quote-note')) {
    const note = document.createElement('p');
    note.id = 'demo-quote-note';
    note.className = 'text-xs text-outline';
    note.textContent = 'A quote match confirms literal words in the judgment. It does not alone prove the fact belongs to the correct proceeding or that the legal conclusion is right.';
    sourceHeader?.after(note);
  }
  setText('analysis-case-title', detail.title);
  setText('summary-defect-badge', defectSummary(detail.counts.defect, detail.counts.contested));
  setText('summary-court', `${detail.court} · ${detail.decision_date}`);
  setText('summary-period', `${detail.input_label} · ${detail.id}`);
  setText('summary-input-label', detail.comparison ? 'Same facts as Plain Qwen' : 'Fine-tuned extractor output');
  setText('confidence-text', 'Saved model output · verify against the judgment');
  const ready = byId('confidence-text')?.nextElementSibling;
  if (ready) ready.querySelector('span:last-child').textContent = 'For human review';
  const summary = byId('summary-text');
  if (summary) summary.textContent = 'This is the exact saved NoticeCheck output for this judgment. Select a finding to inspect its source.';
  setText('recommendation-text', detail.main.handoff?.escalate ? `Human review recommended: ${(detail.main.handoff.reasons || []).map(nice).join(', ') || 'see case details'}.` : 'The saved run did not trigger a hand-off. Review findings and source before drawing conclusions.');
  renderCheckerComparison();
  renderFindings(detail.main.findings);
  replaySteps = detail.trace || [];
  replayIndex = 0;
  byId('demo-replay-log')?.replaceChildren();
  setText('demo-replay-status', 'Press Analyse Case to replay the saved trace');
  const tracePanel = byId('model-trace-panel');
  if (tracePanel) tracePanel.innerHTML = '<strong>Saved execution trace</strong><p>Use Play in the review pane to follow every recorded step.</p>';
  const accordion = document.querySelector('#case-checks-container + details');
  if (accordion) {
    accordion.classList.remove('hidden');
    accordion.innerHTML = `<summary class="cursor-pointer font-semibold">Full saved execution trace (${detail.trace.length} steps)</summary><div class="mt-3 max-h-72 overflow-y-auto text-xs">${detail.trace.map(step => `<p class="border-b border-surface-container-high py-1">${escapeHtml(step.step)}. ${escapeHtml(stepLabel(step))}</p>`).join('')}</div>`;
  }
}

async function selectDemoCase(letter) {
  liveController?.abort();
  liveController = null;
  stopReplay();
  const request = ++caseRequest;
  const selected = demoCases[['A','B','C'].indexOf(letter)];
  if (!selected) return;
  const response = await fetch(`/api/cases/${selected.id}`);
  if (!response.ok) throw new Error((await response.json()).error);
  const detail = await response.json();
  if (request !== caseRequest) return;
  showCase(detail);
  document.querySelectorAll('.case-card').forEach(el => el.classList.toggle('ring-2', el.dataset.case === letter));
  ['A','B','C'].forEach((key,i) => setText(`case-pill-${key}`, `${key}: ${demoCases[i]?.court || ''}`));
}
window.demoSelect = letter => selectDemoCase(letter).catch(err => alert(err.message));

function stepLabel(step) {
  if (step.tool) return `${step.stage}: ${step.tool}(${JSON.stringify(step.args || {})}) → ${step.ok ? 'ok' : 'error'}${step.output_summary ? ` · ${step.output_summary}` : ''}`;
  if (step.defect) return `${step.stage}: ${nice(step.defect)} → ${nice(step.output_summary || 'checked')}`;
  if (step.stage === 'handoff') return `Hand-off: ${step.output_summary || 'completed'}`;
  if (step.stage === 'verify') return `Verifier: ${step.output_summary || 'checked evidence'}`;
  return `${nice(step.stage)}: ${step.model ? `model response (${step.model})` : 'completed'}`;
}

function stopReplay() {
  if (replayTimer) clearInterval(replayTimer);
  replayTimer = null;
}
function replayNext() {
  if (replayIndex >= replaySteps.length) {
    stopReplay();
    renderFindings(demoCase.main.findings);
    setText('demo-replay-status', 'Replay complete · final saved checklist shown');
    return;
  }
  const step = replaySteps[replayIndex++];
  const item = document.createElement('div');
  item.className = 'p-2 rounded bg-surface-container mb-1 text-xs text-on-surface-variant';
  item.textContent = `${step.step || replayIndex}. ${stepLabel(step)}`;
  byId('demo-replay-log').append(item);
  item.scrollIntoView({block:'nearest'});
  setText('demo-replay-status', `Step ${replayIndex} of ${replaySteps.length}`);
  if (step.defect && step.stage === 'precondition_check') {
    const found = demoCase.main.findings.find(f => f.type === step.defect);
    if (found) {
      const provisional = {...found, verdict: ['defect','contested','cant_tell','no_defect'].includes(step.output_summary) ? step.output_summary : found.verdict};
      const host = byId('case-checks-container');
      host.insertAdjacentHTML('beforeend', findingCard(provisional, true));
      const quote = (found.evidence || []).find(e => e.source === 'record' && e.quote)?.quote;
      const para = findQuoteParagraph(quote);
      if (para !== null) showParagraph(para);
    }
  }
}
window.demoPlay = () => {
  if (!demoCase) return;
  if (replayIndex >= replaySteps.length) { replayIndex = 0; byId('demo-replay-log').replaceChildren(); byId('case-checks-container').replaceChildren(); }
  stopReplay();
  replayTimer = setInterval(replayNext, 650);
};
window.demoPause = stopReplay;
window.demoNext = () => {stopReplay(); replayNext();};
window.demoStart = () => {
  if (!demoCase) return;
  if (demoCase.comparison) toggleRQ1View('nc');
  replaySteps = demoCase.trace || [];
  replayIndex = 0;
  byId('demo-replay-log').replaceChildren();
  byId('case-checks-container').replaceChildren();
  switchView('state-results');
  demoPlay();
};

function appendLiveLog(label, detail) {
  const item = document.createElement('details');
  item.className = 'p-2 rounded bg-surface-container mb-1 text-xs text-on-surface-variant';
  const summary = document.createElement('summary');
  summary.className = 'cursor-pointer';
  summary.textContent = label;
  item.append(summary);
  if (detail && Object.keys(detail).length) {
    const pre = document.createElement('pre');
    pre.className = 'mt-2 whitespace-pre-wrap break-words text-on-surface';
    pre.textContent = JSON.stringify(detail, null, 2);
    item.append(pre);
  }
  byId('demo-replay-log').append(item);
  item.scrollIntoView({block:'nearest'});
}

function showLiveEvent(event) {
  if (event.type === 'input') {
    demoCase.paragraphs = event.paragraphs;
    renderParagraphs(event.paragraphs);
    setText('demo-replay-status', `${event.paragraphs.length} source paragraph(s) loaded`);
  } else if (event.type === 'stage') {
    setText('demo-replay-status', event.message);
    appendLiveLog(event.message);
  } else if (event.type === 'extraction') {
    renderLiveFactsPanel(event.facts);
    appendLiveLog(`Gemini extraction complete · ${event.grounding.quotes_located} quotes located`,
                  {grounding: event.grounding, model: event.model});
  } else if (event.type === 'step') {
    const step = event.step;
    const detail = {};
    for (const key of ['by','args','output','response','finding','error']) {
      if (step[key] !== undefined && step[key] !== null) detail[key] = step[key];
    }
    appendLiveLog(`${step.step}. ${stepLabel(step)}`, detail);
    setText('demo-replay-status', `Live NoticeCheck · ${step.stage} · step ${step.step}`);
    if (step.stage === 'precondition_check' && step.finding) {
      byId('case-checks-container').insertAdjacentHTML('beforeend', findingCard(step.finding, true));
      const quote = (step.finding.evidence || []).find(e => e.source === 'record' && e.quote)?.quote;
      const para = findQuoteParagraph(quote);
      if (para !== null) showParagraph(para);
    }
  } else if (event.type === 'result') {
    demoCase.main = event.result;
    renderFindings(event.result.findings);
    const counts = {defect: 0, contested: 0};
    for (const finding of event.result.findings) if (finding.verdict in counts) counts[finding.verdict]++;
    setText('summary-defect-badge', defectSummary(counts.defect, counts.contested));
    setText('recommendation-text', event.result.handoff?.escalate
      ? `Human review recommended: ${(event.result.handoff.reasons || []).map(nice).join(', ')}.`
      : 'No automatic hand-off was triggered. Review the findings and source before drawing conclusions.');
    setText('demo-replay-status', 'Live Gemini run complete · final NoticeCheck checklist shown');
    appendLiveLog('Final checklist and hand-off received');
  } else if (event.type === 'error') {
    setText('demo-replay-status', `Live run stopped: ${event.message}`);
    appendLiveLog(`Live run stopped: ${event.message}`);
  }
}

window.demoRunLive = async () => {
  const text = byId('custom-case-input')?.value.trim() || '';
  if (text.length < 80 || text.length > 30000) {
    alert('Paste 80 to 30,000 characters from a High Court GST judgment.');
    return;
  }
  if (!liveAvailable) {
    alert('Set GEMINI_API_KEY and GEMINI_MODEL in the repository .env, then restart this server.');
    return;
  }
  liveController?.abort();
  stopReplay();
  const controller = new AbortController();
  liveController = controller;
  demoCase = {mode: 'live_gemini', paragraphs: [], main: {findings: []}, comparison: null};
  renderParagraphs([]);
  byId('judgment-panel-title').parentElement.nextElementSibling.textContent = 'Pasted judgment text';
  byId('demo-facts-panel')?.classList.add('hidden');
  byId('rq1-btn-nc')?.closest('.bg-surface-container-low')?.classList.add('hidden');
  byId('case-checks-container').classList.remove('hidden');
  byId('case-checks-container').replaceChildren();
  byId('demo-replay-log').replaceChildren();
  const replayControl = byId('demo-replay-control');
  replayControl.querySelector('strong').textContent = 'Live Gemini pipeline · events as they occur';
  replayControl.querySelectorAll('button').forEach(button => button.classList.add('hidden'));
  const accordion = document.querySelector('#case-checks-container + details');
  accordion?.classList.add('hidden');
  const headerBadge = document.querySelector('header .uppercase span:last-child');
  if (headerBadge) headerBadge.textContent = 'Live preview · Gemini replaces Qwen';
  setText('analysis-case-title', 'Pasted judgment · live Gemini preview');
  setText('summary-defect-badge', 'Analysis in progress');
  setText('summary-court', 'Pasted High Court judgment');
  setText('summary-period', 'Gemini extraction → NoticeCheck with Gemini');
  setText('summary-input-label', 'Gemini-extracted facts (live)');
  setText('summary-text', `A new analysis is running. Findings appear provisionally as checks finish; the final checklist follows verification.${livePrecedents === 'bundled_excerpts' ? ' Case-law search uses a small bundled excerpt index in this preview.' : ''}`);
  setText('recommendation-text', 'Human review recommendation appears when the run finishes.');
  setText('confidence-text', 'Live Gemini output · verify against the judgment');
  setText('demo-replay-status', 'Connecting to the live pipeline…');
  const tracePanel = byId('model-trace-panel');
  if (tracePanel) tracePanel.innerHTML = '<strong>Live execution events</strong><p>The panel below shows structured model decisions and tool results, not private model thoughts.</p>';
  switchView('state-results');
  let completed = false;
  let failed = false;
  try {
    const response = await fetch('/api/live', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text}), signal: controller.signal});
    if (!response.ok) {
      const problem = await response.json();
      throw new Error(problem.error || `HTTP ${response.status}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) if (line.trim()) {
        const event = JSON.parse(line);
        if (controller !== liveController) return;
        showLiveEvent(event);
        if (event.type === 'result') completed = true;
        if (event.type === 'error') failed = true;
      }
    }
    if (buffer.trim()) {
      const event = JSON.parse(buffer);
      if (controller === liveController) showLiveEvent(event);
      if (event.type === 'result') completed = true;
      if (event.type === 'error') failed = true;
    }
    if (!completed && !failed && controller === liveController) throw new Error('The stream ended without a final checklist.');
  } catch (err) {
    if (err.name !== 'AbortError' && controller === liveController) showLiveEvent({type: 'error', message: err.message});
  } finally {
    if (controller === liveController) liveController = null;
  }
};

async function initDemo() {
  const response = await fetch('/api/cases');
  if (!response.ok) throw new Error('Saved cases could not be loaded');
  demoCases = await response.json();
  const health = await (await fetch('/api/health')).json();
  liveAvailable = Boolean(health.live_available);
  livePrecedents = health.live_precedents;
  const startHeading = document.querySelector('#state-start h2');
  if (startHeading) startHeading.textContent = 'Explore a real saved NoticeCheck analysis';
  const firstStep = byId('step-nav-1');
  if (firstStep) firstStep.querySelector('span:last-child').textContent = 'Choose judgment';
  byId('step-nav-2')?.remove();
  const reviewStep = byId('step-nav-3');
  if (reviewStep) {
    reviewStep.querySelector('span:first-child').textContent = '2';
    reviewStep.querySelector('span:last-child').textContent = 'Replay & review';
  }
  byId('state-analysis')?.remove();
  const headerBadge = document.querySelector('header .uppercase span:last-child');
  if (headerBadge) headerBadge.textContent = 'Real saved Qwen runs';
  setText('trace-toggle-label', 'Inspect execution trace');
  const caseHeading = byId('case-selection-group')?.previousElementSibling;
  if (caseHeading) caseHeading.querySelectorAll('h3,p,span').forEach(el => {
    if (el.tagName === 'H3') el.textContent = 'Select a judgment from the saved runs';
    else if (el.tagName === 'P') el.textContent = 'Actual saved Qwen outputs. Choose Case C to compare the checker with Plain Qwen on identical facts.';
    else if (el.textContent.includes('Illustrative Example')) el.textContent = 'Real saved Qwen outputs';
  });
  const research = byId('research-modal');
  if (research) {
    const heading = [...research.querySelectorAll('h4')].find(el => el.textContent.includes('Research Overview'));
    if (heading) heading.textContent = 'Project overview & checker comparison';
    for (const label of research.querySelectorAll('span')) {
      if (label.textContent.includes('RQ2: Fact Extraction Precision')) label.parentElement.remove();
      else if (label.textContent.includes('RQ1: Checker Pipeline Comparison')) {
        label.textContent = 'Plain Qwen vs. NoticeCheck';
        const note = label.parentElement.querySelector('p');
        if (note) note.textContent = 'The two saved checkers receive the same human-checked fact record. The comparison shows what NoticeCheck’s planning, tools, statutory checks and verification add. Its measured F1 gain did not conclusively meet the planned threshold.';
        label.parentElement.parentElement.classList.remove('md:grid-cols-2');
      }
    }
  }
  setText('nav-about-btn', 'About NoticeCheck');
  const aboutButton = byId('open-research-modal');
  if (aboutButton) aboutButton.querySelector('span:last-child').textContent = 'About the pipeline';
  const footer = document.querySelector('footer');
  if (footer) footer.querySelectorAll('span').forEach(span => {if (span.textContent.includes('GSTN Spec v3.4')) span.textContent = 'Saved Qwen run';});
  document.querySelectorAll('.case-card').forEach((card,i) => {
    const item = demoCases[i];
    if (!item) {card.classList.add('hidden'); return;}
    card.setAttribute('onclick', `demoSelect('${'ABC'[i]}')`);
    card.querySelector('h4')?.replaceChildren(document.createTextNode(item.title));
    const smaller = card.querySelector('.font-code-citation');
    if (smaller) smaller.textContent = `${item.court} · ${item.decision_date}`;
    const blurb = card.querySelector('p');
    if (blurb) blurb.textContent = `${item.description} · ${defectSummary(item.counts.defect, item.counts.contested)}`;
    const foot = card.querySelector('.border-t');
    if (foot) foot.innerHTML = `<span>${escapeHtml(item.id)}</span><span>${escapeHtml(item.run)}</span>`;
  });
  byId('btn-start-analysis').setAttribute('onclick','demoStart()');
  ['A','B','C'].forEach(key => byId(`case-pill-${key}`)?.setAttribute('onclick', `demoSelect('${key}')`));
  document.querySelectorAll('[onclick="switchView(\'state-analysis\')"], [onclick="switchView(\'state-results\')"]').forEach(el => el.setAttribute('onclick','demoStart()'));
  const paste = document.querySelector('#state-start details');
  if (paste) {
    paste.querySelector('summary').textContent = 'Paste a High Court judgment · live Gemini preview';
    paste.querySelector('p').textContent = 'Paste judgment text with the relevant numbered paragraphs. Gemini replaces Qwen for both fact extraction and NoticeCheck in this live preview.';
    const button = paste.querySelector('button[onclick="loadCustomCase()"]');
    button?.setAttribute('onclick', 'demoRunLive()');
    if (button) button.textContent = 'Run live with Gemini';
    const status = document.createElement('p');
    status.className = 'text-xs text-outline';
    status.textContent = liveAvailable ? 'Gemini is configured on this server.' : 'To enable live mode, set GEMINI_API_KEY and GEMINI_MODEL in .env, then restart the server. Saved Qwen replay works now.';
    paste.querySelector('textarea')?.after(status);
  }
  const control = document.createElement('div');
  control.id = 'demo-replay-control';
  control.className = 'bg-surface-container-low rounded-xl p-3 mb-3 border border-surface-container-high';
  control.innerHTML = `<div class="flex flex-wrap items-center gap-2"><strong class="mr-auto">Recorded Qwen run · step by step</strong><button onclick="demoPlay()" class="px-3 py-1 rounded bg-primary-container">Play</button><button onclick="demoPause()" class="px-3 py-1 rounded bg-surface-container-high">Pause</button><button onclick="demoNext()" class="px-3 py-1 rounded bg-surface-container-high">Next step</button></div><p id="demo-replay-status" class="text-xs text-outline my-2">Press Analyse Case to replay the saved trace</p><div id="demo-replay-log" class="max-h-40 overflow-y-auto font-code-trace"></div>`;
  byId('case-checks-container').before(control);
  await selectDemoCase('A');
  document.documentElement.classList.add('demo-ready');
}
document.addEventListener('DOMContentLoaded', () => initDemo().catch(err => {
  const message = document.createElement('p');
  message.className = 'm-6 p-4 rounded-xl bg-error-container text-on-error-container';
  message.textContent = `The saved demo could not load: ${err.message}`;
  document.body.prepend(message);
}));
