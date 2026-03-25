const REMINDERS_KEY = "drama_reminders";

export interface DramaReminder {
  id: number;
  name: string;
  first_air_date: string;
  notified: boolean;
}

export function getReminders(): DramaReminder[] {
  try {
    const saved = localStorage.getItem(REMINDERS_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function saveReminders(reminders: DramaReminder[]) {
  localStorage.setItem(REMINDERS_KEY, JSON.stringify(reminders));
}

export function addReminder(drama: { id: number; name: string; first_air_date: string }) {
  const reminders = getReminders();
  if (reminders.some((r) => r.id === drama.id)) return;
  reminders.push({ id: drama.id, name: drama.name, first_air_date: drama.first_air_date, notified: false });
  saveReminders(reminders);
}

export function removeReminder(dramaId: number) {
  const reminders = getReminders().filter((r) => r.id !== dramaId);
  saveReminders(reminders);
}

export function hasReminder(dramaId: number): boolean {
  return getReminders().some((r) => r.id === dramaId);
}

export async function requestNotificationPermission(): Promise<boolean> {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  if (Notification.permission === "denied") return false;
  const result = await Notification.requestPermission();
  return result === "granted";
}

export function checkAndNotify() {
  if (!("Notification" in window) || Notification.permission !== "granted") return;

  const reminders = getReminders();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let changed = false;

  for (const r of reminders) {
    if (r.notified) continue;
    const airDate = new Date(r.first_air_date + "T00:00:00");
    const diffDays = Math.round((airDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) {
      new Notification("ドラマ放送開始!", {
        body: `「${r.name}」が放送開始しました`,
        icon: "/movie-recommend/icon-192.png",
        tag: `drama-${r.id}`,
      });
      r.notified = true;
      changed = true;
    } else if (diffDays === 1) {
      new Notification("明日放送開始!", {
        body: `「${r.name}」が明日から放送開始です`,
        icon: "/movie-recommend/icon-192.png",
        tag: `drama-remind-${r.id}`,
      });
    }
  }

  if (changed) saveReminders(reminders);
}
