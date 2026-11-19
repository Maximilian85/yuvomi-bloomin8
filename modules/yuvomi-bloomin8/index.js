import { mountDesigner } from './designer.js';
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
  container.replaceChildren();
  const header=document.createElement('div');header.className='page-toolbar';
  const title=document.createElement('h1');title.className='page-toolbar__title';title.textContent='BLOOMIN8 E-Ink';
  header.append(title);
  const body=document.createElement('div');body.className='app-page__body';
  const section=document.createElement('section');section.className='page-section page-measure bloomin8';
  body.append(section);container.append(header,body);
  mountDesigner(section,{signal:context?.signal});
}
