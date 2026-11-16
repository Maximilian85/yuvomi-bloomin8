export async function render(container, { section }) {
  if (section !== 'household') return;
  container.replaceChildren();
  const heading = document.createElement('h3');
  heading.textContent = 'BLOOMIN8 – Haushaltskonfiguration';
  const info = document.createElement('p');
  info.textContent = 'Derzeit: 30 Minuten Aktualisierung, Nachtpause 21:00–06:00 Uhr (Europe/Berlin).';
  const detail = document.createElement('p');
  detail.textContent = 'Die Geräteverbindung wird momentan im BLOOMIN8-Dienst konfiguriert. Eine sichere Speicherung und Änderung direkt hier folgt mit der Yuvomi-API-Anbindung.';
  container.append(heading, info, detail);
}
