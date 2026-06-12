(function registerCutedControlBar(global) {
  const DEFAULT_STATE = {
    aiStatus: "idle",
    captionsEnabled: false,
    effectMenuOpen: false,
    effectStyle: "clean",
    formatMenuOpen: false,
    insertMenuOpen: false,
    aspectRatio: "9:16",
    bumpers: { intro: null, outro: null },
    muted: false,
    ready: false,
    status: null,
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

    container.innerHTML = renderControlBar();
    const elements = readElements(container);
    const teardown = bindEvents(container, elements, state, callbacks, settings, statusClock);
    syncView(elements, state);

    return {
      destroy() {
        window.clearTimeout(statusClock.id);
        teardown();
        container.innerHTML = "";
      },
      getState() {
        return snapshotState(state);
      },
      update(nextState) {
        if (Object.prototype.hasOwnProperty.call(nextState || {}, "status")) {
          window.clearTimeout(statusClock.id);
        }
        Object.assign(state, normalizeState({ ...state, ...nextState }));
        reconcileReadyStatus(state);
        syncView(elements, state);
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
      onDiscardClick: options.onDiscardClick || nested.onDiscardClick,
      onEffectClick: options.onEffectClick || nested.onEffectClick,
      onEffectStyleChange: options.onEffectStyleChange || nested.onEffectStyleChange,
      onFormatChange: options.onFormatChange || nested.onFormatChange,
      onBumperClick: options.onBumperClick || nested.onBumperClick,
      onBumperRemove: options.onBumperRemove || nested.onBumperRemove,
      onBumperChange: options.onBumperChange || nested.onBumperChange,
      onInsertClick: options.onInsertClick || nested.onInsertClick,
      onReadyCancel: options.onReadyCancel || nested.onReadyCancel,
      onVolumeChange: options.onVolumeChange || nested.onVolumeChange
    };
  }

  function normalizeState(state) {
    const effectStyle = ["clean", "vhs", "film", "grain"].includes(state.effectStyle) ? state.effectStyle : "clean";
    const aiStatus = ["idle", "loading", "active"].includes(state.aiStatus) ? state.aiStatus : "idle";

    return {
      aiStatus,
      captionsEnabled: Boolean(state.captionsEnabled),
      effectMenuOpen: Boolean(state.effectMenuOpen),
      effectStyle,
      formatMenuOpen: Boolean(state.formatMenuOpen),
      insertMenuOpen: Boolean(state.insertMenuOpen),
      aspectRatio: FORMAT_OPTIONS.some((option) => option.value === state.aspectRatio) ? state.aspectRatio : "9:16",
      bumpers: normalizeBumpers(state.bumpers),
      muted: Boolean(state.muted),
      ready: Boolean(state.ready),
      status: normalizeStatus(state.status),
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

  function readElements(container) {
    return {
      aiButton: container.querySelector("[data-cuted-control='ai']"),
      approveButton: container.querySelector("[data-cuted-control='approve']"),
      captionButton: container.querySelector("[data-cuted-control='caption']"),
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
      insertMenu: container.querySelector("[data-cuted-insert-menu]"),
      readyCancelButton: container.querySelector("[data-cuted-control='ready-cancel']"),
      renderZone: container.querySelector("[data-cuted-render-zone]"),
      sonicRail: container.querySelector("[data-cuted-sonic-rail]"),
      soundButton: container.querySelector("[data-cuted-control='sound']"),
      toolGroup: container.querySelector("[data-cuted-tool-group]"),
      statusBar: container.querySelector("[data-cuted-bar-status]"),
      statusLabel: container.querySelector("[data-cuted-status-label]"),
      statusMeter: container.querySelector("[data-cuted-status-meter]"),
      volumeSlider: container.querySelector("[data-cuted-control='volume']"),
      volumeValue: container.querySelector("[data-cuted-value='volume']")
    };
  }

  function bindEvents(container, elements, state, callbacks, settings, statusClock) {
    const setStatus = (status, holdMs = 2600) => {
      window.clearTimeout(statusClock.id);
      state.status = normalizeStatus(status);
      syncStatus(elements, state);
      if (!state.status || state.status.persistent || holdMs <= 0) return;
      statusClock.id = window.setTimeout(() => {
        state.status = null;
        syncStatus(elements, state);
      }, holdMs);
    };
    const closeMenus = () => {
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      syncView(elements, state);
    };
    const lockReady = () => {
      state.ready = true;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      setStatus(buildReadyStatus(), 0);
      syncView(elements, state);
    };
    const dismissClick = (event) => {
      if (container.contains(event.target)) return;
      closeMenus();
    };
    const dismissKey = (event) => {
      if (event.key === "Escape") closeMenus();
    };

    document.addEventListener("click", dismissClick);
    document.addEventListener("keydown", dismissKey);

    elements.volumeSlider.addEventListener("input", () => {
      state.volume = Number(elements.volumeSlider.value);
      state.muted = state.volume === 0;
      setStatus({ kind: "volume", label: `Volume ${state.volume}%`, progress: state.volume, tone: "blue" });
      syncView(elements, state);
      callbacks.onVolumeChange?.({ muted: state.muted, volume: state.volume });
    });

    elements.soundButton.addEventListener("click", () => {
      state.muted = !state.muted;
      state.volume = state.muted ? 0 : Math.max(state.volume, 75);
      setStatus({
        kind: "volume",
        label: state.muted ? "Audio muted" : `Volume ${state.volume}%`,
        progress: state.volume,
        tone: state.muted ? "neutral" : "blue"
      });
      syncView(elements, state);
      callbacks.onVolumeChange?.({ muted: state.muted, volume: state.volume });
    });

    elements.aiButton.addEventListener("click", () => {
      callbacks.onAiClick?.({ ...state });
      if (state.aiStatus === "idle") {
        state.aiStatus = "loading";
        setStatus({ kind: "ai", label: "AI analyzing frame safety...", progress: 42, tone: "blue" });
        syncView(elements, state);
        callbacks.onAiStatusChange?.({ aiStatus: state.aiStatus });
        window.setTimeout(() => {
          state.aiStatus = "active";
          setStatus({ kind: "ai", label: "AI ready for this cut", tone: "blue" });
          syncView(elements, state);
          callbacks.onAiStatusChange?.({ aiStatus: state.aiStatus });
        }, 1400);
      }
    });

    elements.effectButton.addEventListener("click", () => {
      state.effectMenuOpen = !state.effectMenuOpen;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
      setStatus({
        kind: "effect",
        label: state.effectMenuOpen ? "Choose a visual effect" : "Effect menu closed",
        tone: state.effectMenuOpen ? "green" : "neutral"
      });
      syncView(elements, state);
      callbacks.onEffectClick?.({ effectMenuOpen: state.effectMenuOpen, effectStyle: state.effectStyle });
    });

    elements.effectOptions.forEach((button) => {
      button.addEventListener("click", () => {
        state.effectStyle = button.dataset.cutedEffectStyle;
        state.effectMenuOpen = false;
        setStatus({ kind: "effect", label: `Effect preview: ${button.textContent.trim()}`, tone: "green" });
        syncView(elements, state);
        callbacks.onEffectStyleChange?.({ effectStyle: state.effectStyle });
      });
    });

    elements.captionButton.addEventListener("click", () => {
      state.captionsEnabled = !state.captionsEnabled;
      setStatus({ kind: "caption", label: state.captionsEnabled ? "Captions on" : "Captions off", tone: state.captionsEnabled ? "blue" : "neutral" });
      syncView(elements, state);
      callbacks.onCaptionToggle?.({ captionsEnabled: state.captionsEnabled });
    });
    elements.approveButton.addEventListener("click", () => {
      lockReady();
      callbacks.onApproveClick?.(snapshotState(state));
    });
    elements.discardButton.addEventListener("click", () => {
      setStatus({ kind: "discard", label: "Cut discarded", tone: "red" });
      callbacks.onDiscardClick?.({ ...state });
    });
    elements.readyCancelButton.addEventListener("click", () => {
      state.ready = false;
      setStatus({ kind: "editing", label: "Back to editing", tone: "neutral" }, 1800);
      syncView(elements, state);
      callbacks.onReadyCancel?.(snapshotState(state));
    });

    elements.formatButton.addEventListener("click", () => {
      state.formatMenuOpen = !state.formatMenuOpen;
      state.effectMenuOpen = false;
      state.insertMenuOpen = false;
      setStatus({ kind: "format", label: state.formatMenuOpen ? "Choose output format" : "Format menu closed", tone: "blue" });
      syncView(elements, state);
    });

    elements.formatOptions.forEach((button) => {
      button.addEventListener("click", () => {
        state.aspectRatio = button.dataset.cutedFormat;
        state.formatMenuOpen = false;
        setStatus({ kind: "format", label: `Format selected: ${state.aspectRatio}`, tone: "blue" });
        syncView(elements, state);
        callbacks.onFormatChange?.({ aspectRatio: state.aspectRatio });
      });
    });

    elements.insertButton.addEventListener("click", () => {
      state.insertMenuOpen = !state.insertMenuOpen;
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      setStatus({ kind: "insert", label: state.insertMenuOpen ? "Insert bumper: Start or End" : "Insert menu closed", tone: "blue" });
      syncView(elements, state);
      callbacks.onInsertClick?.({ insertMenuOpen: state.insertMenuOpen, bumpers: { ...state.bumpers } });
    });

    elements.bumperButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const slot = button.dataset.cutedBumperSlot;
        if (!state.bumpers[slot] && settings.mockBumpers) {
          state.bumpers[slot] = mockBumper(slot);
        }
        setStatus({ kind: "insert", label: `${slot === "intro" ? "Start" : "End"} bumper attached`, tone: "green" });
        syncView(elements, state);
        callbacks.onBumperClick?.({ slot, bumper: state.bumpers[slot] });
        callbacks.onBumperChange?.({ bumpers: { ...state.bumpers } });
      });
    });

    elements.bumperRemoves.forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const slot = button.dataset.cutedBumperRemove;
        state.bumpers[slot] = null;
        setStatus({ kind: "insert", label: `${slot === "intro" ? "Start" : "End"} bumper removed`, tone: "red" });
        syncView(elements, state);
        callbacks.onBumperRemove?.({ slot });
        callbacks.onBumperChange?.({ bumpers: { ...state.bumpers } });
      });
    });

    return () => {
      window.clearTimeout(statusClock.id);
      document.removeEventListener("click", dismissClick);
      document.removeEventListener("keydown", dismissKey);
    };
  }

  function syncView(elements, state) {
    elements.controlBar.classList.toggle("is-ready", state.ready);
    elements.renderZone.classList.toggle("is-ready", state.ready);
    elements.soundButton.classList.toggle("is-muted", state.muted);
    elements.sonicRail.classList.toggle("is-muted", state.muted);
    elements.sonicRail.style.setProperty("--volume", `${state.volume}%`);
    elements.sonicRail.style.setProperty("--volume-num", String(state.volume / 100));
    elements.volumeSlider.value = String(state.volume);
    elements.volumeValue.textContent = `${state.volume}%`;
    elements.aiButton.dataset.aiStatus = state.aiStatus;
    elements.aiButton.classList.toggle("is-loading", state.aiStatus === "loading");
    elements.aiButton.classList.toggle("is-active", state.aiStatus === "loading" || state.aiStatus === "active");
    elements.captionButton.classList.toggle("is-active", state.captionsEnabled);
    elements.effectButton.classList.toggle("is-active", true);
    if (state.ready) {
      state.effectMenuOpen = false;
      state.formatMenuOpen = false;
      state.insertMenuOpen = false;
    }
    elements.effectMenu.dataset.open = String(state.effectMenuOpen);
    syncInsert(elements, state);
    syncStatus(elements, state);
    elements.approveButton.closest("[data-cuted-ready-region]").dataset.ready = String(state.ready);

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

  function syncStatus(elements, state) {
    const status = state.ready ? buildReadyStatus() : state.status;
    const hasStatus = Boolean(status && status.label);
    window.clearTimeout(elements.statusBar._cutedHideTimer);
    elements.controlBar.classList.toggle("has-status", hasStatus);
    elements.controlBar.dataset.statusKind = hasStatus ? status.kind : "idle";
    elements.controlBar.dataset.statusTone = hasStatus ? status.tone : "neutral";
    elements.toolGroup.classList.toggle("is-ready", state.ready);
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
      elements.controlBar.classList.remove("has-status");
      elements.toolGroup.classList.remove("is-status-active");
    }
    elements.statusBar.dataset.tone = hasStatus ? status.tone : "neutral";
    elements.statusBar.dataset.kind = hasStatus ? status.kind : "idle";
    if (hasStatus && status.kind === "ready") {
      elements.statusLabel.innerHTML = renderReadyLetters(status.label);
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

        <div class="cuted-bar-status-layer" data-kind="idle" data-tone="neutral" data-cuted-bar-status hidden>
          <span data-cuted-status-label></span>
          <i data-cuted-status-meter></i>
        </div>

        <div class="cuted-control-group cuted-audio-group">
          <button class="cuted-icon-button cuted-sound-button" type="button" aria-label="Volume" data-cuted-control="sound">
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
          <div class="cuted-sonic-rail" data-cuted-sonic-rail>
            <div class="cuted-sonic-fill"></div>
            <div class="cuted-sonic-bars" aria-hidden="true">
              ${renderSonicBars()}
            </div>
            <input class="cuted-volume-slider" type="range" min="0" max="100" value="75" aria-label="Volume" data-cuted-control="volume" />
          </div>
          <span class="cuted-volume-value" data-cuted-value="volume">75%</span>
        </div>

        <div class="cuted-divider" aria-hidden="true"></div>

        <div class="cuted-control-group cuted-format-group" aria-label="Formato">
          ${renderFormatDropdown()}
        </div>

        <div class="cuted-divider" aria-hidden="true"></div>

        <div class="cuted-render-zone" data-cuted-render-zone>
          <div class="cuted-control-group cuted-tool-group" data-cuted-tool-group>
            <div class="cuted-tool-buttons">
              <button class="cuted-tile-button cuted-ai-button" type="button" aria-label="IA" data-cuted-control="ai">
                <span>IA</span>
                <i class="cuted-ai-loader" aria-hidden="true"></i>
              </button>
              <button class="cuted-tile-button cuted-fx-button is-active" type="button" aria-label="FX" data-cuted-control="effect">
                <span>FX</span>
              </button>
              <button class="cuted-tile-button cuted-insert-button" type="button" aria-label="Insert" data-cuted-control="insert">
                <span>Insert</span>
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
        ${renderBumperOption("intro", "Start", "Before cut")}
        ${renderBumperOption("outro", "End", "After cut")}
      </div>
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
      label: "READY",
      persistent: true,
      tone: "green"
    };
  }

  function reconcileReadyStatus(state) {
    if (state.ready) {
      state.status = buildReadyStatus();
      return;
    }
    if (state.status?.kind === "ready") {
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
      status: state.ready ? buildReadyStatus() : state.status ? { ...state.status } : null
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

  function clamp(value, min, max) {
    if (Number.isNaN(value)) return min;
    return Math.min(Math.max(value, min), max);
  }

  global.createCutedControlBar = createCutedControlBar;
})(window);
