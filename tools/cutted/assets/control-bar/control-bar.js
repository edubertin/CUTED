(function registerCutedControlBar(global) {
  const DEFAULT_STATE = {
    aiStatus: "idle",
    captionMode: "off",
    captionsEnabled: false,
    captionMenuOpen: false,
    captionPaletteOpen: null,
    captionStyle: { size: 72, width: 28, bottom: 16, mode: "off", textColor: "#ffffff", backgroundColor: "transparent" },
    effectMenuOpen: false,
    effectStyle: "clean",
    formatMenuOpen: false,
    insertMenuOpen: false,
    volumeMenuOpen: false,
    aspectRatio: "9:16",
    bumpers: { intro: null, outro: null },
    busy: false,
    clipInfo: { rank: "", title: "", summary: "" },
    muted: false,
    ready: false,
    discarded: false,
    renderQueued: false,
    status: null,
    trimApplied: false,
    trimMode: false,
    volume: 75
  };

  const FORMAT_OPTIONS = [
    { value: "9:16", title: "Vertical", meta: "TikTok / Reels / Shorts", icon: "vertical" },
    { value: "4:5", title: "Feed", meta: "Facebook 1080x1350", icon: "feed" },
    { value: "16:9", title: "Wide", meta: "YouTube 1920x1080", icon: "wide" }
  ];

  function createCutedControlBar(container, options = {}) {
    if (!container) {
      throw new Error("createCutedControlBar requires a container.");
    }

    const callbacks = readCallbacks(options);
    const settings = {
      mockBumpers: options.mockBumpers !== false
    };
    const state = normalizeState({ ...DEFAULT_STATE, ...options });
    const statusClock = { id: null };
    const subscribers = new Set();
    reconcileReadyStatus(state);

    container.innerHTML = renderControlBar();
    const elements = readElements(container);
    const teardown = bindEvents(container, elements, state, callbacks, settings, statusClock, subscribers);
    syncView(elements, state);

    return {
      destroy() {
        window.clearTimeout(statusClock.id);
        teardown();
        subscribers.clear();
        container.innerHTML = "";
      },
      getState() {
        return snapshotState(state);
      },
      subscribe(listener) {
        if (typeof listener !== "function") return () => {};
        subscribers.add(listener);
        return () => subscribers.delete(listener);
      },
      update(nextState) {
        const hasIncomingStatus = Object.prototype.hasOwnProperty.call(nextState || {}, "status");
        const incomingStatus = hasIncomingStatus ? normalizeStatus(nextState.status) : state.status;
        const incomingBumpers = normalizeBumpers(nextState?.bumpers);
        const insertedSlot = state.insertMenuOpen ? ["intro", "outro"].find((slot) => !state.bumpers[slot] && incomingBumpers[slot]) : null;
        const keepTimedStatus = state.status && !state.status.persistent && statusClock.id;
        const keepMenuStatus = state.status?.persistent && (
          (state.captionMenuOpen && state.status.kind === "caption") ||
          (state.effectMenuOpen && state.status.kind === "effect") ||
          (state.insertMenuOpen && state.status.kind === "insert")
        );
        const keepLocalStatus = hasIncomingStatus && !incomingStatus && !insertedSlot && (keepTimedStatus || keepMenuStatus);
        if (hasIncomingStatus && !keepLocalStatus) {
          window.clearTimeout(statusClock.id);
        }
        const normalizedNext = normalizeState({ ...state, ...nextState });
        if (insertedSlot && !incomingStatus) {
          const label = insertedSlot === "intro" ? "Start video inserted" : "End video inserted";
          normalizedNext.status = { kind: "insert", label, persistent: true, progress: null, tone: "green" };
        }
        if (keepLocalStatus) normalizedNext.status = state.status;
        Object.assign(state, normalizedNext);
        reconcileReadyStatus(state);
        syncView(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
      },
      setStatus(status, holdMs = 0) {
        window.clearTimeout(statusClock.id);
        state.status = normalizeStatus(status);
        syncView(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
        if (!state.status || state.status.persistent || holdMs <= 0) return;
        statusClock.id = window.setTimeout(() => {
          state.status = null;
          syncView(elements, state);
          emitStateChange(container, callbacks, subscribers, state);
        }, holdMs);
      },
      clearStatus() {
        window.clearTimeout(statusClock.id);
        state.status = null;
        syncView(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
      },
      setReady(ready = true) {
        state.ready = Boolean(ready);
        if (state.ready) state.discarded = false;
        reconcileReadyStatus(state);
        syncView(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
      },
      setDiscarded(discarded = true) {
        state.discarded = Boolean(discarded);
        if (state.discarded) state.ready = false;
        reconcileReadyStatus(state);
        syncView(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
      },
      reset(nextState = {}) {
        window.clearTimeout(statusClock.id);
        Object.assign(state, normalizeState({ ...DEFAULT_STATE, ...nextState }));
        reconcileReadyStatus(state);
        syncView(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
      }
    };
  }

  function readCallbacks(options) {
    const nested = options.callbacks && typeof options.callbacks === "object" ? options.callbacks : {};
    return {
      onAiClick: options.onAiClick || nested.onAiClick,
      onAiStatusChange: options.onAiStatusChange || nested.onAiStatusChange,
      onApproveClick: options.onApproveClick || nested.onApproveClick,
      onCaptionToggle: options.onCaptionToggle || nested.onCaptionToggle,
      onCaptionStyleChange: options.onCaptionStyleChange || nested.onCaptionStyleChange,
      onDiscardClick: options.onDiscardClick || nested.onDiscardClick,
      onEffectClick: options.onEffectClick || nested.onEffectClick,
      onEffectStyleChange: options.onEffectStyleChange || nested.onEffectStyleChange,
      onFormatChange: options.onFormatChange || nested.onFormatChange,
      onBumperClick: options.onBumperClick || nested.onBumperClick,
      onBumperRemove: options.onBumperRemove || nested.onBumperRemove,
      onBumperChange: options.onBumperChange || nested.onBumperChange,
      onInsertClick: options.onInsertClick || nested.onInsertClick,
      onStateChange: options.onStateChange || nested.onStateChange,
      onReadyCancel: options.onReadyCancel || nested.onReadyCancel,
      onSendRender: options.onSendRender || nested.onSendRender,
      onTrimConfirm: options.onTrimConfirm || nested.onTrimConfirm,
      onTrimToggle: options.onTrimToggle || nested.onTrimToggle,
      onVolumeChange: options.onVolumeChange || nested.onVolumeChange
    };
  }

  function emitStateChange(container, callbacks, subscribers, state) {
    const snapshot = snapshotState(state);
    callbacks.onStateChange?.(snapshot);
    subscribers.forEach((listener) => listener(snapshot));
    container.dispatchEvent(new CustomEvent("cuted-control-bar:statechange", {
      bubbles: true,
      detail: snapshot
    }));
  }

  function normalizeState(state) {
    const effectStyle = ["clean", "vhs", "film", "grain"].includes(state.effectStyle) ? state.effectStyle : "clean";
    const aiStatus = ["idle", "loading", "active"].includes(state.aiStatus) ? state.aiStatus : "idle";
    const captionMode = normalizeCaptionMode(state.captionMode || state.captionStyle?.mode || (state.captionsEnabled ? "on" : "off"));

    return {
      aiStatus,
      busy: Boolean(state.busy),
      captionMode,
      captionsEnabled: captionMode !== "off",
      captionMenuOpen: Boolean(state.captionMenuOpen),
      captionPaletteOpen: ["text", "background"].includes(state.captionPaletteOpen) ? state.captionPaletteOpen : null,
      captionStyle: normalizeCaptionStyle({ ...state.captionStyle, mode: captionMode }),
      effectMenuOpen: Boolean(state.effectMenuOpen),
      effectStyle,
      formatMenuOpen: Boolean(state.formatMenuOpen),
      insertMenuOpen: Boolean(state.insertMenuOpen),
      volumeMenuOpen: Boolean(state.volumeMenuOpen),
      aspectRatio: FORMAT_OPTIONS.some((option) => option.value === state.aspectRatio) ? state.aspectRatio : "9:16",
      bumpers: normalizeBumpers(state.bumpers),
      clipInfo: normalizeClipInfo(state.clipInfo),
      muted: Boolean(state.muted),
      ready: Boolean(state.ready),
      discarded: Boolean(state.discarded),
      renderQueued: Boolean(state.renderQueued),
      status: normalizeStatus(state.status),
      trimApplied: Boolean(state.trimApplied),
      trimMode: Boolean(state.trimMode),
      volume: clamp(Number(state.volume), 0, 100)
    };
  }

  function normalizeStatus(value) {
    if (!value || typeof value !== "object") return null;
    const tone = ["blue", "green", "red", "neutral"].includes(value.tone) ? value.tone : "neutral";
    const progress = Number(value.progress);
    return {
      kind: String(value.kind || "idle"),
      label: String(value.label || ""),
      progress: Number.isFinite(progress) ? clamp(progress, 0, 100) : null,
      persistent: Boolean(value.persistent),
      tone
    };
  }

  function normalizeClipInfo(value) {
    const input = value && typeof value === "object" ? value : {};
    return {
      rank: String(input.rank || "").trim(),
      title: String(input.title || "").trim(),
      summary: String(input.summary || "").trim()
    };
  }

  function normalizeCaptionStyle(value) {
    const input = value && typeof value === "object" ? value : {};
    const mode = normalizeCaptionMode(input.mode || input.captionMode);
    return {
      size: clamp(Number(input.size || 72), 24, 140),
      width: clamp(Number(input.width || 28), 12, 56),
      bottom: clamp(Number(input.bottom || input.height || 16), 6, 32),
      mode,
      textColor: normalizeHexColor(input.textColor, "#ffffff"),
      backgroundColor: normalizeCaptionBackground(input.backgroundColor)
    };
  }

  function normalizeCaptionMode(value) {
    const mode = String(value || "").trim().toLowerCase();
    if (mode === "animated" || mode === "animada") return "animated";
    if (mode === "on" || mode === "static") return "on";
    return "off";
  }

  function normalizeCaptionBackground(value) {
    const raw = String(value || "").trim().toLowerCase();
    if (!raw || raw === "transparent" || raw === "none") return "transparent";
    return normalizeHexColor(raw, "#000000");
  }

  function normalizeHexColor(value, fallback) {
    const raw = String(value || "").trim();
    return /^#[0-9a-f]{6}$/i.test(raw) ? raw.toLowerCase() : fallback;
  }

  function readElements(container) {
    return {
      aiButton: container.querySelector("[data-cuted-control='ai']"),
      approveButton: container.querySelector("[data-cuted-control='approve']"),
      captionButton: container.querySelector("[data-cuted-control='caption']"),
      captionMenu: container.querySelector("[data-cuted-caption-menu]"),
      captionToggle: container.querySelector("[data-cuted-caption-toggle]"),
      captionModeButtons: Array.from(container.querySelectorAll("[data-cuted-caption-mode]")),
      captionOkButton: container.querySelector("[data-cuted-caption-ok]"),
      captionBottomInput: container.querySelector("[data-cuted-caption-bottom]"),
      captionSizeInput: container.querySelector("[data-cuted-caption-size]"),
      captionWidthInput: container.querySelector("[data-cuted-caption-width]"),
      captionSteps: Array.from(container.querySelectorAll("[data-cuted-caption-step]")),
      captionPalette: container.querySelector("[data-cuted-caption-palette]"),
      captionPickers: Array.from(container.querySelectorAll("[data-cuted-caption-picker]")),
      captionSwatches: Array.from(container.querySelectorAll("[data-cuted-caption-swatch]")),
      clipInfo: container.querySelector("[data-cuted-clip-info]"),
      clipRank: container.querySelector("[data-cuted-clip-rank]"),
      clipSummary: container.querySelector("[data-cuted-clip-summary]"),
      clipTitle: container.querySelector("[data-cuted-clip-title]"),
      discardButton: container.querySelector("[data-cuted-control='discard']"),
      effectButton: container.querySelector("[data-cuted-control='effect']"),
      effectMenu: container.querySelector("[data-cuted-effect-menu]"),
      effectOptions: Array.from(container.querySelectorAll("[data-cuted-effect-style]")),
      formatButton: container.querySelector("[data-cuted-control='format']"),
      formatIcon: container.querySelector("[data-cuted-format-icon]"),
      formatLabel: container.querySelector("[data-cuted-format-label]"),
      formatMenu: container.querySelector("[data-cuted-format-menu]"),
      formatOptions: Array.from(container.querySelectorAll("[data-cuted-format]")),
      formatTitle: container.querySelector("[data-cuted-format-title]"),
      bumperButtons: Array.from(container.querySelectorAll("[data-cuted-bumper-slot]")),
      bumperRemoves: Array.from(container.querySelectorAll("[data-cuted-bumper-remove]")),
      controlBar: container.querySelector("[data-cuted-control-bar]"),
      insertButton: container.querySelector("[data-cuted-control='insert']"),
      insertDots: Array.from(container.querySelectorAll("[data-cuted-insert-dot]")),
      insertExitButton: container.querySelector("[data-cuted-insert-exit]"),
      insertMenu: container.querySelector("[data-cuted-insert-menu]"),
      readyCancelButton: container.querySelector("[data-cuted-control='ready-cancel']"),
      renderZone: container.querySelector("[data-cuted-render-zone]"),
      sonicRail: container.querySelector("[data-cuted-sonic-rail]"),
      soundButton: container.querySelector("[data-cuted-control='sound']"),
      toolGroup: container.querySelector("[data-cuted-tool-group]"),
      trimButton: container.querySelector("[data-cuted-control='trim']"),
      statusBar: container.querySelector("[data-cuted-bar-status]"),
      statusAction: container.querySelector("[data-cuted-status-action]"),
      statusLabel: container.querySelector("[data-cuted-status-label]"),
      statusMeter: container.querySelector("[data-cuted-status-meter]"),
      volumeMuteButton: container.querySelector("[data-cuted-control='volume-mute']"),
      volumePopover: container.querySelector("[data-cuted-volume-popover]"),
      volumeSlider: container.querySelector("[data-cuted-control='volume']"),
      volumeValue: container.querySelector("[data-cuted-value='volume']")
    };
  }

  function bindEvents(container, elements, state, callbacks, settings, statusClock, subscribers) {
    const setStatus = (status, holdMs = 2600) => {
      window.clearTimeout(statusClock.id);
      state.status = normalizeStatus(status);
      syncStatus(elements, state);
      emitStateChange(container, callbacks, subscribers, state);
      if (!state.status || state.status.persistent || holdMs <= 0) return;
      statusClock.id = window.setTimeout(() => {
        state.status = null;
        syncStatus(elements, state);
        emitStateChange(container, callbacks, subscribers, state);
      }, holdMs);
    };
    const sync = () => {
      syncView(elements, state);
      emitStateChange(container, callbacks, subscribers, state);
    };
    const emitCaptionChange = () => {
      const payload = { captionMode: state.captionMode, captionsEnabled: state.captionsEnabled, captionStyle: { ...state.captionStyle, mode: state.captionMode } };
      callbacks.onCaptionToggle?.(payload);
      callbacks.onCaptionStyleChange?.(payload);
    };
    const updateCaptionStyle = (nextStyle, label) => {
      state.captionStyle = normalizeCaptionStyle({ ...state.captionStyle, ...nextStyle });
      setCaptionStatus(label);
      sync();
      emitCaptionChange();
    };
    const setCaptionStatus = (label, tone = "blue") => {
      setStatus({ kind: "caption", label, tone, persistent: state.captionMenuOpen }, state.captionMenuOpen ? 0 : undefined);
    };
    const closeCaptionPalette = () => {
      state.captionPaletteOpen = null;
    };
    const setInsertStatus = (label, tone = "blue") => {
      setStatus({ kind: "insert", label, tone, persistent: state.insertMenuOpen }, state.insertMenuOpen ? 0 : undefined);
    };
    const closeMenus = () => {
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      sync();
    };
    const closeToolModes = () => {
      const wasTrimMode = state.trimMode;
      state.trimMode = false;
      if (wasTrimMode) callbacks.onTrimToggle?.({ trimMode: false });
    };
    const restoreTrimStatus = () => {
      if (!state.trimMode) return false;
      window.clearTimeout(statusClock.id);
      state.status = buildTrimStatus();
      sync();
      return true;
    };
    const confirmTrimMode = () => {
      if (!state.trimMode) return false;
      window.clearTimeout(statusClock.id);
      state.trimMode = false;
      state.status = null;
      callbacks.onTrimToggle?.({ trimMode: false });
      sync();
      callbacks.onTrimConfirm?.(snapshotState(state));
      return true;
    };
    const isLocked = () => state.ready || state.discarded || state.busy;
    const lockReady = () => {
      state.ready = true;
      state.discarded = false;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      closeToolModes();
      setStatus(buildReadyStatus(), 0);
      sync();
    };
    const lockDiscarded = () => {
      state.ready = false;
      state.discarded = true;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      closeToolModes();
      setStatus(buildDiscardedStatus(), 0);
      sync();
    };
    const dismissClick = (event) => {
      if (container.contains(event.target)) return;
      if (state.captionMenuOpen || state.effectMenuOpen || state.insertMenuOpen) return;
      closeMenus();
    };
    const dismissKey = (event) => {
      if (state.captionMenuOpen || state.effectMenuOpen || state.insertMenuOpen) return;
      if (event.key === "Escape") closeMenus();
    };

    document.addEventListener("click", dismissClick, true);
    document.addEventListener("keydown", dismissKey);

    elements.volumeSlider.addEventListener("input", () => {
      if (isLocked()) return;
      state.volume = Number(elements.volumeSlider.value);
      state.muted = state.volume === 0;
      sync();
      callbacks.onVolumeChange?.({ muted: state.muted, volume: state.volume });
    });

    elements.soundButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      state.volumeMenuOpen = !state.volumeMenuOpen;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      sync();
    });

    elements.volumeMuteButton.addEventListener("click", () => {
      if (isLocked()) return;
      state.muted = !state.muted;
      state.volume = state.muted ? 0 : Math.max(state.volume, 75);
      sync();
      callbacks.onVolumeChange?.({ muted: state.muted, volume: state.volume });
    });

    elements.aiButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      closeToolModes();
      state.volumeMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      if (state.aiStatus === "active") {
        setStatus({ kind: "ai", label: "AI camera already exists", tone: "blue" }, 1500);
        sync();
        return;
      }
      callbacks.onAiClick?.({ ...state });
      if (state.aiStatus === "idle") {
        state.aiStatus = "loading";
        setStatus({ kind: "ai", label: "AI analyzing frame safety...", progress: 42, tone: "blue" });
        sync();
        callbacks.onAiStatusChange?.({ aiStatus: state.aiStatus });
        window.setTimeout(() => {
          if (isLocked()) return;
          state.aiStatus = "active";
          setStatus({ kind: "ai", label: "AI ready for this cut", tone: "blue" });
          sync();
          callbacks.onAiStatusChange?.({ aiStatus: state.aiStatus });
        }, 1400);
      }
    });

    elements.effectButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      closeToolModes();
      state.effectMenuOpen = true;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      setStatus({
        kind: "effect",
        label: "FX",
        persistent: true,
        tone: "green"
      }, 0);
      sync();
      callbacks.onEffectClick?.({ effectMenuOpen: state.effectMenuOpen, effectStyle: state.effectStyle });
    });

    elements.effectOptions.forEach((button) => {
      button.addEventListener("click", () => {
        if (isLocked()) return;
        closeToolModes();
        state.effectStyle = button.dataset.cutedEffectStyle;
        state.effectMenuOpen = false;
        state.captionMenuOpen = false;
        closeCaptionPalette();
        state.volumeMenuOpen = false;
        setStatus({ kind: "effect", label: `FX ${button.textContent.trim()}`, tone: "green" }, 1700);
        sync();
        callbacks.onEffectStyleChange?.({ effectStyle: state.effectStyle });
      });
    });

    elements.captionButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      state.captionMenuOpen = true;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.volumeMenuOpen = false;
      setCaptionStatus("Closed caption");
      sync();
    });
    elements.captionToggle.addEventListener("click", (event) => {
      if (isLocked()) return;
      const modeButton = event.target instanceof Element ? event.target.closest("[data-cuted-caption-mode]") : null;
      const fallbackMode = state.captionMode === "off" ? "on" : state.captionMode === "on" ? "animated" : "off";
      const mode = normalizeCaptionMode(modeButton?.dataset.cutedCaptionMode || fallbackMode);
      state.captionMode = mode;
      state.captionsEnabled = mode !== "off";
      state.captionStyle = normalizeCaptionStyle({ ...state.captionStyle, mode });
      setCaptionStatus(captionModeLabel(mode), mode === "off" ? "neutral" : "blue");
      sync();
      emitCaptionChange();
    });
    elements.captionOkButton.addEventListener("click", () => {
      if (isLocked()) return;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      setStatus({ kind: "caption", label: "Caption saved", tone: "neutral" }, 1200);
      sync();
    });
    elements.captionSteps.forEach((button) => {
      button.addEventListener("click", () => {
        if (isLocked()) return;
        const key = ["bottom", "width"].includes(button.dataset.cutedCaptionStep) ? button.dataset.cutedCaptionStep : "size";
        const direction = Number(button.dataset.cutedCaptionDirection || 0);
        const current = key === "bottom" ? state.captionStyle.bottom : key === "width" ? state.captionStyle.width : state.captionStyle.size;
        const step = key === "size" ? 2 : 1;
        const next = current + (direction * step);
        updateCaptionStyle({ [key]: next }, captionStepLabel(key, next));
      });
    });
    [["size", elements.captionSizeInput], ["width", elements.captionWidthInput], ["bottom", elements.captionBottomInput]].forEach(([key, input]) => {
      input.addEventListener("change", () => {
        if (isLocked()) return;
        updateCaptionStyle({ [key]: Number(input.value) }, captionStepLabel(key, input.value));
      });
    });
    elements.captionPickers.forEach((picker) => {
      picker.addEventListener("click", () => {
        if (isLocked()) return;
        const target = picker.dataset.cutedCaptionPicker === "background" ? "background" : "text";
        state.captionPaletteOpen = state.captionPaletteOpen === target ? null : target;
        setCaptionStatus(target === "background" ? "Background palette" : "Text palette");
        sync();
      });
    });
    elements.captionSwatches.forEach((button) => {
      button.addEventListener("click", () => {
        if (isLocked()) return;
        const key = state.captionPaletteOpen === "background" ? "backgroundColor" : "textColor";
        const value = button.dataset.cutedCaptionValue || "transparent";
        updateCaptionStyle({ [key]: value }, key === "backgroundColor" ? "Background color" : "Text color");
      });
    });
    elements.approveButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      lockReady();
      callbacks.onApproveClick?.(snapshotState(state));
    });
    elements.discardButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      lockDiscarded();
      callbacks.onDiscardClick?.(snapshotState(state));
    });
    elements.readyCancelButton.addEventListener("click", () => {
      state.ready = false;
      state.discarded = false;
      state.renderQueued = false;
      closeToolModes();
      setStatus({ kind: "editing", label: "Back to editing", tone: "neutral" }, 1800);
      sync();
      callbacks.onReadyCancel?.(snapshotState(state));
    });

    elements.statusAction.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (state.trimMode) {
        if (event.target instanceof Element && event.target.closest(".cuted-trim-status-confirm")) {
          confirmTrimMode();
        } else {
          restoreTrimStatus();
        }
        return;
      }
      if (!state.ready || state.discarded || state.busy || state.renderQueued) return;
      state.renderQueued = true;
      state.ready = false;
      closeToolModes();
      setStatus({ kind: "render", label: "SENT TO RENDER", tone: "green" }, 1400);
      sync();
      callbacks.onSendRender?.(snapshotState(state));
    });

    elements.statusAction.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      if (!state.trimMode && (!state.ready || state.discarded || state.busy || state.renderQueued)) return;
      event.preventDefault();
      event.stopPropagation();
      elements.statusAction.click();
    });

    elements.formatButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      state.formatMenuOpen = !state.formatMenuOpen;
      state.effectMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      setStatus({ kind: "format", label: state.formatMenuOpen ? "Choose output format" : "Format menu closed", tone: "blue" });
      sync();
    });

    elements.formatOptions.forEach((button) => {
      button.addEventListener("click", () => {
        if (isLocked()) return;
        state.aspectRatio = button.dataset.cutedFormat;
        state.formatMenuOpen = false;
        state.captionMenuOpen = false;
        closeCaptionPalette();
        state.volumeMenuOpen = false;
        setStatus({ kind: "format", label: `Format selected: ${state.aspectRatio}`, tone: "blue" });
        sync();
        callbacks.onFormatChange?.({ aspectRatio: state.aspectRatio });
      });
    });

    elements.insertButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (restoreTrimStatus()) return;
      closeToolModes();
      state.insertMenuOpen = true;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      setInsertStatus("Insert");
      sync();
      callbacks.onInsertClick?.({ insertMenuOpen: state.insertMenuOpen, bumpers: { ...state.bumpers } });
    });
    elements.insertExitButton.addEventListener("click", () => {
      if (isLocked()) return;
      state.insertMenuOpen = false;
      setStatus({ kind: "insert", label: "Insert closed", tone: "neutral" }, 900);
      sync();
    });

    elements.trimButton.addEventListener("click", () => {
      if (isLocked()) return;
      if (state.trimMode) {
        restoreTrimStatus();
        return;
      }
      state.trimMode = true;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      closeCaptionPalette();
      state.volumeMenuOpen = false;
      setStatus(buildTrimStatus(), 0);
      sync();
      callbacks.onTrimToggle?.({ trimMode: true });
    });

    elements.bumperButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (isLocked()) return;
        const slot = button.dataset.cutedBumperSlot;
        if (!state.bumpers[slot] && settings.mockBumpers) {
          state.bumpers[slot] = mockBumper(slot);
        }
        const label = slot === "intro" ? "Start" : "End";
        setInsertStatus(state.bumpers[slot] ? `${label} video inserted` : `Choose ${label} video`, state.bumpers[slot] ? "green" : "blue");
        sync();
        callbacks.onBumperClick?.({ slot, bumper: state.bumpers[slot] });
        callbacks.onBumperChange?.({ bumpers: { ...state.bumpers } });
      });
    });

    elements.bumperRemoves.forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        if (isLocked()) return;
        const slot = button.dataset.cutedBumperRemove;
        state.bumpers[slot] = null;
        setInsertStatus(`${slot === "intro" ? "Start" : "End"} video removed`, "red");
        sync();
        callbacks.onBumperRemove?.({ slot });
        callbacks.onBumperChange?.({ bumpers: { ...state.bumpers } });
      });
    });

    return () => {
      window.clearTimeout(statusClock.id);
      document.removeEventListener("click", dismissClick, true);
      document.removeEventListener("keydown", dismissKey);
    };
  }

  function syncView(elements, state) {
    const locked = state.ready || state.discarded || state.busy;
    elements.controlBar.classList.toggle("is-busy", state.busy);
    elements.controlBar.classList.toggle("is-ready", state.ready);
    elements.controlBar.classList.toggle("is-discarded", state.discarded);
    elements.controlBar.classList.toggle("is-locked", locked);
    elements.renderZone.classList.toggle("is-ready", state.ready);
    elements.renderZone.classList.toggle("is-discarded", state.discarded);
    elements.renderZone.classList.toggle("is-locked", locked);
    elements.soundButton.classList.toggle("is-muted", state.muted);
    elements.soundButton.classList.toggle("is-active", state.volumeMenuOpen);
    elements.soundButton.setAttribute("aria-expanded", String(state.volumeMenuOpen));
    elements.volumePopover.dataset.open = String(state.volumeMenuOpen);
    elements.sonicRail.classList.toggle("is-muted", state.muted);
    elements.volumeMuteButton.classList.toggle("is-muted", state.muted);
    elements.volumeMuteButton.textContent = state.muted ? "Unmute" : "Mute";
    elements.sonicRail.style.setProperty("--volume", `${state.volume}%`);
    elements.sonicRail.style.setProperty("--volume-num", String(state.volume / 100));
    elements.volumeSlider.value = String(state.volume);
    elements.volumeValue.textContent = `${state.volume}%`;
    syncClipInfo(elements, state);
    elements.aiButton.dataset.aiStatus = state.aiStatus;
    elements.aiButton.classList.toggle("is-loading", state.aiStatus === "loading");
    elements.aiButton.classList.toggle("is-active", state.aiStatus === "loading" || state.aiStatus === "active");
    if (locked) {
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      state.captionMenuOpen = false;
      state.volumeMenuOpen = false;
      state.trimMode = false;
    }
    elements.trimButton.classList.toggle("is-active", state.trimMode || state.trimApplied);
    elements.trimButton.classList.toggle("is-trim-applied", !state.trimMode && state.trimApplied);
    elements.trimButton.setAttribute("aria-pressed", String(state.trimMode));
    elements.captionButton.classList.toggle("is-active", state.captionsEnabled);
    elements.captionButton.classList.toggle("is-menu-open", state.captionMenuOpen);
    elements.captionButton.setAttribute("aria-expanded", String(state.captionMenuOpen));
    syncCaptionMenu(elements, state);
    elements.effectButton.classList.toggle("is-active", true);
    elements.effectMenu.dataset.open = String(state.effectMenuOpen);
    syncInsert(elements, state);
    syncStatus(elements, state);
    elements.approveButton.closest("[data-cuted-ready-region]").dataset.ready = String(state.ready || state.discarded);

    elements.effectOptions.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.cutedEffectStyle === state.effectStyle);
    });

    const selectedFormat = FORMAT_OPTIONS.find((option) => option.value === state.aspectRatio) ?? FORMAT_OPTIONS[0];
    elements.formatLabel.textContent = selectedFormat.value;
    elements.formatTitle.textContent = selectedFormat.title;
    elements.formatIcon.className = `cuted-ratio-icon cuted-ratio-${selectedFormat.icon}`;
    elements.formatButton.classList.toggle("is-active", state.formatMenuOpen);
    elements.formatMenu.dataset.open = String(state.formatMenuOpen);

    elements.formatOptions.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.cutedFormat === state.aspectRatio);
    });
  }

  function syncCaptionMenu(elements, state) {
    elements.captionMenu.dataset.open = String(state.captionMenuOpen);
    elements.captionToggle.dataset.mode = state.captionMode;
    elements.captionToggle.classList.toggle("is-on", state.captionsEnabled);
    elements.captionToggle.setAttribute("aria-pressed", String(state.captionsEnabled));
    elements.captionModeButtons.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.cutedCaptionMode === state.captionMode);
      button.setAttribute("aria-pressed", String(button.dataset.cutedCaptionMode === state.captionMode));
    });
    elements.captionSizeInput.value = String(Math.round(state.captionStyle.size));
    elements.captionWidthInput.value = String(Math.round(state.captionStyle.width));
    elements.captionBottomInput.value = String(Math.round(state.captionStyle.bottom));
    elements.captionPickers.forEach((picker) => {
      const key = picker.dataset.cutedCaptionPicker === "background" ? "backgroundColor" : "textColor";
      const value = state.captionStyle[key];
      picker.style.setProperty("--caption-picker-color", value === "transparent" ? "transparent" : value);
      picker.dataset.transparent = String(value === "transparent");
      picker.classList.toggle("is-active", state.captionPaletteOpen === picker.dataset.cutedCaptionPicker);
    });
    elements.captionPalette.dataset.open = String(Boolean(state.captionPaletteOpen));
    elements.captionPalette.dataset.kind = state.captionPaletteOpen || "text";
    elements.captionSwatches.forEach((button) => {
      const isTransparent = button.dataset.cutedCaptionValue === "transparent";
      const key = state.captionPaletteOpen === "background" ? "backgroundColor" : "textColor";
      button.hidden = !state.captionPaletteOpen || (state.captionPaletteOpen === "text" && isTransparent);
      button.classList.toggle("is-active", button.dataset.cutedCaptionValue === state.captionStyle[key]);
    });
  }

  function syncClipInfo(elements, state) {
    const hasInfo = Boolean(state.clipInfo.rank || state.clipInfo.title || state.clipInfo.summary);
    elements.clipInfo.hidden = !hasInfo;
    elements.clipRank.textContent = state.clipInfo.rank;
    elements.clipTitle.textContent = state.clipInfo.title;
    elements.clipSummary.textContent = state.clipInfo.summary;
  }

  function captionModeLabel(mode) {
    if (mode === "animated") return "Caption animated";
    if (mode === "on") return "Caption ON";
    return "Caption OFF";
  }

  function captionStepLabel(key, value) {
    if (key === "bottom") return `Height ${Math.round(Number(value) || 0)}%`;
    return key === "width" ? `Width ${Math.round(Number(value) || 0)}` : `Size ${Math.round(Number(value) || 0)}`;
  }

  function syncStatus(elements, state) {
    const transientStatus = state.status && !state.status.persistent ? state.status : null;
    const status = state.trimMode ? buildTrimStatus() : state.discarded ? buildDiscardedStatus() : transientStatus || (state.ready ? buildReadyStatus() : state.status);
    const hasStatus = Boolean(status && status.label);
    const statusIsTransient = !state.trimMode && Boolean(transientStatus);
    window.clearTimeout(elements.statusBar._cutedHideTimer);
    elements.controlBar.classList.toggle("has-status", hasStatus);
    elements.controlBar.classList.toggle("is-status-transient", statusIsTransient);
    elements.controlBar.dataset.statusKind = hasStatus ? status.kind : "idle";
    elements.controlBar.dataset.statusTone = hasStatus ? status.tone : "neutral";
    elements.toolGroup.classList.toggle("is-ready", state.ready);
    elements.toolGroup.classList.toggle("is-discarded", state.discarded);
    elements.readyCancelButton.setAttribute("aria-label", state.discarded ? "Restore cut" : "Back to editing");
    if (hasStatus) {
      elements.statusBar.hidden = false;
      elements.statusBar.classList.remove("is-hiding");
      elements.toolGroup.classList.add("is-status-active");
    } else if (!elements.statusBar.hidden) {
      elements.statusBar.classList.add("is-hiding");
      elements.toolGroup.classList.remove("is-status-active");
      elements.statusBar._cutedHideTimer = window.setTimeout(() => {
        elements.statusBar.hidden = true;
        elements.statusBar.classList.remove("is-hiding");
      }, 260);
    } else {
      elements.statusBar.hidden = true;
      elements.statusLabel.textContent = "";
      elements.statusMeter.style.setProperty("--status-progress", "0%");
      elements.controlBar.classList.remove("has-status");
      elements.controlBar.classList.remove("is-status-transient");
      elements.toolGroup.classList.remove("is-status-active");
    }
    elements.statusBar.dataset.tone = hasStatus ? status.tone : "neutral";
    elements.statusBar.dataset.kind = hasStatus ? status.kind : "idle";
    const canConfirmTrim = Boolean(state.trimMode && !state.discarded && !state.busy);
    const canSendRender = Boolean(state.ready && !state.discarded && !state.busy && !state.renderQueued && (!hasStatus || status.kind === "ready"));
    elements.statusBar.setAttribute("role", "status");
    elements.statusBar.removeAttribute("tabindex");
    elements.statusAction.setAttribute("role", canConfirmTrim || canSendRender ? "button" : "presentation");
    elements.statusAction.setAttribute("aria-label", canConfirmTrim ? "Confirmar trim" : canSendRender ? "Enviar para render" : status?.label || "Status");
    elements.statusAction.tabIndex = canConfirmTrim || canSendRender ? 0 : -1;
    if (hasStatus && (status.kind === "ready" || status.kind === "discarded")) {
      elements.statusLabel.innerHTML = renderReadyLetters(status.label);
    } else if (hasStatus && status.kind === "trim") {
      elements.statusLabel.innerHTML = renderTrimStatus();
    } else if (hasStatus) {
      elements.statusLabel.textContent = status.label;
    }
    const progress = hasStatus && status.progress !== null ? status.progress : 0;
    elements.statusMeter.style.setProperty("--status-progress", `${progress}%`);
    elements.statusMeter.hidden = !hasStatus || status.progress === null;
  }

  function renderControlBar() {
    return `
      <nav class="cuted-control-bar" aria-label="CUTED video controls" data-cuted-control-bar>
        <div class="cuted-effect-menu" data-open="false" data-cuted-effect-menu>
          <button class="cuted-look-option is-active" type="button" aria-label="Clean" data-cuted-effect-style="clean">
            <span class="cuted-look-preview cuted-clean-preview"></span>
            <strong>CLEAN</strong>
          </button>
          <button class="cuted-look-option" type="button" aria-label="VHS" data-cuted-effect-style="vhs">
            <span class="cuted-look-preview cuted-vhs-preview"></span>
            <strong>VHS</strong>
          </button>
          <button class="cuted-look-option" type="button" aria-label="Film" data-cuted-effect-style="film">
            <span class="cuted-look-preview cuted-film-preview"></span>
            <strong>FILM</strong>
          </button>
          <button class="cuted-look-option" type="button" aria-label="Grain" data-cuted-effect-style="grain">
            <span class="cuted-look-preview cuted-grain-preview"></span>
            <strong>GRAIN</strong>
          </button>
        </div>

        ${renderCaptionMenu()}

        <div class="cuted-bar-status-layer" data-kind="idle" data-tone="neutral" data-cuted-bar-status hidden>
          <span data-cuted-status-label data-cuted-status-action></span>
          <i data-cuted-status-meter></i>
        </div>

        <div class="cuted-clip-info" data-cuted-clip-info hidden>
          <span class="cuted-clip-rank" data-cuted-clip-rank></span>
          <span class="cuted-clip-copy">
            <strong data-cuted-clip-title></strong>
            <small data-cuted-clip-summary></small>
          </span>
        </div>

        <div class="cuted-control-group cuted-audio-group">
          <button class="cuted-icon-button cuted-sound-button" type="button" aria-label="Volume" aria-haspopup="true" aria-expanded="false" data-cuted-control="sound">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 9v6h4l5 4V5L8 9z"></path>
              <path class="cuted-volume-voice voice-one" d="M17 8a5 5 0 0 1 0 8"></path>
              <path class="cuted-volume-voice voice-two" d="M19.5 5.5a9 9 0 0 1 0 13"></path>
              <path class="cuted-volume-muted-mark" d="M15.4 9.6 21.4 15.6"></path>
              <path class="cuted-volume-muted-mark" d="m21.4 9.6-6 6"></path>
            </svg>
            <span class="cuted-sound-wave wave-one"></span>
            <span class="cuted-sound-wave wave-two"></span>
            <span class="cuted-sound-wave wave-three"></span>
          </button>
          <div class="cuted-volume-popover" data-open="false" data-cuted-volume-popover>
            <div class="cuted-volume-popover-head">
              <span>Volume</span>
              <button class="cuted-volume-mute-button" type="button" data-cuted-control="volume-mute">Mute</button>
            </div>
            <div class="cuted-sonic-rail" data-cuted-sonic-rail>
              <div class="cuted-sonic-fill"></div>
              <div class="cuted-sonic-bars" aria-hidden="true">
                ${renderSonicBars()}
              </div>
              <input class="cuted-volume-slider" type="range" min="0" max="100" value="75" aria-label="Volume" data-cuted-control="volume" />
            </div>
            <span class="cuted-volume-value" data-cuted-value="volume">75%</span>
          </div>
        </div>

        <div class="cuted-divider" aria-hidden="true"></div>

        <div class="cuted-control-group cuted-format-group" aria-label="Formato">
          ${renderFormatDropdown()}
        </div>

        <div class="cuted-divider" aria-hidden="true"></div>

        <div class="cuted-render-zone" data-cuted-render-zone>
          <div class="cuted-control-group cuted-tool-group" data-cuted-tool-group>
            <div class="cuted-tool-buttons">
              <button class="cuted-tile-button cuted-trim-button" type="button" aria-label="Trim" aria-pressed="false" data-cuted-control="trim">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle class="cuted-trim-ring cuted-trim-ring-top" cx="6.1" cy="6.8" r="2.55"></circle>
                  <circle class="cuted-trim-ring cuted-trim-ring-bottom" cx="6.1" cy="17.2" r="2.55"></circle>
                  <path class="cuted-trim-hinge" d="M8.5 12h3.2"></path>
                  <path class="cuted-trim-blade cuted-trim-blade-top" d="M8.3 8.5 19.3 4.2"></path>
                  <path class="cuted-trim-blade cuted-trim-blade-bottom" d="M8.3 15.5 19.3 19.8"></path>
                  <path class="cuted-trim-spark" d="M15.5 12h4.2"></path>
                </svg>
              </button>
              <button class="cuted-tile-button cuted-ai-button" type="button" aria-label="IA" data-cuted-control="ai">
                <span>IA</span>
                <i class="cuted-ai-loader" aria-hidden="true"></i>
              </button>
              <button class="cuted-tile-button cuted-fx-button is-active" type="button" aria-label="FX" data-cuted-control="effect">
                <span>FX</span>
              </button>
              <button class="cuted-tile-button cuted-insert-button" type="button" aria-label="Insert" data-cuted-control="insert">
                <span>INS</span>
                <i data-cuted-insert-dot="intro"></i>
                <i data-cuted-insert-dot="outro"></i>
              </button>
              <button class="cuted-tile-button cuted-cc-button" type="button" aria-label="Closed captions" data-cuted-control="caption">
                <span>CC</span>
              </button>
            </div>
          </div>

          <div class="cuted-divider cuted-ready-divider" aria-hidden="true"></div>

          <div class="cuted-ready-region" data-ready="false" data-cuted-ready-region>
            <div class="cuted-control-group cuted-action-group" aria-label="Acoes">
              <button class="cuted-action-button cuted-discard-button" type="button" aria-label="Descartar" data-cuted-control="discard">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M18 6 6 18"></path>
                  <path d="M6 6l12 12"></path>
                </svg>
              </button>
              <button class="cuted-action-button cuted-approve-button" type="button" aria-label="Aprovar" data-cuted-control="approve">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 6 9 17l-5-5"></path>
                </svg>
              </button>
            </div>
            <div class="cuted-ready-pill" aria-live="polite">
              <button class="cuted-ready-cancel" type="button" aria-label="Back to editing" data-cuted-control="ready-cancel">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M18 6 6 18"></path>
                  <path d="M6 6l12 12"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        ${renderInsertMenu()}
      </nav>
    `;
  }

  function renderFormatDropdown() {
    return `
      <div class="cuted-format-picker">
        <button class="cuted-format-trigger" type="button" aria-label="Formato" data-cuted-control="format">
          <span class="cuted-ratio-icon cuted-ratio-vertical" data-cuted-format-icon></span>
          <span class="cuted-format-copy">
            <strong data-cuted-format-label>9:16</strong>
            <small data-cuted-format-title>Vertical</small>
          </span>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m7 10 5 5 5-5"></path>
          </svg>
        </button>
        <div class="cuted-format-menu" data-open="false" data-cuted-format-menu>
          ${FORMAT_OPTIONS.map(renderFormatOption).join("")}
        </div>
      </div>
    `;
  }

  function renderInsertMenu() {
    return `
      <div class="cuted-insert-menu" data-open="false" data-cuted-insert-menu>
        <button class="cuted-insert-exit" type="button" data-cuted-insert-exit>Done</button>
        <div class="cuted-insert-options">
          ${renderBumperOption("intro", "Start", "Before cut")}
          ${renderBumperOption("outro", "End", "After cut")}
        </div>
      </div>
    `;
  }

  function renderCaptionMenu() {
    return `
      <div class="cuted-caption-menu" data-open="false" data-cuted-caption-menu>
        <div class="cuted-caption-menu-head">
          <div class="cuted-caption-switch" role="group" aria-label="Modo da legenda" data-mode="off" data-cuted-caption-toggle>
            <button type="button" aria-pressed="true" data-cuted-caption-mode="off">OFF</button>
            <button type="button" aria-pressed="false" data-cuted-caption-mode="on">ON</button>
            <button type="button" aria-pressed="false" data-cuted-caption-mode="animated">ANI</button>
          </div>
          <button class="cuted-caption-ok" type="button" data-cuted-caption-ok>OK</button>
        </div>
        <div class="cuted-caption-number-grid">
          ${renderCaptionStepper("size", "FONT", 72)}
          ${renderCaptionStepper("width", "WIDTH", 28)}
          ${renderCaptionStepper("bottom", "ALTURA", 16)}
        </div>
        <div class="cuted-caption-color-grid">
          ${renderCaptionColorPicker("text", "A", "#ffffff")}
          ${renderCaptionColorPicker("background", "BG", "#000000")}
        </div>
        ${renderCaptionPalette()}
      </div>
    `;
  }

  function renderCaptionStepper(key, label, value) {
    const min = key === "bottom" ? "6" : key === "width" ? "12" : "24";
    const max = key === "bottom" ? "32" : key === "width" ? "56" : "140";
    return `
      <label class="cuted-caption-stepper">
        <span>${label}</span>
        <span class="cuted-caption-stepper-row">
          <button type="button" aria-label="${label} menor" data-cuted-caption-step="${key}" data-cuted-caption-direction="-1">-</button>
          <input type="number" min="${min}" max="${max}" value="${value}" data-cuted-caption-${key} />
          <button type="button" aria-label="${label} maior" data-cuted-caption-step="${key}" data-cuted-caption-direction="1">+</button>
        </span>
      </label>
    `;
  }

  function renderCaptionColorPicker(kind, label, value) {
    return `
      <div class="cuted-caption-picker cuted-caption-picker-${kind}" data-cuted-caption-picker="${kind}" style="--caption-picker-color:${value}">
        <span>${label}</span>
        <i aria-hidden="true"></i>
      </div>
    `;
  }

  function renderCaptionPalette() {
    const colors = captionPaletteColors();
    return `
      <div class="cuted-caption-palette" data-open="false" data-kind="text" data-cuted-caption-palette>
        <div class="cuted-caption-palette-grid">
          ${renderCaptionSwatch("transparent")}
          ${colors.map(renderCaptionSwatch).join("")}
        </div>
      </div>
    `;
  }

  function captionPaletteColors() {
    return [
      "#ffffff", "#d7dde5", "#9aa4b2", "#111318",
      "#ffcc00", "#ff8a00", "#ef4444", "#ec4899",
      "#afcf2a", "#46d66f", "#11a2cf", "#2563eb",
      "#7c3aed", "#14b8a6", "#f5f0dc", "#8b5cf6",
      "#ffe066", "#fb7185", "#38bdf8", "#a3e635",
      "#0f172a", "#20242a", "#08212b", "#24330c",
      "#f97316", "#06b6d4", "#84cc16", "#e879f9"
    ];
  }

  function renderCaptionSwatch(color) {
    const isTransparent = color === "transparent";
    return `
      <button class="cuted-caption-swatch${isTransparent ? " is-transparent" : ""}" type="button" aria-label="${isTransparent ? "Transparente" : color}" data-cuted-caption-swatch data-cuted-caption-value="${color}" style="--swatch-color:${isTransparent ? "#000000" : color}"></button>
    `;
  }

  function renderBumperOption(slot, label, meta) {
    return `
      <button class="cuted-bumper-option" type="button" data-cuted-bumper-slot="${slot}">
        <span class="cuted-bumper-visual cuted-bumper-${slot}" aria-hidden="true">
          <i></i><b></b><i></i>
        </span>
        <span class="cuted-bumper-copy">
          <strong>${label}</strong>
          <small>${meta}</small>
          <em data-cuted-bumper-label="${slot}">Add MP4</em>
        </span>
        <span class="cuted-bumper-status" data-cuted-bumper-status="${slot}"></span>
        <span class="cuted-bumper-remove" data-cuted-bumper-remove="${slot}" aria-label="Remove ${label}">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M18 6 6 18"></path>
            <path d="M6 6l12 12"></path>
          </svg>
        </span>
      </button>
    `;
  }

  function renderFormatOption(option) {
    return `
      <button class="cuted-format-option" type="button" data-cuted-format="${option.value}">
        <span class="cuted-ratio-icon cuted-ratio-${option.icon}"></span>
        <span>
          <strong>${option.value}</strong>
          <small>${option.title}</small>
        </span>
        <em>${option.meta}</em>
      </button>
    `;
  }

  function renderSonicBars() {
    const heights = [34, 56, 42, 70, 38, 64, 48, 76, 44, 60, 36, 68, 52, 74, 40, 58, 46, 72];
    return heights.map((height, index) => `<i style="--h:${height}%; --d:${index * 54}ms"></i>`).join("");
  }

  function syncInsert(elements, state) {
    const hasIntro = Boolean(state.bumpers.intro);
    const hasOutro = Boolean(state.bumpers.outro);
    elements.insertButton.classList.toggle("is-active", state.insertMenuOpen || hasIntro || hasOutro);
    elements.insertMenu.dataset.open = String(state.insertMenuOpen);
    elements.insertDots.forEach((dot) => {
      const slot = dot.dataset.cutedInsertDot;
      dot.classList.toggle("is-active", Boolean(state.bumpers[slot]));
    });
    elements.bumperButtons.forEach((button) => {
      const slot = button.dataset.cutedBumperSlot;
      const bumper = state.bumpers[slot];
      button.classList.toggle("is-attached", Boolean(bumper));
      button.querySelector(`[data-cuted-bumper-label="${slot}"]`).textContent = bumper ? bumper.label : "Add MP4";
      button.querySelector(`[data-cuted-bumper-status="${slot}"]`).textContent = bumper ? `${bumper.duration}s` : "";
    });
  }

  function normalizeBumpers(value) {
    const bumpers = value && typeof value === "object" ? value : {};
    return {
      intro: bumpers.intro ? normalizeBumper("intro", bumpers.intro) : null,
      outro: bumpers.outro ? normalizeBumper("outro", bumpers.outro) : null
    };
  }

  function normalizeBumper(slot, value) {
    return {
      duration: Number(value.duration || (slot === "intro" ? 1.8 : 2.4)),
      label: String(value.label || (slot === "intro" ? "start-bumper.mp4" : "end-bumper.mp4")),
      slot
    };
  }

  function mockBumper(slot) {
    return normalizeBumper(slot, {});
  }

  function buildReadyStatus() {
    return {
      kind: "ready",
      label: "SEND TO RENDER",
      persistent: true,
      tone: "green"
    };
  }

  function buildDiscardedStatus() {
    return {
      kind: "discarded",
      label: "CUT DISCARDED",
      persistent: true,
      tone: "red"
    };
  }

  function buildTrimStatus() {
    return {
      kind: "trim",
      label: "TRIM",
      persistent: true,
      tone: "blue"
    };
  }

  function reconcileReadyStatus(state) {
    if (state.discarded) {
      state.ready = false;
      state.status = buildDiscardedStatus();
      return;
    }
    if (state.ready) {
      state.status = buildReadyStatus();
      return;
    }
    if (state.status?.kind === "ready" || state.status?.kind === "discarded") {
      state.status = null;
    }
  }

  function snapshotState(state) {
    return {
      ...state,
      bumpers: {
        intro: state.bumpers.intro ? { ...state.bumpers.intro } : null,
        outro: state.bumpers.outro ? { ...state.bumpers.outro } : null
      },
      captionStyle: { ...state.captionStyle },
      clipInfo: { ...state.clipInfo },
      status: state.discarded ? buildDiscardedStatus() : state.ready ? buildReadyStatus() : state.status ? { ...state.status } : null
    };
  }

  function renderReadyLetters(text) {
    return Array.from(text)
      .map((letter, index) => {
        const content = letter === " " ? "&nbsp;" : letter;
        return `<span data-cuted-status-letter style="--i:${index}">${content}</span>`;
      })
      .join("");
  }

  function renderTrimStatus() {
    return '<span class="cuted-trim-status-main">TRIM</span><span class="cuted-trim-status-confirm">CONFIRME</span>';
  }

  function clamp(value, min, max) {
    if (Number.isNaN(value)) return min;
    return Math.min(Math.max(value, min), max);
  }

  global.createCutedControlBar = createCutedControlBar;
})(window);
