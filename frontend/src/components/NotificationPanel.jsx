import { useState, useRef, useEffect } from "react";
import { Bell, Briefcase, FileCheck, Video, Clock } from "lucide-react";

const NOTIFS = [
  { id: 1, icon: Briefcase, title: "New Internship", body: "Full Stack Developer Intern — Chennai", time: "2 min ago" },
  { id: 2, icon: FileCheck, title: "Document ready", body: "Renewable_Energy_Overview.pptx finished generating", time: "18 min ago" },
  { id: 3, icon: Clock, title: "Reminder", body: "Review project PPT at 9:00 AM tomorrow", time: "1 hr ago" },
  { id: 4, icon: Video, title: "Video ready", body: "Your product teaser video has finished rendering", time: "3 hr ago" },
];

export default function NotificationPanel() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function onDocClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 rounded-lg hover:bg-bgSoft text-muted hover:text-ink transition-colors"
        aria-label="Notifications"
      >
        <Bell size={19} />
        <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary" />
      </button>

      {open && (
        <div className="absolute right-0 top-11 w-80 rounded-2xl bg-white border border-line shadow-premium overflow-hidden z-30">
          <div className="px-4 py-3 border-b border-line">
            <p className="text-sm font-semibold text-ink">Notifications</p>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {NOTIFS.map(({ id, icon: Icon, title, body, time }) => (
              <div key={id} className="flex gap-3 px-4 py-3 hover:bg-bgSoft/60 border-b border-line last:border-0">
                <div className="w-8 h-8 rounded-lg bg-bgSoft flex items-center justify-center text-primary shrink-0">
                  <Icon size={15} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">{title}</p>
                  <p className="text-xs text-muted truncate">{body}</p>
                  <p className="text-[11px] text-muted mt-0.5">{time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
