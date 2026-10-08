import React, { useEffect, useRef, useState } from 'react';
import { AudioLines, Pause, Play, RotateCcw, Square, Volume2 } from 'lucide-react';
import { VerificationStatus } from '../types';

const LANGUAGES: Record<string, { label: string; locale: string }> = {
  en: { label: 'English', locale: 'en-US' },
  kn: { label: 'Kannada', locale: 'kn-IN' },
  hi: { label: 'Hindi', locale: 'hi-IN' },
  ta: { label: 'Tamil', locale: 'ta-IN' },
};

type AudioState = 'ready' | 'preparing' | 'playing' | 'paused' | 'stopped' | 'error';

interface VerifiedSpeechControlsProps {
  text: string;
  language: string;
  verificationStatus?: VerificationStatus;
  label?: string;
  unavailableReason?: string;
  elderMode?: boolean;
  enabled?: boolean;
}

export const VerifiedSpeechControls: React.FC<VerifiedSpeechControlsProps> = ({
  text,
  language,
  verificationStatus,
  label = 'explanation',
  unavailableReason,
  elderMode = false,
  enabled = true,
}) => {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [audioState, setAudioState] = useState<AudioState>('ready');
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const languageConfig = LANGUAGES[language] || LANGUAGES.en;
  const languageVoices = voices.filter((voice) => voice.localService && voice.lang.toLowerCase().startsWith(languageConfig.locale.slice(0, 2)));
  const voice = languageVoices.find((candidate) => candidate.lang.toLowerCase() === languageConfig.locale.toLowerCase())
    || languageVoices[0];
  const verified = verificationStatus === 'VERIFIED';
  const speechAvailable = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const canSpeak = enabled && verified && !!text.trim() && speechAvailable && !!voice;

  useEffect(() => {
    if (!speechAvailable) return;
    const synthesis = window.speechSynthesis;
    const updateVoices = () => setVoices(synthesis.getVoices());
    updateVoices();
    synthesis.addEventListener('voiceschanged', updateVoices);
    return () => {
      synthesis.removeEventListener('voiceschanged', updateVoices);
      if (utteranceRef.current) {
        utteranceRef.current = null;
        synthesis.cancel();
      }
    };
  }, [speechAvailable]);

  useEffect(() => {
    if (audioState === 'playing' || audioState === 'paused' || audioState === 'preparing') {
      utteranceRef.current = null;
      if (speechAvailable) window.speechSynthesis.cancel();
      setAudioState('ready');
    }
  }, [text, language, verificationStatus, speechAvailable]);

  const play = () => {
    if (!canSpeak || !voice) return;
    const synthesis = window.speechSynthesis;
    synthesis.cancel();
    setAudioState('preparing');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = languageConfig.locale;
    utterance.voice = voice;
    utterance.rate = 0.9;
    utterance.onstart = () => {
      if (utteranceRef.current === utterance) setAudioState('playing');
    };
    utterance.onend = () => {
      if (utteranceRef.current === utterance) setAudioState('stopped');
      utteranceRef.current = null;
    };
    utterance.onerror = (event) => {
      utteranceRef.current = null;
      if (event.error !== 'canceled' && event.error !== 'interrupted') setAudioState('error');
    };
    utteranceRef.current = utterance;
    try {
      synthesis.speak(utterance);
    } catch {
      utteranceRef.current = null;
      setAudioState('error');
    }
  };

  const pauseOrResume = () => {
    if (audioState === 'playing') {
      window.speechSynthesis.pause();
      setAudioState('paused');
    } else if (audioState === 'paused') {
      window.speechSynthesis.resume();
      setAudioState('playing');
    }
  };

  const stop = () => {
    utteranceRef.current = null;
    if (speechAvailable) window.speechSynthesis.cancel();
    setAudioState('stopped');
  };

  const unavailableMessage = !verified
    ? unavailableReason || 'Audio is unavailable until the explanation is verified.'
    : !enabled
      ? 'Voice is turned off in Accessibility settings.'
    : !text.trim()
      ? unavailableReason || 'No verified text is available for audio.'
    : !speechAvailable
      ? 'Audio could not be played. You can read the verified explanation instead.'
      : !voice
        ? `${languageConfig.label} voice is not available on this device.`
        : '';
  const stateMessage = audioState === 'preparing'
    ? 'Preparing audio...'
    : audioState === 'playing'
      ? `Playing in ${languageConfig.label}`
      : audioState === 'paused'
        ? 'Paused'
        : audioState === 'stopped'
          ? 'Stopped. Select Play to listen again.'
          : audioState === 'error'
            ? 'Audio could not be played. You can read the verified explanation instead.'
            : canSpeak
              ? `Ready to listen in ${languageConfig.label}`
              : unavailableMessage;

  return (
    <section aria-label={`Audio controls for verified ${label}`} className="rounded-2xl border border-slate-600 bg-slate-800 p-4 shadow-inner sm:p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="mt-1 rounded-xl bg-sky-400/15 p-2.5 text-sky-300" aria-hidden="true">
            <Volume2 className="h-6 w-6" />
          </span>
          <div>
            <h3 className={`${elderMode ? 'text-xl' : 'text-base'} font-bold text-white`}>{elderMode ? 'LISTEN TO THIS' : `Listen to ${label}`}</h3>
            <p role="status" aria-live="polite" className={`mt-1 ${elderMode ? 'text-base' : 'text-sm'} ${audioState === 'error' || (!verified || !voice) ? 'text-amber-200' : 'text-slate-300'}`}>
              {audioState === 'playing' && <AudioLines className="mr-2 inline h-5 w-5 animate-pulse" aria-hidden="true" />}
              {stateMessage}
            </p>
            <p className={`mt-1 ${elderMode ? 'text-sm' : 'text-xs'} text-slate-400`}>Audio is generated on this device. Verified text is not uploaded.</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2" aria-label="Playback controls">
          <button
            type="button"
            onClick={play}
            disabled={!canSpeak || audioState === 'preparing' || audioState === 'playing' || audioState === 'paused'}
            aria-label={`Play verified ${label} in ${languageConfig.label}`}
            className={`inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500 font-bold text-slate-950 transition hover:bg-sky-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300 disabled:cursor-not-allowed disabled:opacity-45 ${elderMode ? 'min-h-16 w-full px-6 text-xl sm:w-auto' : 'min-h-12 px-5 text-base'}`}
          >
            <Play className="h-5 w-5" />
            <span>{elderMode ? (audioState === 'playing' ? 'Playing' : 'Listen to this') : (audioState === 'stopped' || audioState === 'error' ? 'Play again' : 'Play')}</span>
          </button>
          <button
            type="button"
            onClick={pauseOrResume}
            disabled={!canSpeak || (audioState !== 'playing' && audioState !== 'paused')}
            aria-label={audioState === 'paused' ? 'Resume audio' : 'Pause audio'}
            className="inline-flex min-h-12 min-w-12 items-center justify-center gap-2 rounded-xl border border-slate-500 bg-slate-700 px-4 text-sm font-semibold text-white transition hover:bg-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300 disabled:cursor-not-allowed disabled:opacity-45"
          >
            {audioState === 'paused' ? <Play className="h-5 w-5" /> : <Pause className="h-5 w-5" />}
            <span className="sm:hidden">{audioState === 'paused' ? 'Resume' : 'Pause'}</span>
          </button>
          <button
            type="button"
            onClick={stop}
            disabled={!canSpeak || !['playing', 'paused', 'preparing'].includes(audioState)}
            aria-label="Stop audio"
            className="inline-flex min-h-12 min-w-12 items-center justify-center rounded-xl border border-slate-500 bg-slate-700 px-4 text-white transition hover:bg-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300 disabled:cursor-not-allowed disabled:opacity-45"
          >
            <Square className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={play}
            disabled={!canSpeak}
            aria-label={`Replay verified ${label}`}
            className="inline-flex min-h-12 min-w-12 items-center justify-center rounded-xl border border-slate-500 bg-slate-700 px-4 text-white transition hover:bg-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300 disabled:cursor-not-allowed disabled:opacity-45"
          >
            <RotateCcw className="h-5 w-5" />
          </button>
        </div>
      </div>
    </section>
  );
};