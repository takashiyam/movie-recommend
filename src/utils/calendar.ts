import type { DramaDetail } from "../types/movie";

const DAYS_JP = ["日", "月", "火", "水", "木", "金", "土"];

export function getDayOfWeek(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr + "T00:00:00");
  return `${DAYS_JP[d.getDay()]}曜`;
}

function formatCalendarDate(dateStr: string): string {
  // Format: YYYYMMDD (all-day event)
  return dateStr.replace(/-/g, "");
}

function nextDay(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + 1);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

export function googleCalendarUrl(drama: { name: string; first_air_date: string; overview?: string; networks?: { name: string }[] }): string {
  const start = formatCalendarDate(drama.first_air_date);
  const end = nextDay(drama.first_air_date);
  const network = drama.networks?.map((n) => n.name).join(", ") || "";
  const details = [
    drama.overview ? drama.overview.slice(0, 200) : "",
    network ? `放送局: ${network}` : "",
  ].filter(Boolean).join("\n");

  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: `${drama.name} 放送開始`,
    dates: `${start}/${end}`,
    details,
    ctz: "Asia/Tokyo",
  });
  return `https://calendar.google.com/calendar/render?${params}`;
}

export function generateIcs(drama: { name: string; first_air_date: string; overview?: string; networks?: { name: string }[] }): string {
  const start = formatCalendarDate(drama.first_air_date);
  const end = nextDay(drama.first_air_date);
  const network = drama.networks?.map((n) => n.name).join(", ") || "";
  const desc = [
    drama.overview ? drama.overview.slice(0, 200).replace(/\n/g, "\\n") : "",
    network ? `放送局: ${network}` : "",
  ].filter(Boolean).join("\\n");

  const now = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//DramaGuide//JP//",
    "BEGIN:VEVENT",
    `DTSTART;VALUE=DATE:${start}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${drama.name} 放送開始`,
    desc ? `DESCRIPTION:${desc}` : "",
    `DTSTAMP:${now}`,
    `UID:drama-${start}-${drama.name.replace(/\s/g, "")}@dramaguide`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].filter(Boolean).join("\r\n");
}

export function downloadIcs(drama: Parameters<typeof generateIcs>[0]) {
  const ics = generateIcs(drama);
  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${drama.name}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
