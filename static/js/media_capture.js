class MediaCaptureManager {
  constructor(videoElementId = "webcamPreview") {
    this.videoElement = document.getElementById(videoElementId);
    this.mediaStream = null;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isRecording = false;
  }

  async requestMediaAccess() {
    try {
      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
        },
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);

      if (this.videoElement) {
        this.videoElement.srcObject = this.mediaStream;
        await new Promise((resolve) => {
          this.videoElement.onloadedmetadata = () => {
            this.videoElement.play();
            resolve();
          };
        });
      }

      return this.mediaStream;
    } catch (error) {
      console.error("Error accessing media:", error);
      if (error.name === "NotAllowedError") {
        throw new Error(
          "Permission denied. Please grant access to webcam and microphone.",
        );
      } else if (error.name === "NotFoundError") {
        throw new Error("No webcam or microphone found on this device.");
      }
      throw new Error(`Media access error: ${error.message}`);
    }
  }

  async startRecording() {
    if (!this.mediaStream) {
      throw new Error(
        "No media stream available. Call requestMediaAccess first.",
      );
    }

    this.recordedChunks = [];

    const options = {
      mimeType: "video/webm;codecs=vp8,opus",
      videoBitsPerSecond: 2500000,
    };

    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      options.mimeType = "video/webm";
    }

    this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };

    this.mediaRecorder.onerror = (event) => {
      console.error("MediaRecorder error:", event.error);
    };

    this.mediaRecorder.start();
    this.isRecording = true;
  }

  async stopRecording() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || !this.isRecording) {
        reject(new Error("Recording not active"));
        return;
      }

      this.mediaRecorder.onstop = () => {
        const mimeType = this.mediaRecorder.mimeType || "video/webm";
        const blob = new Blob(this.recordedChunks, { type: mimeType });
        this.isRecording = false;
        resolve(blob);
      };

      this.mediaRecorder.stop();
    });
  }

  getRecordedBlob() {
    if (this.recordedChunks.length === 0) {
      throw new Error("No recorded data");
    }

    const mimeType = this.mediaRecorder
      ? this.mediaRecorder.mimeType
      : "video/webm";
    return new Blob(this.recordedChunks, { type: mimeType });
  }

  stopMediaStream() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
  }

  isRecordingActive() {
    return this.isRecording;
  }
}

let mediaCaptureManager = null;

async function initializeMediaCapture(videoElementId = "webcamPreview") {
  mediaCaptureManager = new MediaCaptureManager(videoElementId);
  return await mediaCaptureManager.requestMediaAccess();
}

async function startRecording() {
  if (!mediaCaptureManager) {
    throw new Error("Media capture not initialized");
  }
  return await mediaCaptureManager.startRecording();
}

async function stopRecording() {
  if (!mediaCaptureManager) {
    throw new Error("Media capture not initialized");
  }
  return await mediaCaptureManager.stopRecording();
}

function getRecordedBlob() {
  if (!mediaCaptureManager) {
    throw new Error("Media capture not initialized");
  }
  return mediaCaptureManager.getRecordedBlob();
}

function stopMediaStream() {
  if (mediaCaptureManager) {
    mediaCaptureManager.stopMediaStream();
  }
}

function isRecordingActive() {
  return mediaCaptureManager && mediaCaptureManager.isRecordingActive();
}
