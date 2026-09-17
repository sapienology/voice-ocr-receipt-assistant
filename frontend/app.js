const API_BASE = window.location.port === '3000'
  ? `${window.location.protocol}//${window.location.hostname}:8001`
  : '';

const backendStatus = document.getElementById('backend-status');
const receiptFileInput = document.getElementById('receipt-file');
const audioFileInput = document.getElementById('audio-file');
const questionInput = document.getElementById('question-input');

const receiptResult = document.getElementById('receipt-result');
const answerResult = document.getElementById('answer-result');
const transcriptionResult = document.getElementById('transcription-result');
const receiptFileName = document.getElementById('receipt-file-name');
const audioFileName = document.getElementById('audio-file-name');

function setStatus(message, isError = false) {
  backendStatus.textContent = message;
  backendStatus.style.color = isError ? '#fca5a5' : '#86efac';
  backendStatus.style.borderColor = isError ? 'rgba(239,68,68,0.5)' : 'rgba(34,197,94,0.35)';
  backendStatus.style.background = isError ? 'rgba(127,29,29,0.25)' : 'rgba(15,118,110,0.15)';
}

function showResult(element, text, type = 'success') {
  element.classList.remove('hidden', 'error', 'success');
  element.classList.add(type);
  element.textContent = text;
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  button.textContent = busy ? 'Working...' : label;
}

function renderReceipt(receipt) {
  const items = (receipt.items || []).map((item) =>
    `<li><span>${item.name}</span><strong>${item.price ?? '—'}</strong></li>`
  ).join('');

  return `<div class="receipt-summary">
    <div class="receipt-topline"><strong>${receipt.merchant || 'Receipt scan'}</strong><span>${receipt.date || 'Date unavailable'}</span></div>
    <div class="receipt-metrics">
      <div><small>Subtotal</small><strong>${receipt.subtotal ?? '—'}</strong></div>
      <div><small>Tax</small><strong>${receipt.tax ?? '—'}</strong></div>
      <div class="metric-total"><small>Total</small><strong>${receipt.total ?? '—'}</strong></div>
    </div>
    ${items ? `<ul class="receipt-items">${items}</ul>` : ''}
  </div>`;
}

async function checkBackend() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      throw new Error('Backend health check failed');
    }

    const data = await response.json();
    if (data.status === 'healthy') {
      setStatus('Backend online');
    } else {
      setStatus('Backend responded unexpectedly', true);
    }
  } catch (error) {
    setStatus('Backend offline', true);
  }
}

async function readJsonSafely(response) {
  const text = await response.text();

  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch (error) {
    return { detail: text };
  }
}

async function uploadReceipt() {
  const file = receiptFileInput.files[0];
  if (!file) {
    showResult(receiptResult, 'Please choose a receipt file first.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  const button = document.getElementById('upload-receipt-btn');
  setBusy(button, true, 'Analyze Receipt');
  try {
    const response = await fetch(`${API_BASE}/receipt`, {
      method: 'POST',
      body: formData,
    });

    const data = await readJsonSafely(response);

    if (!response.ok) {
      throw new Error(data.detail || 'Receipt processing failed');
    }

    const receipt = data.receipt || data;
    receiptResult.innerHTML = renderReceipt(receipt);
    receiptResult.classList.remove('hidden', 'error');
    receiptResult.classList.add('success');
  } catch (error) {
    showResult(receiptResult, `Receipt processing failed: ${error.message}`, 'error');
  } finally {
    setBusy(button, false, 'Analyze Receipt');
  }
}

async function askReceiptQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    showResult(answerResult, 'Please enter a question first.', 'error');
    return;
  }

  const button = document.getElementById('ask-btn');
  setBusy(button, true, 'Ask Question');
  try {
    const response = await fetch(`${API_BASE}/ask?question=${encodeURIComponent(question)}` , {
      method: 'POST',
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Question failed');
    }

    const answerText = data.answer || JSON.stringify(data, null, 2);
    showResult(answerResult, `Q: ${question}\n\nA: ${answerText}`, 'success');
  } catch (error) {
    showResult(answerResult, `Error: ${error.message}`, 'error');
  } finally {
    setBusy(button, false, 'Ask Question');
  }
}

async function transcribeAudio() {
  const file = audioFileInput.files[0];
  if (!file) {
    showResult(transcriptionResult, 'Please choose an audio file first.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  const button = document.getElementById('transcribe-btn');
  setBusy(button, true, 'Transcribe Audio');
  try {
    const response = await fetch(`${API_BASE}/transcribe`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Transcription failed');
    }

    const text = data.text || JSON.stringify(data, null, 2);
    showResult(transcriptionResult, text, 'success');
  } catch (error) {
    showResult(transcriptionResult, `Error: ${error.message}`, 'error');
  } finally {
    setBusy(button, false, 'Transcribe Audio');
  }
}

document.getElementById('upload-receipt-btn').addEventListener('click', uploadReceipt);
document.getElementById('ask-btn').addEventListener('click', askReceiptQuestion);
document.getElementById('transcribe-btn').addEventListener('click', transcribeAudio);
receiptFileInput.addEventListener('change', () => {
  receiptFileName.textContent = receiptFileInput.files[0]?.name || 'Drop an image or choose a file';
});
audioFileInput.addEventListener('change', () => {
  audioFileName.textContent = audioFileInput.files[0]?.name || 'Choose an audio recording';
});

checkBackend();
