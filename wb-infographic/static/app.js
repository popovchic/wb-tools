'use strict';

// ── Состояние ──────────────────────────────────────────────────────────────
let currentTemplate = null;   // JSON шаблона
let resultBlob = null;        // PNG результата

// ── Утилиты ────────────────────────────────────────────────────────────────
function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }
function $(id) { return document.getElementById(id); }

function showOverlay(text) {
  $('overlay-text').textContent = text;
  show($('overlay'));
}
function hideOverlay() { hide($('overlay')); }

function showStep(n) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  $('step' + n).classList.add('active');
}

// ── Дропзоны ───────────────────────────────────────────────────────────────
function initDropzone(dzId, inputId, onFile) {
  const dz = $(dzId);
  const inp = $(inputId);

  dz.addEventListener('click', () => inp.click());
  inp.addEventListener('change', () => {
    if (inp.files[0]) onFile(inp.files[0]);
  });
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('dragover');
    if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]);
  });
}

function previewImage(file, imgId, wrapId) {
  const reader = new FileReader();
  reader.onload = e => {
    $(imgId).src = e.target.result;
    show($(wrapId));
  };
  reader.readAsDataURL(file);
}

// ── Превью шаблона (div-based) ─────────────────────────────────────────────
function renderTemplatePreview(tmpl) {
  const el = $('template-preview');
  el.innerHTML = '';

  const layout = tmpl.layout || {};
  const bg = layout.background_color || '#1a1a1a';
  const grad = layout.background_gradient;

  // Фон
  const bgDiv = document.createElement('div');
  bgDiv.className = 'tp-bg';
  if (grad && grad.from && grad.to) {
    bgDiv.style.background = `linear-gradient(${grad.direction || 'to bottom'}, ${grad.from}, ${grad.to})`;
  } else {
    bgDiv.style.background = bg;
  }
  el.appendChild(bgDiv);

  const W = el.offsetWidth || 300;
  const H = el.offsetHeight || 400;
  const scaleX = W / 900;
  const scaleY = H / 1200;

  // Фото товара
  const img = tmpl.layout?.product_image || {};
  const imgW = (img.width_percent || 50) / 100 * W;
  const imgH = imgW * 1.2;
  const photoDiv = document.createElement('div');
  photoDiv.className = 'tp-photo';
  photoDiv.textContent = 'Фото товара';
  photoDiv.style.width = imgW + 'px';
  photoDiv.style.height = imgH + 'px';

  const pos = img.position || 'center';
  if (pos === 'left') {
    photoDiv.style.left = '0'; photoDiv.style.top = '50%'; photoDiv.style.transform = 'translateY(-50%)';
  } else if (pos === 'right') {
    photoDiv.style.right = '0'; photoDiv.style.top = '50%'; photoDiv.style.transform = 'translateY(-50%)';
  } else if (pos === 'top') {
    photoDiv.style.top = '0'; photoDiv.style.left = '50%'; photoDiv.style.transform = 'translateX(-50%)';
  } else if (pos === 'bottom') {
    photoDiv.style.bottom = '0'; photoDiv.style.left = '50%'; photoDiv.style.transform = 'translateX(-50%)';
  } else {
    photoDiv.style.top = '50%'; photoDiv.style.left = '50%';
    photoDiv.style.transform = 'translate(-50%, -50%)';
  }
  el.appendChild(photoDiv);

  // Заголовок
  const t = tmpl.title || {};
  const titleDiv = document.createElement('div');
  titleDiv.className = 'tp-title';
  titleDiv.textContent = 'Ваш заголовок';
  titleDiv.style.color = t.color || '#fff';
  titleDiv.style.fontSize = Math.round((t.font_size || 32) * scaleY) + 'px';
  titleDiv.style.fontWeight = t.font_weight || 'bold';
  titleDiv.style.width = (t.max_width_percent || 80) + '%';

  const tpos = t.position || 'top-center';
  titleDiv.style.top = Math.round(40 * scaleY) + 'px';
  if (tpos === 'top-left') {
    titleDiv.style.left = Math.round(40 * scaleX) + 'px';
  } else if (tpos === 'top-right') {
    titleDiv.style.right = Math.round(40 * scaleX) + 'px';
    titleDiv.style.textAlign = 'right';
  } else {
    titleDiv.style.left = '50%';
    titleDiv.style.transform = 'translateX(-50%)';
    titleDiv.style.textAlign = 'center';
  }
  el.appendChild(titleDiv);

  // Буллеты
  const bullets = tmpl.bullets || [];
  const bpos = tmpl.bullets_position || 'bottom';
  if (bullets.length) {
    const bulletsDiv = document.createElement('div');
    bulletsDiv.className = 'tp-bullets';

    if (bpos === 'left') {
      bulletsDiv.style.left = Math.round(40 * scaleX) + 'px';
      bulletsDiv.style.top = '50%';
      bulletsDiv.style.transform = 'translateY(-50%)';
      bulletsDiv.style.width = '40%';
    } else if (bpos === 'right') {
      bulletsDiv.style.right = Math.round(40 * scaleX) + 'px';
      bulletsDiv.style.top = '50%';
      bulletsDiv.style.transform = 'translateY(-50%)';
      bulletsDiv.style.width = '40%';
    } else {
      bulletsDiv.style.bottom = Math.round(80 * scaleY) + 'px';
      bulletsDiv.style.left = Math.round(40 * scaleX) + 'px';
      bulletsDiv.style.right = Math.round(40 * scaleX) + 'px';
    }

    bullets.slice(0, 3).forEach((b, i) => {
      const bDiv = document.createElement('div');
      bDiv.className = 'tp-bullet';
      bDiv.style.color = b.color || '#fff';
      bDiv.style.fontSize = Math.round((b.font_size || 18) * scaleY) + 'px';
      bDiv.textContent = (b.icon ? b.icon + ' ' : '') + `Преимущество ${i + 1}`;
      bulletsDiv.appendChild(bDiv);
    });
    el.appendChild(bulletsDiv);
  }

  // Бейдж
  const badge = tmpl.badge;
  if (badge) {
    const badgeDiv = document.createElement('div');
    badgeDiv.className = 'tp-badge';
    badgeDiv.textContent = 'Бейдж';
    badgeDiv.style.background = badge.background_color || '#e53e3e';
    badgeDiv.style.color = badge.text_color || '#fff';
    badgeDiv.style.borderRadius = badge.shape === 'circle' ? '50%' : badge.shape === 'rounded' ? '12px' : '4px';
    if (badge.position === 'top-left') {
      badgeDiv.style.top = '8px'; badgeDiv.style.left = '8px';
    } else {
      badgeDiv.style.top = '8px'; badgeDiv.style.right = '8px';
    }
    el.appendChild(badgeDiv);
  }

  show($('template-preview-wrap'));
}

