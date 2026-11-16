export async function render(container, { section }) {
  if (section !== 'household') return;
  container.replaceChildren();
  const heading = document.createElement('h3');
  heading.textContent = 'BLOOMIN8-Relay einrichten';
  const intro = document.createElement('p');
  intro.textContent = 'Das Modul liest deine Yuvomi-Termine direkt. Für den E-Ink-Rahmen läuft zusätzlich ein Docker-Relay, das dieselben Termine mit einem lesenden Yuvomi-API-Token abruft.';
  const list = document.createElement('ol');
  for (const item of [
    'Unter Einstellungen → Haushalt → API-Zugriff einen Token mit Kalender-Leserechten erstellen.',
    'Im Relay-Docker-Stack YUVOMI_URL (interne Yuvomi-Adresse), YUVOMI_API_TOKEN, EINK_PULL_TOKEN und EINK_PUBLIC_URL setzen.',
    'Relay starten und im Browser http://SYNOLOGY-IP:8088/health prüfen.',
    'Den bereits eingerichteten BLOOMIN8-Pull unverändert auf die Relay-Adresse zeigen lassen.'
  ]) {
    const li = document.createElement('li');
    li.textContent = item;
    list.append(li);
  }
  const note = document.createElement('p');
  note.textContent = 'Wichtig: API- und Geräte-Token niemals hier eingeben oder im Modul speichern. Sie bleiben ausschließlich in der Docker-Umgebung. Wetter, Stundenplan und Fotos folgen in späteren Versionen.';
  container.append(heading, intro, list, note);
}
