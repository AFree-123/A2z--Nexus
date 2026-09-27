import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function SplashPage() {
  const navigate = useNavigate();
  const moved = useRef(false);
  const audioRef = useRef(null);

  const goToAuth = () => {
    if (moved.current) return;

    moved.current = true;
    navigate("/auth", { replace: true });
  };

  useEffect(() => {
    const audio = audioRef.current;
    const startAudio = () => {
      audio?.play().catch(() => {});
    };
    startAudio();
    window.addEventListener("pointerdown", startAudio, { once: true });

    const fallback = window.setTimeout(() => {
      goToAuth();
    }, 10000);

    return () => {
      window.clearTimeout(fallback);
      window.removeEventListener("pointerdown", startAudio);
      audio?.pause();
    };
  }, []);

  return (
    <main className="fixed inset-0 w-screen h-screen overflow-hidden bg-black">
      <audio
        ref={audioRef}
        src="/assets/a2z-background.mp3"
        autoPlay
        loop
        preload="auto"
      />
      <video
        src="/assets/a2z-intro.mp4"
        autoPlay
        muted
        playsInline
        preload="auto"
        className="absolute inset-0 w-full h-full object-cover"
        onEnded={goToAuth}
      />
    </main>
  );
}