// ── Шаг 1: Tabs ────────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    $('tab-' + tab.dataset.tab).classList.add('active');
  });
});

// ── Шаг 1: Создать новый ───────────────────────────────────────────────────
let sampleFile = null;

initDropzone('dz-sample', 'input-sample', file => {
  sampleFile = file;
  previewImage(file, 'sample-preview', 'sample-preview-wrap');
  $('btn-create-template').disabled = false;
});

$('btn-create-template').addEventListener('click', async () => {
  if (!sampleFile) return;
  showOverlay('Анализирую образец...');

  const fd = new FormData();
  fd.append('image', sampleFile);
  const instructions = $('instructions-new').value.trim();
  if (instructions) fd.append('instructions', instructions);

  try {
    const resp = await fetch('/api/template/create', { method: 'POST', body: fd });
    if (!resp.ok) throw new Error(await resp.text());
    currentTemplate = await resp.json();
    renderTemplatePreview(currentTemplate);
  } catch (e) {
    alert('Ошибка при создании шаблона: ' + e.message);
  } finally {
    hideOverlay();
  }
});

// ── Шаг 1: Загрузить готовый ───────────────────────────────────────────────
initDropzone('dz-template', 'input-template', file => {
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const tmpl = JSON.parse(e.target.result);
      if (!tmpl.layout || !tmpl.title) throw new Error('Неверный формат шаблона');
      currentTemplate = tmpl;
      renderTemplatePreview(currentTemplate);
      $('btn-modify-template').disabled = false;
    } catch (err) {
      alert('Не удалось загрузить шаблон: ' + err.message);
    }
  };
  reader.readAsText(file);
});

$('btn-modify-template').addEventListener('click', async () => {
  const instructions = $('instructions-modify').value.trim();
  if (!instructions || !currentTemplate) return;
  showOverlay('Применяю правки...');

  const fd = new FormData();
  fd.append('template_json', JSON.stringify(currentTemplate));
  fd.append('instructions', instructions);

  try {
    const resp = await fetch('/api/template/modify', { method: 'POST', body: fd });
    if (!resp.ok) throw new Error(await resp.text());
    currentTemplate = await resp.json();
    renderTemplatePreview(currentTemplate);
  } catch (e) {
    alert('Ошибка при правке шаблона: ' + e.message);
  } finally {
    hideOverlay();
  }
});

