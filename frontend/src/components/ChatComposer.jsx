import { useEffect, useRef, useState } from "react";

import {
  Paperclip,
  Mic,
  ArrowUp,
  Square,
  Image as ImageIcon,
  FileText,
  Video,
  FolderOpen,
  X,
} from "lucide-react";

import FileAttachment from "./FileAttachment";

export default function ChatComposer({
  onSend,
  disabled = false,
}) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [listening, setListening] = useState(false);

  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  /* ======================================================
     VOICE
  ====================================================== */

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";

      for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
      ) {
        const transcript =
          event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interimText += transcript;
        }
      }

      if (finalText) {
        setText((old) => {
          const clean = old
            .replace(/\s*\[listening\].*$/i, "")
            .trim();

          return clean
            ? `${clean} ${finalText.trim()}`
            : finalText.trim();
        });
      }

      if (interimText) {
        setText((old) => {
          const clean = old
            .replace(/\s*\[listening\].*$/i, "")
            .trim();

          return clean
            ? `${clean} [listening] ${interimText.trim()}`
            : `${interimText.trim()} [listening]`;
        });
      }
    };

    recognition.onerror = (event) => {
      console.error(
        "Voice error:",
        event.error
      );

      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);

      setText((old) =>
        old
          .replace(/\s*\[listening\].*$/i, "")
          .trim()
      );
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch {}

      recognitionRef.current = null;
    };
  }, []);

  /* ======================================================
     START VOICE
  ====================================================== */

  function startVoice() {
    if (disabled) return;

    const recognition =
      recognitionRef.current;

    if (!recognition) {
      alert(
        "Voice input is not supported in this browser."
      );
      return;
    }

    try {
      recognition.start();
    } catch {}
  }

  /* ======================================================
     STOP VOICE
  ====================================================== */

  function stopVoice() {
    try {
      recognitionRef.current?.stop();
    } catch {}

    setListening(false);
  }

  /* ======================================================
     TOGGLE VOICE
  ====================================================== */

  function toggleVoice() {
    if (listening) {
      stopVoice();
    } else {
      startVoice();
    }
  }

  /* ======================================================
     FILE PICKER
  ====================================================== */

  function chooseFile(accept) {
    if (!fileInputRef.current) {
      return;
    }

    fileInputRef.current.accept = accept;

    setMenuOpen(false);

    setTimeout(() => {
      fileInputRef.current?.click();
    }, 100);
  }

  /* ======================================================
     FILE CHANGE
  ====================================================== */

  function handleFileChange(event) {
    const selected = Array.from(
      event.target.files || []
    );

    console.log(
      "FILE SELECTED:",
      selected
    );

    if (!selected.length) {
      return;
    }

    setFiles((old) => [
      ...old,
      ...selected,
    ]);

    event.target.value = "";
  }

  /* ======================================================
     REMOVE FILE
  ====================================================== */

  function removeFile(index) {
    setFiles((old) =>
      old.filter(
        (_, i) => i !== index
      )
    );
  }

  /* ======================================================
     SEND MESSAGE
  ====================================================== */

  function sendMessage() {
    console.log(
      "========================"
    );

    console.log(
      "A2Z SEND BUTTON CLICKED"
    );

    console.log(
      "TEXT:",
      text
    );

    console.log(
      "FILES:",
      files
    );

    console.log(
      "DISABLED:",
      disabled
    );

    console.log(
      "========================"
    );

    const cleanText = text
      .replace(
        /\s*\[listening\].*$/i,
        ""
      )
      .trim();

    /*
      If only file/image exists,
      automatically create a message.
    */

    let finalText = cleanText;

    if (
      !finalText &&
      files.length > 0
    ) {
      finalText =
        `Please analyze the uploaded file${
          files.length > 1
            ? "s"
            : ""
        }: ${files
          .map((file) => file.name)
          .join(", ")}`;
    }

    /*
      Nothing to send
    */

    if (
      !finalText &&
      files.length === 0
    ) {
      console.log(
        "NOTHING TO SEND"
      );

      return;
    }

    stopVoice();

    /*
      Send object to ChatPage.
    */

    const payload = {
      text: finalText,
      files: [...files],
    };

    console.log(
      "SENDING PAYLOAD:",
      payload
    );

    if (
      typeof onSend !== "function"
    ) {
      console.error(
        "ERROR: onSend is not a function"
      );

      return;
    }

    onSend(payload);

    /*
      Clear after sending.
    */

    setText("");
    setFiles([]);
    setMenuOpen(false);
  }

  /* ======================================================
     ENTER KEY
  ====================================================== */

  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      sendMessage();
    }
  }

  /* ======================================================
     CAN SEND
  ====================================================== */

  const canSend =
    !disabled &&
    (
      text.trim().length > 0 ||
      files.length > 0
    );

  /* ======================================================
     UI
  ====================================================== */

  return (
    <div className="bg-transparent">

      {/* ==================================================
          SELECTED FILES
      ================================================== */}

      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3 px-2">

          {files.map(
            (file, index) => (
              <div
                key={`${file.name}-${index}`}
              >
                <FileAttachment
                  file={file}
                  onRemove={() =>
                    removeFile(index)
                  }
                />
              </div>
            )
          )}

        </div>
      )}

      {/* ==================================================
          LISTENING
      ================================================== */}

      {listening && (
        <div className="mb-2 px-2 flex items-center gap-2 text-sm text-primary">

          <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />

          <span>
            Listening...
          </span>

          <button
            type="button"
            onClick={stopVoice}
            className="ml-2 underline text-muted hover:text-ink transition"
          >
            Cancel
          </button>

        </div>
      )}

      {/* ==================================================
          COMPOSER
      ================================================== */}

      <div className="relative">

        {/* ==================================================
            ATTACHMENT MENU
        ================================================== */}

        {menuOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() =>
                setMenuOpen(false)
              }
            />

            <div className="absolute bottom-14 left-0 z-50 w-64 rounded-2xl border border-line bg-white shadow-xl overflow-hidden">

              {/* MENU HEADER */}

              <div className="px-4 py-3 border-b border-line">

                <p className="text-sm font-semibold text-ink">
                  Add to chat
                </p>

                <p className="text-xs text-muted mt-1">
                  Choose a file type
                </p>

              </div>

              {/* ==================================================
                  PHOTO
              ================================================== */}

              <button
                type="button"
                onClick={() =>
                  chooseFile("image/*")
                }
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-bgSoft text-left transition"
              >

                <div className="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                  <ImageIcon size={18} />
                </div>

                <div>
                  <p className="text-sm font-medium text-ink">
                    Photo
                  </p>

                  <p className="text-xs text-muted">
                    JPG, PNG, WEBP, GIF
                  </p>
                </div>

              </button>

              {/* ==================================================
                  DOCUMENT
              ================================================== */}

              <button
                type="button"
                onClick={() =>
                  chooseFile(
                    ".pdf,.doc,.docx,.txt,.csv,.xls,.xlsx,.ppt,.pptx"
                  )
                }
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-bgSoft text-left transition"
              >

                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <FileText size={18} />
                </div>

                <div>
                  <p className="text-sm font-medium text-ink">
                    Document
                  </p>

                  <p className="text-xs text-muted">
                    PDF, DOCX, TXT, XLSX
                  </p>
                </div>

              </button>

              {/* ==================================================
                  VIDEO
              ================================================== */}

              <button
                type="button"
                onClick={() =>
                  chooseFile("video/*")
                }
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-bgSoft text-left transition"
              >

                <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                  <Video size={18} />
                </div>

                <div>
                  <p className="text-sm font-medium text-ink">
                    Video
                  </p>

                  <p className="text-xs text-muted">
                    MP4, MOV, WEBM
                  </p>
                </div>

              </button>

              {/* ==================================================
                  OTHER FILES
              ================================================== */}

              <button
                type="button"
                onClick={() =>
                  chooseFile("*/*")
                }
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-bgSoft text-left transition"
              >

                <div className="w-9 h-9 rounded-xl bg-gray-100 text-gray-700 flex items-center justify-center shrink-0">
                  <FolderOpen size={18} />
                </div>

                <div>
                  <p className="text-sm font-medium text-ink">
                    Other files
                  </p>

                  <p className="text-xs text-muted">
                    Any supported file
                  </p>
                </div>

              </button>

            </div>
          </>
        )}

        {/* ==================================================
            SINGLE INPUT BAR
        ================================================== */}

        <div className="flex items-end gap-2 rounded-2xl border border-line bg-bgLight px-3 py-2">

          {/* ==================================================
              ATTACH BUTTON
          ================================================== */}

          <button
            type="button"
            onClick={() =>
              setMenuOpen(
                (old) => !old
              )
            }
            disabled={disabled}
            className="p-2 rounded-lg text-muted hover:text-ink hover:bg-white shrink-0 transition disabled:opacity-50"
            title="Attach file"
          >
            {menuOpen ? (
              <X size={19} />
            ) : (
              <Paperclip size={18} />
            )}
          </button>

          {/* ==================================================
              FILE INPUT
          ================================================== */}

          <input
            ref={fileInputRef}
            type="file"
            multiple
            hidden
            onChange={
              handleFileChange
            }
          />

          {/* ==================================================
              TEXT INPUT
          ================================================== */}

          <textarea
            value={text}
            onChange={(event) =>
              setText(
                event.target.value
              )
            }
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={disabled}
            placeholder="Ask A2Z Nexus anything..."
            className="flex-1 resize-none bg-transparent text-sm text-ink placeholder:text-muted focus:outline-none py-1.5 min-h-[32px] max-h-32 disabled:opacity-60"
          />

          {/* ==================================================
              VOICE
          ================================================== */}

          <button
            type="button"
            onClick={toggleVoice}
            disabled={disabled}
            className={`p-2 rounded-lg shrink-0 transition ${
              listening
                ? "text-red-500 bg-red-50"
                : "text-muted hover:text-ink hover:bg-white"
            } disabled:opacity-50`}
            title={
              listening
                ? "Stop listening"
                : "Voice Agent"
            }
          >
            {listening ? (
              <Square size={18} />
            ) : (
              <Mic size={18} />
            )}
          </button>

          {/* ==================================================
              SEND
          ================================================== */}

          <button
            type="button"
            onClick={sendMessage}
            disabled={!canSend}
            className={`p-2 rounded-lg shrink-0 transition-all ${
              canSend
                ? "bg-primary text-white hover:bg-primary/90 cursor-pointer"
                : "bg-primary/40 text-white cursor-not-allowed"
            }`}
            title="Send message"
          >
            <ArrowUp size={18} />
          </button>

        </div>

      </div>

    </div>
  );
}