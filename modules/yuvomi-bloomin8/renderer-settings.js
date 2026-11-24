// Only fields supported by the relay. Never expose the relay admin token.
export function rendererSettings(state){
 const integer=(value,min,max,fallback)=>Number.isFinite(Number(value))?Math.max(min,Math.min(max,Math.round(Number(value)))):fallback;
 return {showCalendar:!!state.showCalendar,showClock:!!state.showClock,showAllDay:!!state.showAllDay,calendarLimit:integer(state.calendarLimit,1,5,5),calendarFontScale:['compact','normal','large'].includes(state.calendarFontScale)?state.calendarFontScale:'normal',imageQuality:integer(state.imageQuality,50,95,90)};
}