// ── Шаг 1: Сохранить шаблон ───────────────────────────────────────────────
$('btn-save-template').addEventListener('click', () => {
  if (!currentTemplate) return;
  const blob = new Blob([JSON.stringify(currentTemplate, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `шаблон-${Date.now()}.template`;
  a.click();
  URL.revokeObjectURL(url);
});

// ── Шаг 1 → Шаг 2 ─────────────────────────────────────────────────────────
$('btn-to-step2').addEventListener('click', () => {
  if (!currentTemplate) return;
  showStep(2);
});

// ── Шаг 2: Фото товара ─────────────────────────────────────────────────────
let productFile = null;

initDropzone('dz-product', 'input-product', file => {
  productFile = file;
  previewImage(file, 'product-preview', 'product-preview-wrap');
  updateCreateBtn();
});

function updateCreateBtn() {
  $('btn-create-infographic').disabled = !productFile;
}

// ── Шаг 2: Буллеты ─────────────────────────────────────────────────────────
let bulletCount = 3;

$('btn-add-bullet').addEventListener('click', () => {
  if (bulletCount >= 6) return;
  bulletCount++;
  const inp = document.createElement('input');
  inp.type = 'text';
  inp.className = 'input bullet-input';
  inp.placeholder = `Преимущество ${bulletCount}`;
  $('bullets-list').appendChild(inp);
  if (bulletCount >= 6) $('btn-add-bullet').style.display = 'none';
});

// ── Шаг 2: Создать инфографику ─────────────────────────────────────────────
$('btn-create-infographic').addEventListener('click', async () => {
  if (!productFile || !currentTemplate) return;

  const removeBg = $('remove-bg').checked;
  hide($('result-wrap'));
  show($('loader'));
  $('loader-text').textContent = removeBg ? 'Убираю фон...' : 'Создаю инфографику...';

  const bullets = Array.from(document.querySelectorAll('.bullet-input'))
    .map(i => i.value.trim())
    .filter(Boolean);

  const fd = new FormData();
  fd.append('template_json', JSON.stringify(currentTemplate));
  fd.append('product_image', productFile);
  fd.append('remove_bg', removeBg ? 'true' : 'false');
  fd.append('title', $('input-title').value.trim());
  bullets.forEach((b, i) => fd.append(`bullet_${i + 1}`, b));
  const badge = $('input-badge').value.trim();
  const footer = $('input-footer').value.trim();
  if (badge) fd.append('badge', badge);
  if (footer) fd.append('footer', footer);

  // Переключить лоадер после 5 сек если remove_bg
  let loaderTimer = null;
  if (removeBg) {
    loaderTimer = setTimeout(() => {
      $('loader-text').textContent = 'Создаю инфографику...';
    }, 6000);
  }

  try {
    const resp = await fetch('/api/infographic/create', { method: 'POST', body: fd });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    const blob = await resp.blob();
    resultBlob = blob;
    const url = URL.createObjectURL(blob);
    $('result-img').src = url;
    show($('result-wrap'));
  } catch (e) {
    alert('Ошибка: ' + e.message);
  } finally {
    clearTimeout(loaderTimer);
    hide($('loader'));
  }
});

// ── Результат: скачать ─────────────────────────────────────────────────────
$('btn-download').addEventListener('click', () => {
  if (!resultBlob) return;
  const url = URL.createObjectURL(resultBlob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `инфографика-${Date.now()}.png`;
  a.click();
  URL.revokeObjectURL(url);
});

// ── Результат: создать ещё ─────────────────────────────────────────────────
$('btn-create-more').addEventListener('click', () => {
  productFile = null;
  resultBlob = null;
  $('input-product').value = '';
  $('product-preview').src = '';
  hide($('product-preview-wrap'));
  hide($('result-wrap'));
  $('input-title').value = '';
  document.querySelectorAll('.bullet-input').forEach(i => i.value = '');
  $('input-badge').value = '';
  $('input-footer').value = '';
  updateCreateBtn();
});

// ── Назад к шаблону ────────────────────────────────────────────────────────
function goToStep1() {
  showStep(1);
  hide($('result-wrap'));
  hide($('loader'));
}
$('btn-back').addEventListener('click', goToStep1);
$('btn-new-template').addEventListener('click', goToStep1);
