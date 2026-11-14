export function render(container) {
  container.innerHTML = `
    <section class="bloomin8">
      <h2>BLOOMIN8 E-Ink</h2>
      <p>Der Bilderrahmen ruft das Dashboard selbst über WLAN ab.</p>
      <p>Derzeit ist ein Docker-basierter Pull-Verbindungstest implementiert. Kalender, Wetter, Immich und eine serverseitige Einstellungsverwaltung folgen.</p>
      <p>Standard: alle 30 Minuten, Nachtpause 21–6 Uhr.</p>
    </section>`;
}
