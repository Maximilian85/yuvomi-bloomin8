import { mountDesigner } from './designer.js';
export async function render(container,{section}){
  if(section!=='household')return;
  mountDesigner(container);
}
