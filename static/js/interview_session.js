class InterviewSessionManager {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.currentQuestionIndex = 0;
    this.questions = [];
    this.isRecording = false;
    this.timerInterval = null;
    this.timeRemaining = 90;

    this.questionNumberEl = document.getElementById("questionNumber");
    this.questionCategoryEl = document.getElementById("questionCategory");
    this.questionTextEl = document.getElementById("questionText");
    this.timerEl = document.getElementById("timer");
    this.timerStatusEl = document.getElementById("timerStatus");
    this.recordingIndicatorEl = document.getElementById("recordingIndicator");
    this.startRecordingBtn = document.getElementById("startRecordingBtn");
    this.stopRecordingBtn = document.getElementById("stopRecordingBtn");
    this.skipBtn = document.getElementById("skipBtn");
    this.uploadStatusEl = document.getElementById("uploadStatus");
    this.errorAlertEl = document.getElementById("errorAlert");
    this.permissionDenialEl = document.getElementById("permissionDenial");
  }

  async initialize() {
    try {
      const response = await fetch(`/api/v1/session/${this.sessionId}`);
      const data = await response.json();

      if (!response.ok) {
        this.showError(data.error || "Failed to load session");
        return;
      }

      this.questions = data.questions;

      try {
        await initializeMediaCapture("webcamPreview");
      } catch (error) {
        this.showPermissionDenial(error.message);
        return;
      }

      this.loadQuestion();
      this.setupEventListeners();
    } catch (error) {
      this.showError(`Failed to initialize session: ${error.message}`);
    }
  }

  loadQuestion() {
    if (this.currentQuestionIndex >= this.questions.length) {
      this.completeInterview();
      return;
    }

    const question = this.questions[this.currentQuestionIndex];
    this.questionNumberEl.textContent = `Question ${this.currentQuestionIndex + 1} / ${this.questions.length}`;
    this.questionCategoryEl.textContent = question.category
      ? question.category.charAt(0).toUpperCase() + question.category.slice(1)
      : "General";
    this.questionTextEl.textContent =
      question.text || "No question text available.";

    this.timeRemaining = 90;
    this.updateTimer();
    this.isRecording = false;
    this.recordingIndicatorEl.classList.add("hidden");
    this.startRecordingBtn.classList.remove("hidden");
    this.stopRecordingBtn.classList.add("hidden");
    this.uploadStatusEl.classList.add("hidden");
    this.timerStatusEl.textContent = "Ready";
    this.errorAlertEl.classList.add("hidden");
  }

  async startRecording() {
    try {
      await startRecording();
      this.isRecording = true;

      this.startRecordingBtn.classList.add("hidden");
      this.stopRecordingBtn.classList.remove("hidden");
      this.recordingIndicatorEl.classList.remove("hidden");
      this.timerStatusEl.textContent = "Recording...";

      this.startTimer();
    } catch (error) {
      this.showError(`Failed to start recording: ${error.message}`);
    }
  }

  async stopRecording() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }

    try {
      const blob = await stopRecording();
      this.isRecording = false;

      this.stopRecordingBtn.classList.add("hidden");
      this.recordingIndicatorEl.classList.add("hidden");
      this.timerStatusEl.textContent = "Uploading...";
      this.uploadStatusEl.classList.remove("hidden");

      await this.uploadResponse(blob);

      this.currentQuestionIndex++;
      this.loadQuestion();
    } catch (error) {
      this.showError(`Failed to stop recording: ${error.message}`);
    }
  }

  async uploadResponse(blob) {
    const question = this.questions[this.currentQuestionIndex];
    const formData = new FormData();
    formData.append("session_id", this.sessionId);
    formData.append("question_id", question.id);
    formData.append("video", blob, `q${this.currentQuestionIndex + 1}.webm`);

    try {
      const response = await fetch("/api/v1/session/upload-response", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Upload failed");
      }
    } catch (error) {
      throw new Error(`Upload failed: ${error.message}`);
    }
  }

  startTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }

    this.timerInterval = setInterval(async () => {
      this.timeRemaining--;
      this.updateTimer();

      if (this.timeRemaining <= 0) {
        clearInterval(this.timerInterval);
        this.timerStatusEl.textContent = "Time's up!";
        await this.stopRecording();
      }
    }, 1000);
  }

  updateTimer() {
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    this.timerEl.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    this.timerEl.style.color = this.timeRemaining <= 10 ? "#e74c3c" : "#2c3e50";
  }

  async completeInterview() {
    this.uploadStatusEl.classList.remove("hidden");
    this.uploadStatusEl.innerHTML =
      '<div class="spinner-animation"></div><p>Finalizing session...</p>';

    try {
      const response = await fetch("/api/v1/session/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: this.sessionId }),
      });

      const data = await response.json();
      if (response.ok) {
        window.location.href = `/analysis_wait?session_id=${this.sessionId}`;
      } else {
        this.showError(data.error || "Failed to complete interview");
      }
    } catch (error) {
      this.showError(`Failed to complete interview: ${error.message}`);
    }
  }

  setupEventListeners() {
    this.startRecordingBtn.addEventListener("click", () =>
      this.startRecording(),
    );
    this.stopRecordingBtn.addEventListener("click", () => this.stopRecording());
    this.skipBtn.addEventListener("click", async () => {
      if (this.isRecording) {
        await this.stopRecording();
      } else {
        this.currentQuestionIndex++;
        this.loadQuestion();
      }
    });

    document
      .getElementById("retryPermissionBtn")
      ?.addEventListener("click", () => window.location.reload());
  }

  showError(message) {
    this.errorAlertEl.textContent = message;
    this.errorAlertEl.classList.remove("hidden");
  }

  showPermissionDenial(message) {
    this.permissionDenialEl.classList.remove("hidden");
    console.error("Permission denied:", message);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get("session_id");

  if (!sessionId) {
    document.getElementById("errorAlert").textContent =
      "No session_id provided in the URL.";
    document.getElementById("errorAlert").classList.remove("hidden");
    return;
  }

  const manager = new InterviewSessionManager(sessionId);
  await manager.initialize();
});
