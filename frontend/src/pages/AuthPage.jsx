import { useMemo, useState } from "react";
import {
  Eye,
  EyeOff,
  LogIn,
  UserPlus,
  Sparkles,
  MessageCircle,
  FileText,
  Mic,
  Briefcase,
  ArrowRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import A2ZNexusLogo from "../components/A2ZNexusLogo";

const STORAGE_KEY = "a2z-nexus-user";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000";

export default function AuthPage() {
  const navigate = useNavigate();

  const [mode, setMode] = useState("login");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const title = useMemo(
    () =>
      mode === "login"
        ? "Welcome back"
        : "Create your A2Z account",
    [mode]
  );

  const update = (key) => (e) => {
    setError("");

    setForm((v) => ({
      ...v,
      [key]: e.target.value,
    }));
  };

  function submit(e) {
    e.preventDefault();

    const email = form.email.trim().toLowerCase();
    const password = form.password;

    /* ================= VALIDATION ================= */

    if (
      !email ||
      !password ||
      (mode === "register" &&
        (!form.name.trim() || !form.confirmPassword))
    ) {
      setError("Please fill in all required fields.");
      return;
    }

    /* ================= CONFIRM PASSWORD ================= */

    if (
      mode === "register" &&
      password !== form.confirmPassword
    ) {
      setError("Passwords do not match.");
      return;
    }

    /* ================= REGISTER ================= */

    if (mode === "register") {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          name: form.name.trim(),
          email,
          password,
        })
      );

      localStorage.setItem(
        "a2z-nexus-session",
        JSON.stringify({
          name: form.name.trim(),
          email,
          guest: false,
        })
      );

      navigate("/chat", { replace: true });
      return;
    }

    /* ================= LOGIN ================= */

    const saved = JSON.parse(
      localStorage.getItem(STORAGE_KEY) || "null"
    );

    if (!saved) {
      setError("No account found. Please register first.");
      return;
    }

    if (
      saved.email !== email ||
      saved.password !== password
    ) {
      setError("Email or password is incorrect.");
      return;
    }

    localStorage.setItem(
      "a2z-nexus-session",
      JSON.stringify({
        name: saved.name,
        email: saved.email,
        guest: false,
      })
    );

    navigate("/chat", { replace: true });
  }

  /* ================= GOOGLE ================= */

  function continueWithGoogle() {
    window.location.href = `${API_URL}/api/auth/google`;
  }

  /* ================= MICROSOFT ================= */

  function continueWithMicrosoft() {
    window.location.href = `${API_URL}/api/auth/microsoft`;
  }

  /* ================= SWITCH MODE ================= */

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setShowPassword(false);

    setForm({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });
  }

  return (
    <main className="relative h-screen w-full overflow-hidden bg-[#f7f9fc] flex items-center justify-center px-4 lg:px-6">

      {/* ================================================= */}
      {/* BACKGROUND GLOW */}
      {/* ================================================= */}

      <div className="pointer-events-none absolute -top-32 -left-32 h-96 w-96 rounded-full bg-blue-200/30 blur-3xl animate-pulse" />

      <div
        className="pointer-events-none absolute -bottom-40 -right-32 h-[28rem] w-[28rem] rounded-full bg-purple-200/25 blur-3xl animate-pulse"
        style={{ animationDelay: "1.5s" }}
      />

      {/* ================================================= */}
      {/* FLOATING PARTICLES */}
      {/* ================================================= */}

      <div className="pointer-events-none absolute inset-0 overflow-hidden">

        <span className="absolute left-[12%] top-[18%] h-2 w-2 rounded-full bg-blue-400/40 animate-bounce" />

        <span className="absolute left-[80%] top-[25%] h-1.5 w-1.5 rounded-full bg-purple-400/50 animate-ping" />

        <span className="absolute left-[20%] bottom-[20%] h-1.5 w-1.5 rounded-full bg-indigo-400/40 animate-pulse" />

        <span className="absolute right-[15%] bottom-[25%] h-2 w-2 rounded-full bg-blue-300/40 animate-bounce" />

      </div>

      {/* ================================================= */}
      {/* MAIN CONTENT */}
      {/* ================================================= */}

      <div className="relative z-10 w-full max-w-5xl h-full flex items-center">

        <div className="w-full grid lg:grid-cols-2 gap-6 xl:gap-10 items-center">

          {/* ================================================= */}
          {/* LEFT SIDE */}
          {/* ================================================= */}

          <section className="hidden lg:block px-4 xl:px-8">

            <div className="animate-[fadeIn_0.7s_ease-out]">

              {/* Badge */}

              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-white/70 backdrop-blur px-4 py-2 text-xs font-semibold text-blue-600 shadow-sm">

                <Sparkles size={15} />

                Your AI workspace for projects

              </div>

              {/* Logo */}

              <div className="mb-5">
                <A2ZNexusLogo size="lg" />
              </div>

              {/* Heading */}

              <h1 className="text-4xl xl:text-5xl font-bold tracking-tight text-[#111827] leading-tight">

                One AI Workspace.

                <br />

                <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">

                  For Your Projects.

                </span>

              </h1>

              {/* Description */}

              <p className="mt-4 max-w-lg text-sm xl:text-base leading-6 xl:leading-7 text-gray-500">

                Upload, analyze, improve, and manage your projects — all inside one intelligent workspace.

              </p>

              {/* Feature Cards */}

              <div className="mt-6 grid grid-cols-2 gap-3 max-w-lg">

                <FeatureCard
                  icon={<MessageCircle size={18} />}
                  title="AI Chat"
                  text="Smart conversations"
                />

                <FeatureCard
                  icon={<FileText size={18} />}
                  title="Project Analysis"
                  text="Analyze & improve"
                />

                <FeatureCard
                  icon={<Mic size={18} />}
                  title="Smart Tools"
                  text="Build & fix faster"
                />

                <FeatureCard
                  icon={<Briefcase size={18} />}
                  title="Manage Projects"
                  text="Organize your code"
                />

              </div>

            </div>

          </section>

          {/* ================================================= */}
          {/* RIGHT SIDE */}
          {/* ================================================= */}

          <section className="w-full max-w-md mx-auto">

            {/* Mobile Logo */}

            <div className="flex justify-center mb-4 lg:hidden">
              <A2ZNexusLogo size="md" />
            </div>

            {/* ================================================= */}
            {/* AUTH CARD */}
            {/* ================================================= */}

            <div className="rounded-[2rem] border border-white/80 bg-white/85 backdrop-blur-xl p-6 md:p-7 shadow-[0_25px_80px_rgba(15,23,42,0.12)] transition-all duration-500 hover:shadow-[0_30px_90px_rgba(15,23,42,0.16)]">

              {/* ================================================= */}
              {/* LOGIN / REGISTER TABS */}
              {/* ================================================= */}

              <div className="relative flex rounded-2xl bg-gray-100/80 p-1.5 mb-5">

                <div
                  className={`absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] rounded-xl bg-white shadow-sm transition-all duration-300 ${
                    mode === "register"
                      ? "translate-x-[calc(100%+6px)]"
                      : "translate-x-0"
                  }`}
                />

                <button
                  type="button"
                  onClick={() => switchMode("login")}
                  className={`relative z-10 flex-1 rounded-xl py-2 text-sm font-semibold transition-colors duration-300 ${
                    mode === "login"
                      ? "text-gray-900"
                      : "text-gray-400"
                  }`}
                >
                  Login
                </button>

                <button
                  type="button"
                  onClick={() => switchMode("register")}
                  className={`relative z-10 flex-1 rounded-xl py-2 text-sm font-semibold transition-colors duration-300 ${
                    mode === "register"
                      ? "text-gray-900"
                      : "text-gray-400"
                  }`}
                >
                  Register
                </button>

              </div>

              {/* ================================================= */}
              {/* TITLE */}
              {/* ================================================= */}

              <div className="mb-5">

                <div className="inline-flex items-center justify-center h-9 w-9 rounded-xl bg-blue-50 text-blue-600 mb-3">

                  {mode === "login" ? (
                    <LogIn size={18} />
                  ) : (
                    <UserPlus size={18} />
                  )}

                </div>

                <h1 className="text-xl md:text-2xl font-bold tracking-tight text-gray-900">
                  {title}
                </h1>

                <p className="text-xs md:text-sm text-gray-500 mt-1.5 leading-5">

                  {mode === "login"
                    ? "Sign in to continue to your AI workspace."
                    : "Create your account and start exploring A2Z Nexus."}

                </p>

              </div>

              {/* ================================================= */}
              {/* FORM */}
              {/* ================================================= */}

              <form
                onSubmit={submit}
                className="space-y-3.5"
              >

                {/* ================= NAME ================= */}

                {mode === "register" && (
                  <AnimatedInput
                    label="Name"
                    type="text"
                    value={form.name}
                    onChange={update("name")}
                    placeholder="Your name"
                  />
                )}

                {/* ================= EMAIL ================= */}

                <AnimatedInput
                  label="Email"
                  type="email"
                  value={form.email}
                  onChange={update("email")}
                  placeholder="you@example.com"
                />

                {/* ================= PASSWORD ================= */}

                <label className="block">

                  <span className="text-xs font-semibold text-gray-700">
                    Password
                  </span>

                  <div className="relative mt-1.5">

                    <input
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      value={form.password}
                      onChange={update("password")}
                      className="w-full rounded-xl border border-gray-200 bg-gray-50/70 px-4 py-2.5 pr-11 text-sm text-gray-900 outline-none transition-all duration-300 placeholder:text-gray-400 focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
                      placeholder="••••••••"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword((v) => !v)
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition"
                    >

                      {showPassword ? (
                        <EyeOff size={17} />
                      ) : (
                        <Eye size={17} />
                      )}

                    </button>

                  </div>

                </label>

                {/* ================================================= */}
                {/* CONFIRM PASSWORD - REGISTER ONLY */}
                {/* ================================================= */}

                {mode === "register" && (
                  <label className="block">

                    <span className="text-xs font-semibold text-gray-700">
                      Confirm Password
                    </span>

                    <div className="relative mt-1.5">

                      <input
                        type={
                          showPassword
                            ? "text"
                            : "password"
                        }
                        value={form.confirmPassword}
                        onChange={update("confirmPassword")}
                        className={`w-full rounded-xl border bg-gray-50/70 px-4 py-2.5 pr-11 text-sm text-gray-900 outline-none transition-all duration-300 placeholder:text-gray-400 focus:bg-white focus:ring-4 ${
                          form.confirmPassword &&
                          form.password !==
                            form.confirmPassword
                            ? "border-red-300 focus:border-red-400 focus:ring-red-100"
                            : "border-gray-200 focus:border-blue-400 focus:ring-blue-100"
                        }`}
                        placeholder="••••••••"
                      />

                      <button
                        type="button"
                        onClick={() =>
                          setShowPassword((v) => !v)
                        }
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition"
                      >

                        {showPassword ? (
                          <EyeOff size={17} />
                        ) : (
                          <Eye size={17} />
                        )}

                      </button>

                    </div>

                    {/* Live Password Match */}

                    {form.confirmPassword && (
                      <p
                        className={`mt-1.5 text-[11px] font-medium ${
                          form.password ===
                          form.confirmPassword
                            ? "text-green-600"
                            : "text-red-500"
                        }`}
                      >
                        {form.password ===
                        form.confirmPassword
                          ? "✓ Passwords match"
                          : "✕ Passwords do not match"}
                      </p>
                    )}

                  </label>
                )}

                {/* ================================================= */}
                {/* ERROR */}
                {/* ================================================= */}

                {error && (
                  <div className="rounded-xl border border-red-100 bg-red-50 px-3.5 py-2.5 text-xs md:text-sm text-red-600 animate-[shake_0.35s_ease-in-out]">
                    {error}
                  </div>
                )}

                {/* ================================================= */}
                {/* SUBMIT */}
                {/* ================================================= */}

                <button
                  type="submit"
                  className="group relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-blue-200 active:translate-y-0"
                >

                  <span className="absolute inset-0 -translate-x-full bg-white/20 transition-transform duration-700 group-hover:translate-x-full" />

                  <span className="relative flex items-center justify-center gap-2">

                    {mode === "login" ? (
                      <LogIn size={17} />
                    ) : (
                      <UserPlus size={17} />
                    )}

                    {mode === "login"
                      ? "Login to A2Z Nexus"
                      : "Create account"}

                    <ArrowRight
                      size={16}
                      className="transition-transform duration-300 group-hover:translate-x-1"
                    />

                  </span>

                </button>

              </form>

              {/* ================================================= */}
              {/* OR DIVIDER */}
              {/* ================================================= */}

              <div className="flex items-center gap-3 my-4">

                <div className="h-px bg-gray-200 flex-1" />

                <span className="text-[11px] font-semibold text-gray-400">
                  OR
                </span>

                <div className="h-px bg-gray-200 flex-1" />

              </div>

              {/* ================================================= */}
              {/* GOOGLE LOGIN */}
              {/* ================================================= */}

              <button
                type="button"
                onClick={continueWithGoogle}
                className="group w-full rounded-xl border border-gray-200 bg-white py-3 text-sm font-semibold text-gray-700 transition-all duration-300 hover:border-gray-300 hover:bg-gray-50 hover:-translate-y-0.5"
              >

                <span className="flex items-center justify-center gap-3">

                  {/* Google Icon */}

                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >

                    <path
                      fill="#4285F4"
                      d="M21.35 12.27c0-.79-.07-1.54-.23-2.27H12v4.3h5.22a4.47 4.47 0 0 1-1.94 2.93v2.43h3.14c1.84-1.7 2.93-4.2 2.93-7.39Z"
                    />

                    <path
                      fill="#34A853"
                      d="M12 21.5c2.63 0 4.84-.87 6.45-2.36l-3.14-2.43c-.87.58-1.98.92-3.31.92-2.54 0-4.69-1.72-5.46-4.03H3.3v2.5A9.75 9.75 0 0 0 12 21.5Z"
                    />

                    <path
                      fill="#FBBC05"
                      d="M6.54 13.6a5.86 5.86 0 0 1 0-3.2V7.9H3.3a9.75 9.75 0 0 0 0 8.2l3.24-2.5Z"
                    />

                    <path
                      fill="#EA4335"
                      d="M12 6.38c1.43 0 2.71.49 3.72 1.45l2.79-2.79C16.83 3.47 14.63 2.5 12 2.5a9.75 9.75 0 0 0-8.7 5.4l3.24 2.5C7.31 8.1 9.46 6.38 12 6.38Z"
                    />

                  </svg>

                  Continue with Google

                </span>

              </button>

              {/* ================================================= */}
              {/* MICROSOFT LOGIN */}
              {/* ================================================= */}

              <button
                type="button"
                onClick={continueWithMicrosoft}
                className="group w-full mt-3 rounded-xl border border-gray-200 bg-white py-3 text-sm font-semibold text-gray-700 transition-all duration-300 hover:border-gray-300 hover:bg-gray-50 hover:-translate-y-0.5"
              >

                <span className="flex items-center justify-center gap-3">

                  {/* Microsoft Icon */}

                  <span className="grid grid-cols-2 gap-[2px] w-[18px] h-[18px]">

                    <span className="bg-[#f25022]" />
                    <span className="bg-[#7fba00]" />
                    <span className="bg-[#00a4ef]" />
                    <span className="bg-[#ffb900]" />

                  </span>

                  Continue with Microsoft

                </span>

              </button>

            </div>

            {/* Footer */}

            <p className="text-center text-[10px] text-gray-400 mt-3">
              A2Z Nexus · Intelligent AI Workspace
            </p>

          </section>

        </div>

      </div>

      {/* ================================================= */}
      {/* ANIMATIONS */}
      {/* ================================================= */}

      <style>{`

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(18px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes shake {
          0%,
          100% {
            transform: translateX(0);
          }

          25% {
            transform: translateX(-4px);
          }

          75% {
            transform: translateX(4px);
          }
        }

      `}</style>

    </main>
  );
}

/* ================================================= */
/* FEATURE CARD */
/* ================================================= */

function FeatureCard({
  icon,
  title,
  text,
}) {
  return (
    <div className="group flex items-center gap-3 rounded-2xl border border-white bg-white/70 p-3 shadow-sm backdrop-blur transition-all duration-300 hover:-translate-y-1 hover:shadow-md">

      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition-transform duration-300 group-hover:scale-110">
        {icon}
      </div>

      <div>

        <p className="text-xs font-bold text-gray-800">
          {title}
        </p>

        <p className="text-[10px] text-gray-400">
          {text}
        </p>

      </div>

    </div>
  );
}

/* ================================================= */
/* ANIMATED INPUT */
/* ================================================= */

function AnimatedInput({
  label,
  type,
  value,
  onChange,
  placeholder,
}) {
  return (
    <label className="block">

      <span className="text-xs font-semibold text-gray-700">
        {label}
      </span>

      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="mt-1.5 w-full rounded-xl border border-gray-200 bg-gray-50/70 px-4 py-2.5 text-sm text-gray-900 outline-none transition-all duration-300 placeholder:text-gray-400 focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
      />

    </label>
  );
}