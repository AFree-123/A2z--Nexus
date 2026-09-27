import { useEffect, useState } from "react";
import {
  Brain,
  Search,
  Image as ImageIcon,
  Code2,
  FileText,
  Sparkles,
} from "lucide-react";

const STATUS_STEPS = {
  thinking: {
    icon: Brain,
    text: "Thinking...",
  },
  analysing: {
    icon: Sparkles,
    text: "Analysing your request...",
  },
  searching: {
    icon: Search,
    text: "Searching the web...",
  },
  image: {
    icon: ImageIcon,
    text: "Generating image...",
  },
  code: {
    icon: Code2,
    text: "Writing code...",
  },
  document: {
    icon: FileText,
    text: "Creating document...",
  },
  preparing: {
    icon: Sparkles,
    text: "Preparing response...",
  },
};

export default function LoadingState({
  type = "thinking",
}) {
  const [step, setStep] = useState("thinking");

  useEffect(() => {
    setStep("thinking");

    const timer1 = setTimeout(() => {
      setStep("analysing");
    }, 700);

    const timer2 = setTimeout(() => {
      setStep(
        type === "thinking"
          ? "preparing"
          : type
      );
    }, 1600);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [type]);

  const current =
    STATUS_STEPS[step] || STATUS_STEPS.thinking;

  const Icon = current.icon;

  return (
    <div className="flex gap-3 px-4 md:px-0">

      {/* Small AI status icon — NO BIG LOGO */}
      <div
        className="
          w-8 h-8
          rounded-lg
          bg-primary/10
          text-primary
          flex items-center justify-center
          shrink-0
        "
      >
        <Icon
          size={17}
          className="animate-pulse"
        />
      </div>

      {/* Status message */}
      <div
        className="
          rounded-2xl
          rounded-tl-md
          bg-[#ffffff]
          border border-line
          px-4 py-3
          shadow-sm
          min-w-[220px]
        "
      >
        <div className="flex items-center gap-3">

          <div className="flex-1">
            <p className="text-sm font-medium text-ink">
              {current.text}
            </p>

            <div className="flex items-center gap-1 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.2s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.1s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}