import { api } from '/api.js';
import { esc } from '/utils/html.js';

function localDate() {
  const now = new Date();
  const year = now.getFullYear();
  return year + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
}
function eventRow(event) {
  const assigned = Array.isArray(event.assigned_users) ? event.assigned_users : [];
  const first = assigned[0] || {};
  const color = first.avatar_color || event.assigned_color || event.cal_color || '#64748b';
  const safeColor = /^#[0-9a-fA-F]{6}$/.test(color) ? color : '#64748b';
  const start = String(event.start_datetime || '');
  const match = /T(\d{2}:\d{2})/.exec(start);
  const time = event.all_day ? 'Ganztägig' : match ? match[1] : '—';
  const person = first.display_name || first.name || event.assigned_name || '';
  return '<li class="bloomin8-event"><span class="bloomin8-dot" style="background:' + safeColor +
    '"></span><time>' + esc(time) + '</time><span><strong>' + esc(event.title || 'Termin') +
    '</strong>' + (person ? '<small>' + esc(person) + '</small>' : '') + '</span></li>';
}

function layoutSettings() {
  try { return JSON.parse(localStorage.getItem('yuvomi-bloomin8-layout-v1') || '{}'); }
  catch { return {}; }
}
export async function render(container, context) {
  const layout = layoutSettings();
  container.replaceChildren();
  container.insertAdjacentHTML('beforeend', `
    <div class="page-toolbar"><h1 class="page-toolbar__title">BLOOMIN8 E-Ink</h1></div>
    <div class="app-page__body">
      <section class="page-section page-measure bloomin8">
        <h2>Heute auf dem Familienrahmen</h2>
        <div data-bloomin8-layout role="status"></div>
        <p>Diese Termine kommen direkt aus deinem Yuvomi-Kalender. Der E-Ink-Relay-Dienst
           verwendet denselben Kalender über einen eigenen, nur lesenden API-Zugang.</p>
        <div data-bloomin8-events role="status">Termine werden geladen …</div>
        <p class="bloomin8-note">Der Rahmen aktualisiert sein Bild alle 30 Minuten.
           Eine kleine Zeitangabe am Bildrand zeigt den letzten Bildabruf.</p>
        <p>Die Relay-Verbindung wird im Docker-Stack konfiguriert. Unter
           <strong>Einstellungen → Module → BLOOMIN8 E-Ink</strong> findest du die Installationshinweise.</p>
      </section>
    </div>`);
  const preview = container.querySelector('[data-bloomin8-layout]');
  const modeLabels = {dashboard:'Familien-Dashboard',photo:'Immich-Fotomodus',alternate:'Wechsel zwischen Dashboard und Fotomodus'};
  preview.textContent = 'Lokale Layout-Vorschau: ' + (modeLabels[layout.mode] || modeLabels.dashboard) +
    ' · Schriftgröße: ' + (layout.fontScale || 'normal') +
    ' · Foto: ' + (layout.photoPlacement || 'right') +
    '. Die E-Ink-Ausgabe wird noch nicht durch diese Einstellungen gesteuert.';
  const target = container.querySelector('[data-bloomin8-events]');
  const date = localDate();
  try {
    const result = await api.get('/calendar?from=' + date + '&to=' + date);
    if (context?.signal?.aborted) return;
    const events = Array.isArray(result.data) ? result.data : [];
    target.replaceChildren();
    if (events.length) {
      target.insertAdjacentHTML('beforeend', '<ul class="bloomin8-events">' +
        events.slice(0, 20).map(eventRow).join('') + '</ul>');
    } else {
      target.textContent = 'Für heute sind keine Termine vorhanden.';
    }
  } catch (error) {
    if (context?.signal?.aborted) return;
    target.textContent = 'Der Yuvomi-Kalender konnte nicht geladen werden. Prüfe deine Kalenderberechtigung.';
  }
}
