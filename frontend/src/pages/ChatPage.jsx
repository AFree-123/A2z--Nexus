import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Menu,
  Code2,
  Bug,
  TestTube2,
  FileText,
  Search,
  Sparkles,
  Wand2,
  BriefcaseBusiness,
  Bell,
  Sun,
  Moon,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import ChatHeader from "../components/ChatHeader";
import ChatMessage from "../components/ChatMessage";
import ChatComposer from "../components/ChatComposer";
import ShareModal from "../components/ShareModal";
import LoadingState from "../components/LoadingState";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000";
const CHAT_LIMIT = 10;

/* ======================================================
   ID
====================================================== */

function createId() {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 9)}`;
}

/* ======================================================
   SESSION
====================================================== */

function getSession() {
  try {
    return JSON.parse(
      localStorage.getItem("a2z-nexus-session") || "null"
    );
  } catch {
    return null;
  }
}

/* ======================================================
   STORAGE
====================================================== */

function getStorageKey(session) {
  if (!session) return "a2z-nexus-chats-guest";

  if (session.email) {
    return `a2z-nexus-chats-${session.email}`;
  }

  if (session.name) {
    return `a2z-nexus-chats-${session.name}`;
  }

  return "a2z-nexus-chats-guest";
}

function getUsageKey(session) {
  if (!session) return "a2z-nexus-usage-guest";

  if (session.email) {
    return `a2z-nexus-usage-${session.email}`;
  }

  if (session.name) {
    return `a2z-nexus-usage-${session.name}`;
  }

  return "a2z-nexus-usage-guest";
}

/* ======================================================
   LOAD CHATS
====================================================== */

function loadChats(session) {
  try {
    const saved = localStorage.getItem(
      getStorageKey(session)
    );

    if (!saved) return [];

    const parsed = JSON.parse(saved);

    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/* ======================================================
   LOAD USAGE
====================================================== */

function loadUsage(session) {
  try {
    const saved = localStorage.getItem(
      getUsageKey(session)
    );

    const today = new Date().toDateString();

    if (!saved) {
      return {
        date: today,
        used: 0,
        limit: CHAT_LIMIT,
      };
    }

    const parsed = JSON.parse(saved);

    if (parsed.date !== today) {
      return {
        date: today,
        used: 0,
        limit: CHAT_LIMIT,
      };
    }

    return {
      date: today,
      used: Number(parsed.used) || 0,
      limit: CHAT_LIMIT,
    };
  } catch {
    return {
      date: new Date().toDateString(),
      used: 0,
      limit: CHAT_LIMIT,
    };
  }
}

/* ======================================================
   NORMALIZE MESSAGE
====================================================== */

function normalizeMessage(message) {
  if (typeof message === "string") {
    return message.trim();
  }

  if (message && typeof message === "object") {
    return String(
      message.text ||
        message.content ||
        message.message ||
        ""
    ).trim();
  }

  return "";
}

/* ======================================================
   CHAT TITLE
====================================================== */

function generateChatTitle(message = "") {
  const text = String(message || "")
    .replace(/\s+/g, " ")
    .trim();

  if (!text) return "New Chat";

  const lower = text.toLowerCase();

  if (
    (lower.includes("tamilnadu") ||
      lower.includes("tamil nadu")) &&
    (lower.includes("cm") ||
      lower.includes("chief minister") ||
      lower.includes("yaru") ||
      lower.includes("who"))
  ) {
    return "Tamil Nadu Chief Minister";
  }

  if (
    lower.includes("india") &&
    (lower.includes("pm") ||
      lower.includes("prime minister"))
  ) {
    return "India Prime Minister";
  }

  if (
    lower.includes("full stack") ||
    lower.includes("fullstack")
  ) {
    if (
      lower.includes("roadmap") ||
      lower.includes("learn") ||
      lower.includes("learning")
    ) {
      return "Full Stack Roadmap";
    }

    return "Full Stack Development";
  }

  if (lower.includes("react")) {
    if (
      lower.includes("error") ||
      lower.includes("bug") ||
      lower.includes("fix")
    ) {
      return "React Error Fix";
    }

    return "React Development";
  }

  if (
    lower.includes("javascript") ||
    lower.includes(" js ")
  ) {
    return "JavaScript Development";
  }

  if (
    lower.includes("python") ||
    lower.includes("flask") ||
    lower.includes("fastapi")
  ) {
    return "Python Development";
  }

  if (
    lower.includes("html") ||
    lower.includes("css") ||
    lower.includes("tailwind")
  ) {
    return "Web Development";
  }

  if (
    lower.includes("backend") ||
    lower.includes("api") ||
    lower.includes("server")
  ) {
    return "Backend & API";
  }

  if (
    lower.includes("mysql") ||
    lower.includes("database") ||
    lower.includes("sql")
  ) {
    return "Database Development";
  }

  if (
    lower.includes("generate image") ||
    lower.includes("create image") ||
    lower.includes("make image") ||
    lower.includes("draw") ||
    lower.includes("picture") ||
    lower.includes("photo")
  ) {
    return "Image Generation";
  }

  if (
    lower.includes("job") ||
    lower.includes("internship") ||
    lower.includes("intern")
  ) {
    return "Jobs & Internships";
  }

  if (
    lower.includes("resume") ||
    lower.includes("cv") ||
    lower.includes("linkedin")
  ) {
    return "Career Profile";
  }

  if (
    lower.includes("code") ||
    lower.includes("coding") ||
    lower.includes("program") ||
    lower.includes("programming")
  ) {
    return "Coding Help";
  }

  if (
    lower.includes("project") ||
    lower.includes("website") ||
    lower.includes("application") ||
    lower.includes(" app ")
  ) {
    return "Project Development";
  }

  if (
    lower.includes("sih") ||
    lower.includes("smart india hackathon")
  ) {
    return "SIH Project";
  }

  if (
    lower.includes("traffic signal") ||
    lower.includes("traffic management")
  ) {
    return "Smart Traffic Signal";
  }

  if (
    lower.includes("reminder") ||
    lower.includes("remind me")
  ) {
    return "Reminder";
  }

  if (
    lower.includes("pdf") ||
    lower.includes("document") ||
    lower.includes("docx")
  ) {
    return "Document Creation";
  }

  if (
    lower.includes("latest") ||
    lower.includes("current") ||
    lower.includes("news")
  ) {
    return "Latest Information";
  }

  if (lower.includes("weather")) {
    return "Weather Information";
  }

  const cleaned = text
    .replace(
      /^(hi|hello|hey|hii|helo|bro|dude|please)\s+/i,
      ""
    )
    .trim();

  const words = cleaned
    .split(" ")
    .filter(Boolean)
    .slice(0, 6);

  if (!words.length) {
    return "New Chat";
  }

  let title = words.join(" ");

  if (title.length > 38) {
    title = title.slice(0, 38).trim();
  }

  if (cleaned.split(" ").length > 6) {
    title += "...";
  }

  return (
    title.charAt(0).toUpperCase() +
    title.slice(1)
  );
}

/* ======================================================
   LOADING TYPE
====================================================== */

function detectLoadingType(message = "", files = []) {
  const text = String(message).toLowerCase();

  if (
    files.some((file) =>
      file?.type?.startsWith("image/")
    )
  ) {
    return "thinking";
  }

  if (
    text.includes("generate image") ||
    text.includes("create image") ||
    text.includes("make image") ||
    text.includes("draw") ||
    text.includes("image of") ||
    text.includes("picture of") ||
    text.includes("photo of")
  ) {
    return "image";
  }

  if (
    text.includes("code") ||
    text.includes("coding") ||
    text.includes("javascript") ||
    text.includes("python") ||
    text.includes("react") ||
    text.includes("html") ||
    text.includes("css") ||
    text.includes("java ") ||
    text.includes("write a program") ||
    text.includes("fix this code")
  ) {
    return "code";
  }

  if (
    text.includes("pdf") ||
    text.includes("document") ||
    text.includes("docx") ||
    text.includes("create file") ||
    text.includes("create a document")
  ) {
    return "document";
  }

  if (
    text.includes("search") ||
    text.includes("latest") ||
    text.includes("current") ||
    text.includes("today") ||
    text.includes("news") ||
    text.includes("who is") ||
    text.includes("where is") ||
    text.includes("price") ||
    text.includes("weather")
  ) {
    return "searching";
  }

  return "thinking";
}

/* ======================================================
   FILE -> DATA URL
====================================================== */

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve(null);
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      resolve(reader.result);
    };

    reader.onerror = () => {
      reject(
        new Error(
          `Unable to read file: ${file.name}`
        )
      );
    };

    reader.readAsDataURL(file);
  });
}

/* ======================================================
   COMPRESS IMAGE
====================================================== */

function compressImage(file, maxSize = 1600) {
  return new Promise((resolve, reject) => {
    if (!file?.type?.startsWith("image/")) {
      resolve(null);
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      const image = new Image();

      image.onload = () => {
        let width = image.width;
        let height = image.height;

        if (
          width > maxSize ||
          height > maxSize
        ) {
          const scale = Math.min(
            maxSize / width,
            maxSize / height
          );

          width = Math.round(width * scale);
          height = Math.round(height * scale);
        }

        const canvas =
          document.createElement("canvas");

        canvas.width = width;
        canvas.height = height;

        const ctx =
          canvas.getContext("2d");

        ctx.drawImage(
          image,
          0,
          0,
          width,
          height
        );

        const dataUrl =
          canvas.toDataURL(
            "image/jpeg",
            0.82
          );

        resolve(dataUrl);
      };

      image.onerror = () => {
        reject(
          new Error(
            `Unable to process image: ${file.name}`
          )
        );
      };

      image.src = reader.result;
    };

    reader.onerror = () => {
      reject(
        new Error(
          `Unable to read image: ${file.name}`
        )
      );
    };

    reader.readAsDataURL(file);
  });
}

/* ======================================================
   MAIN
====================================================== */

export default function ChatPage() {
  const navigate = useNavigate();
  const session = getSession();

  const [chats, setChats] = useState(() =>
    loadChats(session)
  );

  const [activeChat, setActiveChat] =
    useState(null);

  const [messages, setMessages] =
    useState([]);

  const [isLoading, setIsLoading] =
    useState(false);

  const [loadingType, setLoadingType] =
    useState("thinking");

  const [sidebarOpen, setSidebarOpen] =
    useState(true);

  const [shareOpen, setShareOpen] =
    useState(false);

  const [darkMode, setDarkMode] = useState(() =>
    localStorage.getItem("a2z-nexus-theme") === "dark"
  );

  function toggleTheme() {
    setDarkMode((current) => {
      const next = !current;
      localStorage.setItem("a2z-nexus-theme", next ? "dark" : "light");
      document.documentElement.classList.toggle("a2z-dark", next);
      return next;
    });
  }

  useEffect(() => {
    document.documentElement.classList.toggle("a2z-dark", darkMode);
  }, [darkMode]);

  const [usage, setUsage] =
    useState(() => loadUsage(session));

  const messagesEndRef =
    useRef(null);

  /* ====================================================
     AUTO SCROLL
  ==================================================== */

  const scrollToBottom = (smooth = true) => {
    requestAnimationFrame(() => {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({
          behavior: smooth ? "smooth" : "auto",
          block: "end",
        });
      }, 30);
    });
  };

  useEffect(() => {
    scrollToBottom(true);
  }, [messages, isLoading]);

  /* ====================================================
     SAVE CHATS
  ==================================================== */

  useEffect(() => {
    try {
      localStorage.setItem(
        getStorageKey(session),
        JSON.stringify(chats)
      );
    } catch {}
  }, [chats]);

  /* ====================================================
     SAVE USAGE
  ==================================================== */

  useEffect(() => {
    try {
      localStorage.setItem(
        getUsageKey(session),
        JSON.stringify(usage)
      );
    } catch {}
  }, [usage]);

  /* ====================================================
     LOAD LATEST CHAT
  ==================================================== */

  useEffect(() => {
    if (!chats.length) {
      setActiveChat(null);
      setMessages([]);
      return;
    }

    const latestChat = [...chats].sort(
      (a, b) =>
        new Date(
          b.updatedAt ||
            b.createdAt ||
            0
        ) -
        new Date(
          a.updatedAt ||
            a.createdAt ||
            0
        )
    )[0];

    if (latestChat) {
      setActiveChat(latestChat.id);

      setMessages(
        Array.isArray(
          latestChat.messages
        )
          ? latestChat.messages
          : []
      );

      setTimeout(
        () => scrollToBottom(false),
        100
      );
    }
  }, []);

  /* ====================================================
     UPDATE CHAT
  ==================================================== */

  function updateCurrentChat(
    chatId,
    updatedMessages
  ) {
    setChats((currentChats) =>
      currentChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              messages:
                updatedMessages,
              updatedAt:
                new Date().toISOString(),
            }
          : chat
      )
    );
  }

  /* ====================================================
     SELECT CHAT
  ==================================================== */

  function handleSelectChat(chatId) {
    stopSpeaking();

    const selected =
      chats.find(
        (chat) =>
          chat.id === chatId
      );

    if (!selected) return;

    setActiveChat(chatId);

    setMessages(
      Array.isArray(
        selected.messages
      )
        ? selected.messages
        : []
    );

    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }

    setTimeout(
      () => scrollToBottom(false),
      100
    );
  }

  /* ====================================================
     NEW CHAT
  ==================================================== */

  function handleNewChat() {
    if (
      usage.used >=
      usage.limit
    ) {
      return;
    }

    stopSpeaking();

    setActiveChat(null);
    setMessages([]);
    setLoadingType("thinking");

    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }

    setTimeout(
      () => scrollToBottom(false),
      100
    );
  }

  /* ====================================================
     DELETE CHAT
  ==================================================== */

  function handleDeleteChat(chatId) {
    const remainingChats =
      chats.filter(
        (chat) =>
          chat.id !== chatId
      );

    setChats(remainingChats);

    if (
      activeChat === chatId
    ) {
      setActiveChat(null);
      setMessages([]);

      if (
        remainingChats.length >
        0
      ) {
        const latest =
          [...remainingChats].sort(
            (a, b) =>
              new Date(
                b.updatedAt ||
                  b.createdAt ||
                  0
              ) -
              new Date(
                a.updatedAt ||
                  a.createdAt ||
                  0
              )
          )[0];

        if (latest) {
          setActiveChat(
            latest.id
          );

          setMessages(
            Array.isArray(
              latest.messages
            )
              ? latest.messages
              : []
          );
        }
      }
    }
  }

  /* ====================================================
     SHARE
  ==================================================== */

  function handleShareChat() {
    if (!activeChat) return;

    setShareOpen(true);
  }

  /* ====================================================
     SPEECH
  ==================================================== */

  function speakText(text) {
    if (
      typeof window === "undefined" ||
      !window.speechSynthesis ||
      !text
    ) {
      return;
    }

    try {
      window.speechSynthesis.cancel();

      const clean = String(text)
        .replace(
          /```[\s\S]*?```/g,
          ""
        )
        .replace(
          /[*_#>`]/g,
          ""
        )
        .trim();

      if (!clean) return;

      const utterance =
        new SpeechSynthesisUtterance(
          clean
        );

      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;

      window.speechSynthesis.speak(
        utterance
      );
    } catch {}
  }

  function stopSpeaking() {
    try {
      window.speechSynthesis?.cancel();
    } catch {}
  }

  /* ====================================================
     LOCATION
  ==================================================== */

  function getBrowserLocation() {
    return new Promise(
      (resolve) => {
        if (
          !navigator.geolocation
        ) {
          resolve(null);
          return;
        }

        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              latitude:
                position.coords.latitude,
              longitude:
                position.coords.longitude,
            });
          },
          () => resolve(null),
          {
            enableHighAccuracy: false,
            timeout: 8000,
            maximumAge: 300000,
          }
        );
      }
    );
  }

  /* ====================================================
     SEND MESSAGE
  ==================================================== */

  async function handleSend(payload) {
    const cleanMessage =
      normalizeMessage(payload);

    const files =
      payload &&
      typeof payload === "object" &&
      Array.isArray(payload.files)
        ? payload.files
        : [];

    if (
      (!cleanMessage &&
        files.length === 0) ||
      isLoading
    ) {
      return;
    }

    stopSpeaking();

    setLoadingType(
      detectLoadingType(
        cleanMessage,
        files
      )
    );

    let chatId =
      activeChat;

    let currentMessages = [
      ...messages,
    ];

    /* ==================================================
       FILE INFORMATION
    ================================================== */

    const imageFiles = files.filter(
      (file) =>
        file?.type?.startsWith("image/")
    );

    const nonImageFiles = files.filter(
      (file) =>
        !file?.type?.startsWith("image/")
    );

    const finalMessage =
      cleanMessage ||
      (files.length
        ? `Please analyze the uploaded file${
            files.length > 1
              ? "s"
              : ""
          }: ${files
            .map((file) => file.name)
            .join(", ")}`
        : "");

    if (!finalMessage) {
      return;
    }

    /* ==================================================
       NEW CHAT
    ================================================== */

    if (!chatId) {
      if (
        usage.used >=
        usage.limit
      ) {
        const limitMessage = {
  role: "assistant",
  agent: "System Agent",
  content: `🔒 You have reached today's 10-chat limit.
You can continue sending messages inside your existing conversations. Your new-chat limit will reset tomorrow.`,
};
        setMessages(
          (current) => [
            ...current,
            limitMessage,
          ]
        );

        setTimeout(
          () => scrollToBottom(true),
          50
        );

        return;
      }

      const now =
        new Date().toISOString();

      const newChatId =
        createId();

      const userMessage = {
        id: createId(),
        role: "user",
        content:
          finalMessage,
      };

      currentMessages = [
        userMessage,
      ];

      const chatTitle =
        generateChatTitle(
          finalMessage
        );

      const newChat = {
        id: newChatId,
        title: chatTitle,
        titleLocked: true,
        messages:
          currentMessages,
        createdAt: now,
        updatedAt: now,
      };

      chatId =
        newChatId;

      setChats(
        (currentChats) => [
          newChat,
          ...currentChats,
        ]
      );

      setActiveChat(
        newChatId
      );

      setMessages(
        currentMessages
      );

      setUsage(
        (currentUsage) => ({
          ...currentUsage,
          date:
            new Date().toDateString(),
          used:
            currentUsage.used +
            1,
        })
      );
    } else {
      /* =================================================
         EXISTING CHAT
      ================================================= */

      const userMessage = {
        id: createId(),
        role: "user",
        content:
          finalMessage,
      };

      currentMessages = [
        ...currentMessages,
        userMessage,
      ];

      setMessages(
        currentMessages
      );

      updateCurrentChat(
        chatId,
        currentMessages
      );
    }

    setTimeout(
      () => scrollToBottom(true),
      50
    );

    setIsLoading(true);

    /* ==================================================
       PROJECT ZIP -> WORKSPACE
       Uses the existing attachment UI; no visual changes.
    ================================================== */

    let projectId = localStorage.getItem("a2z-nexus-project-id") || "";
    const zipFile = files.find((file) =>
      file?.name?.toLowerCase().endsWith(".zip")
    );

    /* ==================================================
       API
    ================================================== */

    try {
      if (zipFile) {
        const projectName = zipFile.name.replace(/\.zip$/i, "");
        const createResponse = await fetch(`${API_URL}/api/projects?user_id=default-user`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: projectName,
            description: "Project uploaded from A2Z Nexus Chat",
            repository_path: "",
            technology: "",
            user_id: "default-user"
          })
        });
        if (!createResponse.ok) throw new Error("Could not create the project workspace.");
        const created = await createResponse.json();
        projectId = created.id;

        const form = new FormData();
        form.append("file", zipFile);
        form.append("project_name", projectName);
        form.append("user_id", "default-user");
        const uploadResponse = await fetch(`${API_URL}/api/workspace/projects/${projectId}/upload`, {
          method: "POST",
          body: form
        });
        if (!uploadResponse.ok) {
          const errorText = await uploadResponse.text();
          throw new Error(errorText || "Project upload failed.");
        }
        localStorage.setItem("a2z-nexus-project-id", projectId);
        localStorage.setItem("a2z-nexus-project-name", projectName);
      }
      let location = null;

      const locationWords =
        /\b(near me|nearby|my location|where am i|around me|close to me)\b/i;

      if (
        locationWords.test(
          finalMessage
        )
      ) {
        location =
          await getBrowserLocation();
      }

      /* =================================================
         IMAGE
      ================================================= */

      let image = null;

      if (imageFiles.length > 0) {
        image =
          await compressImage(
            imageFiles[0]
          );
      }

      /* =================================================
         NON-IMAGE FILE INFO
      ================================================= */

      let uploadedFiles = [];

      if (
        nonImageFiles.length > 0
      ) {
        uploadedFiles =
          nonImageFiles.map(
            (file) => ({
              name: file.name,
              type:
                file.type ||
                "application/octet-stream",
              size: file.size,
            })
          );
      }

      /* =================================================
         HISTORY
      ================================================= */

      const previousMessages =
        currentMessages
          .slice(0, -1)
          .slice(-20)
          .map((item) => ({
            role:
              item.role,
            content:
              item.content ||
              "",
          }));

      // Reuse the backend chat session for this conversation so the AI keeps
      // context between turns. Without this, every message started a brand
      // new session on the backend and conversation memory was always empty.
      const backendSessionId =
        localStorage.getItem(`a2z-nexus-backend-session-${chatId}`) ||
        undefined;

      const requestBody = {
        message:
          finalMessage,

        project_id: projectId || undefined,

        session_id: backendSessionId,

        history:
          previousMessages,

        session: {
          name:
            session?.name ||
            "Guest",

          email:
            session?.email ||
            "",

          guest:
            !!session?.guest,
        },

        location,
      };

      if (image) {
        requestBody.image =
          image;
      }

      if (
        uploadedFiles.length > 0
      ) {
        requestBody.files =
          uploadedFiles;
      }

      console.log(
        "=============================="
      );

      console.log(
        "A2Z NEXUS REQUEST"
      );

      console.log(
        "MESSAGE:",
        finalMessage
      );

      console.log(
        "IMAGE:",
        image
          ? "IMAGE ATTACHED"
          : "NO IMAGE"
      );

      console.log(
        "FILES:",
        uploadedFiles
      );

      console.log(
        "HISTORY:",
        previousMessages.length
      );

      console.log(
        "=============================="
      );

      const response =
        await fetch(
          `${API_URL}/api/chat`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify(
              requestBody
            ),
          }
        );

      if (!response.ok) {
        let errorText =
          `Server error (${response.status})`;

        try {
          const errorData =
            await response.json();

          errorText =
            errorData?.error ||
            errorData?.message ||
            errorText;
        } catch {}

        throw new Error(
          errorText
        );
      }

      const data =
        await response.json();

      console.log(
        "A2Z NEXUS RESPONSE:",
        data
      );

      if (data.session_id) {
        localStorage.setItem(
          `a2z-nexus-backend-session-${chatId}`,
          data.session_id
        );
      }

      /* =================================================
         ASSISTANT MESSAGE
      ================================================= */

      const assistantMessage = {
        id: createId(),

        role: "assistant",

        content:
          data.reply ||
          data.message ||
          data.content ||
          "I couldn't generate a response.",

        agent:
          data.agent ||
          "A2Z Nexus",

        image:
          data.image || null,

        jobs:
          Array.isArray(data.jobs)
            ? data.jobs
            : [],

        reminder:
          data.reminder ||
          null,

        audio:
          data.audio ||
          null,

        file:
          data.file ||
          null,

        search:
          data.search ||
          false,

        searchProvider:
          data.searchProvider ||
          null,
      };

      const finalMessages = [
        ...currentMessages,
        assistantMessage,
      ];

      setMessages(
        finalMessages
      );

      updateCurrentChat(
        chatId,
        finalMessages
      );

      /* =================================================
         VOICE
      ================================================= */

      if (
        !assistantMessage.audio?.url &&
        data.voiceResponse === true
      ) {
        speakText(
          assistantMessage.content
        );
      }

      setTimeout(
        () => scrollToBottom(true),
        100
      );
    } catch (error) {
      console.error(
        "A2Z Nexus chat error:",
        error
      );

      const errorMessage = {
        id: createId(),

        role: "assistant",

        agent:
          "System Agent",

        content:
          `⚠️ Something went wrong.

${
            error?.message ||
            "Unable to connect to A2Z Nexus server."
          }

Please make sure the backend is running on port 4000.`,
      };

      const finalMessages = [
        ...currentMessages,
        errorMessage,
      ];

      setMessages(
        finalMessages
      );

      updateCurrentChat(
        chatId,
        finalMessages
      );
    } finally {
      setIsLoading(false);

      setTimeout(
        () => scrollToBottom(true),
        150
      );
    }
  }

  /* ====================================================
     QUICK ACTIONS
  ==================================================== */

  const quickActions = [
    {
      icon: Code2,
      label: "Explain Code",
      prompt:
        "Explain this code in simple terms and suggest improvements.",
    },
    {
      icon: Bug,
      label: "Debug",
      prompt:
        "Help me debug my code and find the issue.",
    },
    {
      icon: TestTube2,
      label: "Write Tests",
      prompt:
        "Write test cases for my code.",
    },
    {
      icon: Search,
      label: "Analyze Project",
      prompt:
        "Analyze my project and suggest improvements.",
    },
    {
      icon: FileText,
      label: "Generate Docs",
      prompt:
        "Create documentation for my project.",
    },
    {
      icon: Wand2,
      label: "Improve Code",
      prompt:
        "Improve this code for readability and performance.",
    },
  ];

  function sendStarterPrompt(prompt) {
    handleSend({
      text: prompt,
      files: [],
    });
  }

  /* ====================================================
     UI
  ==================================================== */

  return (
    <div className="flex h-screen bg-[#f7f8ff] text-ink overflow-hidden">

      {/* =================================================
          LEFT NAVIGATION
      ================================================= */}

      <Sidebar
        activeChat={activeChat}
        chats={chats}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onShareChat={handleShareChat}
        mobileOpen={sidebarOpen}
        onCloseMobile={() =>
          setSidebarOpen(false)
        }
        usage={usage}
      />

      {!sidebarOpen && (
        <button
          type="button"
          onClick={() =>
            setSidebarOpen(true)
          }
          title="Open sidebar"
          aria-label="Open sidebar"
          className="fixed top-4 left-4 z-[70] w-10 h-10 rounded-xl bg-white/95 border border-[#e5e7eb] shadow-lg flex items-center justify-center text-ink hover:bg-[#f5f3ff] transition-all"
        >
          <Menu size={19} />
        </button>
      )}

      {/* =================================================
          MAIN WORKSPACE
      ================================================= */}

      <main className="flex-1 min-w-0 h-full flex flex-col bg-white relative overflow-hidden">

        {/* =================================================
            TOP BAR
        ================================================= */}

        <header className="h-[72px] shrink-0 border-b border-[#eef0f6] bg-white/90 backdrop-blur-xl flex items-center justify-end px-4 md:px-7 relative z-10">

          <div className="flex items-center gap-2.5">

            <button
              type="button"
              title={darkMode ? "Light theme" : "Dark theme"}
              onClick={toggleTheme}
              className="hidden sm:flex w-10 h-10 rounded-xl items-center justify-center text-[#64748b] hover:text-[#4f46e5] hover:bg-[#f5f3ff] transition"
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <button
              type="button"
              title="Notifications"
              onClick={() => navigate("/notifications")}
              className="relative hidden sm:flex w-10 h-10 rounded-xl items-center justify-center text-[#64748b] hover:text-[#4f46e5] hover:bg-[#f5f3ff] transition"
            >
              <Bell size={18} />

              <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[#ef4444] text-white text-[9px] font-bold flex items-center justify-center">
                3
              </span>
            </button>

            <div className="h-8 w-px bg-[#edf0f5] hidden sm:block" />

            <div className="flex items-center gap-2.5 pl-1">

              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#7c3aed] flex items-center justify-center text-white text-xs font-bold shadow-md">
                {(session?.name?.[0] ||
                  "G"
                ).toUpperCase()}
              </div>

              <div className="hidden md:block leading-tight">
                <p className="text-xs font-semibold text-[#172554]">
                  {session?.name ||
                    "Guest"}
                </p>

                <p className="text-[10px] text-[#64748b]">
                  AI Workspace
                </p>
              </div>

              <span className="text-xs text-[#64748b] hidden md:block">
                ⌄
              </span>

            </div>
          </div>
        </header>

        {/* =================================================
            CHAT BODY
        ================================================= */}

        <div className="flex-1 min-h-0 flex overflow-hidden relative">

          <section className="flex-1 min-w-0 flex flex-col relative overflow-hidden">

            {/* Soft decorative background */}

            <div className="pointer-events-none absolute inset-0 overflow-hidden">

              <div className="absolute -top-32 -left-24 w-80 h-80 rounded-full bg-[#e9e7ff] blur-3xl opacity-70" />

              <div className="absolute -bottom-40 -left-20 w-96 h-96 rounded-full bg-[#eef2ff] blur-3xl opacity-80" />

              <div className="absolute -bottom-36 -right-24 w-96 h-96 rounded-full bg-[#f3e8ff] blur-3xl opacity-70" />

            </div>

            {/* =================================================
                CHAT CONTENT
            ================================================= */}

            <div className="flex-1 overflow-y-auto overscroll-contain scroll-smooth relative z-[1]">

              <div className="w-full max-w-6xl mx-auto px-5 md:px-10 py-8 min-h-full">

                {/* =================================================
                    EMPTY CHAT
                ================================================= */}

                {messages.length === 0 &&
                  !isLoading && (
                    <div className="min-h-[calc(100vh-190px)] flex flex-col items-center justify-center text-center px-4 pb-10">

                      {/* =========================================
                          A2Z NEXUS LOGO
                          NO BACKGROUND
                          NO CARD
                          NO BORDER
                          FLOATING ANIMATION
                      ========================================= */}

                      <div className="relative mb-6 flex items-center justify-center">

                        <img
                          src="/assets/a2z-nexus-logo.png"
                          alt="A2Z Nexus"
                          draggable={false}
                          className="w-28 h-28 object-contain a2z-logo-float select-none"
                        />

                      </div>

                      {/* =========================================
                          HEADING
                      ========================================= */}

                      <h1 className="text-3xl md:text-4xl font-bold tracking-[-0.03em] text-[#111b4d]">

                        How can I{" "}

                        <span className="bg-gradient-to-r from-[#4f46e5] to-[#7c3aed] bg-clip-text text-transparent">

                          help you

                        </span>{" "}

                        today?

                      </h1>

                      {/* =========================================
                          DESCRIPTION
                      ========================================= */}

                      <p className="text-sm md:text-base text-[#64748b] mt-4 max-w-2xl leading-7">

                        Ask anything, get instant answers, solve problems, and bring your ideas to life with A2Z Nexus.

                      </p>

                      {/* =========================================
                          QUICK ACTIONS
                      ========================================= */}

                      <div className="mt-8 flex flex-wrap items-center justify-center gap-3 max-w-4xl">

                        {[
                          [
                            Code2,
                            "Code",
                            "Explain or improve code",
                          ],
                          [
                            FileText,
                            "Documents",
                            "Write and analyze",
                          ],
                          [
                            Sparkles,
                            "AI Chat",
                            "Ask anything",
                          ],
                          [
                            Wand2,
                            "Create",
                            "Build your ideas",
                          ],
                          [
                            Search,
                            "Web Search",
                            "Find current info",
                          ],
                          [
                            BriefcaseBusiness,
                            "Jobs",
                            "Find opportunities",
                          ],
                          [
                            BellIcon,
                            "Reminders",
                            "Remember tasks",
                          ],
                        ].map(
                          ([
                            Icon,
                            label,
                            hint,
                          ]) => (
                            <button
                              key={label}
                              type="button"
                              onClick={() =>
                                sendStarterPrompt(
                                  hint
                                )
                              }
                              className="group flex items-center gap-2.5 rounded-full border border-[#e5e7eb] bg-white/90 px-4 py-2.5 text-xs md:text-sm font-medium text-[#334155] shadow-[0_5px_18px_rgba(79,70,229,0.06)] hover:-translate-y-0.5 hover:border-[#c4b5fd] hover:bg-[#faf9ff] hover:text-[#4f46e5] transition-all"
                            >

                              <span className="w-7 h-7 rounded-full bg-[#f5f3ff] flex items-center justify-center group-hover:bg-[#ede9fe] transition">

                                <Icon
                                  size={15}
                                  className="text-[#4f46e5]"
                                />

                              </span>

                              {label}

                            </button>
                          )
                        )}

                      </div>
                    </div>
                  )}

                {/* =================================================
                    MESSAGES
                ================================================= */}

                {messages.map(
                  (message) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                    />
                  )
                )}

                {/* =================================================
                    LOADING
                ================================================= */}

                {isLoading && (
                  <LoadingState
                    type={loadingType}
                  />
                )}

                <div
                  ref={messagesEndRef}
                  className="h-px w-full"
                />

              </div>
            </div>

            {/* =================================================
                COMPOSER
            ================================================= */}

            <div className="shrink-0 px-4 md:px-10 pb-5 pt-2 bg-gradient-to-t from-white via-white/95 to-transparent relative z-[2]">

              <div className="max-w-6xl mx-auto">

                <div className="rounded-[24px] bg-white border border-[#e5e7eb] shadow-[0_10px_35px_rgba(79,70,229,0.10)] p-1.5">

                  <ChatComposer
                    onSend={handleSend}
                    disabled={isLoading}
                  />

                </div>

              </div>

            </div>

          </section>

        </div>

      </main>

      {/* =================================================
          SHARE MODAL
      ================================================= */}

      {shareOpen && (
        <ShareModal
          open={shareOpen}
          onClose={() =>
            setShareOpen(false)
          }
          chat={
            chats.find(
              (chat) =>
                chat.id === activeChat
            ) || null
          }
        />
      )}

    </div>
  );
}

/* ======================================================
   BELL ICON
====================================================== */

function BellIcon() {
  return (
    <span className="relative inline-flex">

      <span className="text-sm">
        ♧
      </span>

      <span className="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full bg-red-400" />

    </span>
  );
}