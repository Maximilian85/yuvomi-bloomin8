const KEY = 'yuvomi-bloomin8-layout-v1';
const DEFAULTS = { mode: 'dashboard', photoSource: 'yuvomi-immich', photoPlacement: 'right', photoFit: 'cover', photoInterval: 'every-pull', showCalendar: true, showClock: true, showNotes: true, showWeather: false, showTimetable: false, fontScale: 'normal', rotationMinutes: 60 };
const OPTIONS = {
  mode: [['dashboard','Familien-Dashboard'],['photo','Fotomodus'],['alternate','Automatischer Wechsel']],
  photoPlacement: [['right','Rechts'],['bottom','Unten'],['background','Als Hintergrund']],
  photoFit: [['cover','Bildfüllend zuschneiden'],['contain','Vollständig anzeigen']],
  photoInterval: [['every-pull','Bei jedem Bildabruf'],['hourly','Stündlich'],['daily','Täglich']],
  fontScale: [['normal','Normal'],['large','Groß'],['extra-large','Sehr groß']]
};
function load() {
  try { const stored = JSON.parse(localStorage.getItem(KEY) || '{}'); return {...DEFAULTS, ...stored}; }
  catch { return {...DEFAULTS}; }
}
function field(label, key, options, state) {
  const wrapper = document.createElement('label'); wrapper.className = 'bloomin8-setting';
  const span = document.createElement('span'); span.textContent = label;
  const select = document.createElement('select'); select.name = key;
  for (const [value, text] of options) {
    const option = document.createElement('option'); option.value = value; option.textContent = text; select.append(option);
  }
  select.value = state[key]; wrapper.append(span, select); return wrapper;
}
function check(label, key, state) {
  const wrapper = document.createElement('label'); wrapper.className = 'bloomin8-setting bloomin8-setting--check';
  const input = document.createElement('input'); input.type = 'checkbox'; input.name = key; input.checked = Boolean(state[key]);
  wrapper.append(input, document.createTextNode(' ' + label)); return wrapper;
}
export async function render(container, {section}) {
  if (section !== 'household') return;
  const state = load();
  const heading = document.createElement('h3'); heading.textContent = 'Bildschirm und Layout';
  const intro = document.createElement('p'); intro.textContent = 'Konfiguriere den geplanten Dashboard- und Fotomodus. Dies ist eine lokale Vorschau: Die Einstellungen werden vorerst nur in diesem Browser gespeichert und noch nicht an den Docker-Relay übertragen.';
  const form = document.createElement('form'); form.className = 'bloomin8-settings-form';
  form.append(
    field('Anzeigemodus','mode',OPTIONS.mode,state),
    field('Fotoposition im Dashboard','photoPlacement',OPTIONS.photoPlacement,state),
    field('Fotozuschnitt','photoFit',OPTIONS.photoFit,state),
    field('Neues Zufallsbild','photoInterval',OPTIONS.photoInterval,state),
    field('Schriftgröße','fontScale',OPTIONS.fontScale,state),
    check('Kalender anzeigen','showCalendar',state),
    check('Uhrzeit anzeigen','showClock',state),
    check('Familiennotizen anzeigen','showNotes',state),
    check('Wetter anzeigen (noch nicht angebunden)','showWeather',state),
    check('Stundenplan anzeigen (noch nicht angebunden)','showTimetable',state)
  );
  const rotate = document.createElement('label'); rotate.className = 'bloomin8-setting';
  rotate.textContent = 'Wechselintervall in Minuten (Fotomodus/Dashboard)';
  const minutes = document.createElement('input'); minutes.type='number'; minutes.name='rotationMinutes'; minutes.min='5'; minutes.max='1440'; minutes.step='5'; minutes.value=state.rotationMinutes;
  rotate.append(minutes); form.append(rotate);
  const immich = document.createElement('p'); immich.textContent = 'Immich: Es wird die bestehende Yuvomi-Integration verwendet. Hier werden bewusst keine Immich-Zugangsdaten erfasst. Die Verbindung zum Yuvomi-Immich-Endpunkt folgt nach Prüfung der verfügbaren API.';
  const save = document.createElement('button'); save.type='submit'; save.textContent='Vorschau-Einstellungen speichern';
  const status = document.createElement('p'); status.setAttribute('role','status');
  form.append(save,status);
  form.addEventListener('submit', event => {
    event.preventDefault();
    const next = {...DEFAULTS};
    for (const key of Object.keys(DEFAULTS)) {
      const element = form.elements.namedItem(key);
      if (!element) continue;
      if (typeof DEFAULTS[key] === 'boolean') next[key] = element.checked;
      else if (typeof DEFAULTS[key] === 'number') next[key] = Math.min(1440, Math.max(5, Number(element.value) || 60));
      else next[key] = element.value;
    }
    localStorage.setItem(KEY, JSON.stringify(next));
    status.textContent='Lokal gespeichert. Die Modulseite zeigt die Auswahl nach dem nächsten Öffnen; das E-Ink-Gerät bleibt unverändert.';
  });
  container.replaceChildren(heading,intro,form,immich);
}
