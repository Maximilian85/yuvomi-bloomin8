import { esc } from '/utils/html.js';

export async function render(container, context) {
  if (context?.signal?.aborted) return;
  container.replaceChildren();
  container.insertAdjacentHTML('beforeend', `
    <div class="page-toolbar">
      <h1 class="page-toolbar__title">BLOOMIN8 E-Ink</h1>
    </div>
    <div class="app-page__body">
      <section class="page-section page-measure">
        <h2>Dein Familien-Dashboard</h2>
        <p>Der BLOOMIN8-Rahmen zeigt eine Tagesansicht mit Informationen aus Yuvomi.</p>
        <div class="bloomin8-info">
          <h3>Stand der Einrichtung</h3>
          <p>Der Bildabruf über den separaten BLOOMIN8-Dienst funktioniert bereits.
          Die sichere Verbindung zur Yuvomi-API für echte Kalender- und Familiendaten
          wird als nächster Entwicklungsschritt ergänzt.</p>
          <p>Aktualisierung: alle 30 Minuten · Nachtpause: 21:00–06:00 Uhr</p>
          <p>Die Verwaltung der Erweiterung findest du unter
          <strong>Einstellungen → Module → BLOOMIN8 E-Ink</strong>.</p>
        </div>
      </section>
    </div>`);
}
