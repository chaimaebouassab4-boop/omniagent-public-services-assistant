import { useCallback, useEffect, useRef, useState } from "react";

type RecorderStatus = "idle" | "requesting" | "recording" | "stopping";

const FORMATS = [
  { mimeType: "audio/webm;codecs=opus", uploadType: "audio/webm", extension: "webm" },
  { mimeType: "audio/webm", uploadType: "audio/webm", extension: "webm" },
  { mimeType: "audio/ogg;codecs=opus", uploadType: "audio/ogg", extension: "ogg" },
  { mimeType: "audio/mp4", uploadType: "audio/mp4", extension: "mp4" },
] as const;

export function useAudioRecorder() {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [duration, setDuration] = useState(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startedAtRef = useRef(0);
  const generationRef = useRef(0);
  const mountedRef = useRef(true);

  const release = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    recorderRef.current = null;
  }, []);

  const cancel = useCallback(() => {
    generationRef.current += 1;
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") recorder.stop();
    release();
    setDuration(0);
    setStatus("idle");
  }, [release]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      generationRef.current += 1;
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") recorder.stop();
      release();
    };
  }, [release]);

  const start = useCallback(async () => {
    if (status !== "idle") return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      throw new Error("L'enregistrement audio n'est pas pris en charge par ce navigateur.");
    }
    const format = FORMATS.find(({ mimeType }) => MediaRecorder.isTypeSupported(mimeType));
    if (!format) throw new Error("Aucun format audio compatible n'est disponible dans ce navigateur.");

    const generation = ++generationRef.current;
    setStatus("requesting");
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      if (!mountedRef.current || generation !== generationRef.current) return;
      setStatus("idle");
      throw error;
    }
    if (!mountedRef.current || generation !== generationRef.current) {
      stream.getTracks().forEach((track) => track.stop());
      return;
    }

    try {
      const recorder = new MediaRecorder(stream, { mimeType: format.mimeType });
      streamRef.current = stream;
      recorderRef.current = recorder;
      recorder.start();
      startedAtRef.current = Date.now();
      setDuration(0);
      timerRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startedAtRef.current) / 1000));
      }, 250);
      setStatus("recording");
    } catch (error) {
      stream.getTracks().forEach((track) => track.stop());
      release();
      setStatus("idle");
      throw error;
    }
  }, [release, status]);

  const stop = useCallback((): Promise<File> => {
    const recorder = recorderRef.current;
    const format = FORMATS.find(({ mimeType }) => MediaRecorder.isTypeSupported(mimeType));
    if (!recorder || recorder.state !== "recording" || !format) {
      return Promise.reject(new Error("Aucun enregistrement en cours."));
    }
    const generation = generationRef.current;
    setStatus("stopping");
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;

    return new Promise<File>((resolve, reject) => {
      const chunks: BlobPart[] = [];
      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      });
      recorder.addEventListener("error", () => {
        release();
        if (mountedRef.current) setStatus("idle");
        reject(new Error("L'enregistrement audio a échoué."));
      }, { once: true });
      recorder.addEventListener("stop", () => {
        release();
        if (mountedRef.current) setStatus("idle");
        if (generation !== generationRef.current) {
          reject(new Error("Enregistrement annulé."));
          return;
        }
        const blob = new Blob(chunks, { type: format.uploadType });
        if (!blob.size) {
          reject(new Error("L'enregistrement est vide."));
          return;
        }
        resolve(new File([blob], `recording.${format.extension}`, { type: format.uploadType }));
      }, { once: true });
      recorder.stop();
    });
  }, [release]);

  return { status, duration, start, stop, cancel };
}
