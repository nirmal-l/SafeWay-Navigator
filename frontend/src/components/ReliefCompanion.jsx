import React, { useState, useEffect, useRef } from 'react';

export default function ReliefCompanion({ onClose }) {
  // states: 'idle', 'listening', 'processing', 'speaking'
  const [interactionState, setInteractionState] = useState('idle');
  
  const [transcript, setTranscript] = useState('');
  const [aiTranscript, setAiTranscript] = useState('');
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  
  const chatHistoryRef = useRef([]);

  const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;

  useEffect(() => {
    initSpeechRecognition();
    const currentRecognition = recognitionRef.current;
    const currentSynth = synthRef.current;
    
    return () => {
      if (currentRecognition) {
        currentRecognition.stop();
      }
      if (currentSynth) {
        currentSynth.cancel();
      }
    };
  }, []);

  // Set up voice loading to ensure we grab the best professional voice
  useEffect(() => {
    if (synthRef.current) {
        const loadVoices = () => { synthRef.current.getVoices(); };
        synthRef.current.onvoiceschanged = loadVoices;
    }
  }, []);

  const initSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setAiTranscript("Speech recognition is not supported in this browser. Try Chrome.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let currentTrans = '';
      for (let i = 0; i < event.results.length; ++i) {
        currentTrans += event.results[i][0].transcript;
      }
      // Overwrite the full string with latest results so it builds properly
      setTranscript(currentTrans);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
    };

    recognitionRef.current = recognition;
  };

  const handleOrbClick = () => {
    if (interactionState === 'idle') {
      startListening();
    } else if (interactionState === 'listening') {
      stopListeningAndProcess();
    } else if (interactionState === 'speaking') {
      // interrupt AI and start listening
      synthRef.current.cancel();
      startListening();
    }
  };

  const startListening = () => {
    synthRef.current.cancel();
    setTranscript('');
    setAiTranscript('');
    setInteractionState('listening');
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error("Recognition start error:", e);
      }
    }
  };

  const stopListeningAndProcess = async () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setInteractionState('processing');
    
    if (!transcript.trim()) {
       setAiTranscript("I didn't quite catch that. Could you tap the orb and try speaking again?");
       speakText("I didn't quite catch that. Could you tap the orb and try speaking again?");
       return;
    }

    try {
      chatHistoryRef.current.push({ role: 'user', text: transcript.trim() });
      
      const historyString = chatHistoryRef.current.map(h => `${h.role === 'user' ? 'User' : 'Guardian'}: ${h.text}`).join('\n');
      
      // Professional stress-relief prompt
      const prompt = `You are 'Alex', an empathetic, warm, yet highly professional and intelligent companion.
      Your core purpose is to relieve the user from psychological stress while they walk alone at night.
      
      CORE RULES:
      1. NO GENDER ASSUMPTIONS: Remain completely gender-neutral.
      2. PROFESSIONAL YET HUMAN: Talk with a calm, confident, and incredibly professional voice, but never sound like a robot. Speak like an intelligent human companion.
      3. PROACTIVELY ASK QUESTIONS: You must proactively ask them questions about their day-to-day life, general topics, and their personal history/interests. This is crucial for keeping them distracted from their anxiety.
      4. KEEP THEM TALKING: Never let the conversation die. Acknowledge what they say naturally, and then instantly ask an engaging follow-up question.
      5. STORYTELLING: If the user asks for a story or distraction, YOU MUST tell a LONG, rich, immersive multi-paragraph story (at least 300 words). Do not cut it short. Take your time describing the vivid details.
      6. IF THEY FEEL UNSAFE: Drop the casual chat and switch to professional physiological grounding. Instruct them to take a breath, find a well-lit area, and reassure them of their safety.
      7. AVOID LISTS OR FORMATTING: Your response will be spoken aloud via TTS. Use standard text. Do not use asterisks or emojis.
      
      Past Conversation:
      ${historyString}
      
      User just said: "${transcript.trim()}"
      Alex's response:`;

      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.8, maxOutputTokens: 1000 }
        })
      });

      const data = await response.json();
      if (data.candidates && data.candidates[0].content.parts[0].text) {
        const aiResponse = data.candidates[0].content.parts[0].text.trim();
        setAiTranscript(aiResponse);
        chatHistoryRef.current.push({ role: 'guardian', text: aiResponse });
        setInteractionState('speaking');
        speakText(aiResponse);
      } else {
        throw new Error("No text response");
      }
    } catch (e) {
      console.error(e);
      setAiTranscript("I'm having trouble connecting to my network. Please try again.");
      speakText("I'm having trouble connecting to my network. Please try again.");
      setInteractionState('idle');
    }
  };

  const speakText = (text) => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    
    // Attempt to select the most professional english voice available on the device
    const voices = synthRef.current.getVoices();
    let proVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Premium') || v.name.includes('Siri')));
    if (!proVoice) proVoice = voices.find(v => v.lang.startsWith('en')); // fallback

    // Production-ready chunking: robustly handles full paragraphs, trailing text, and prevents dropping
    const chunks = text.match(/[^.!?\n]+[.!?\n]+|\s*[^.!?\n]+$/g) || [text];
    
    let utteranceIndex = 0;
    
    const speakNextSentence = () => {
        if (utteranceIndex >= chunks.length) {
            setInteractionState('idle');
            return;
        }
        
        const chunkStr = chunks[utteranceIndex].trim();
        if (!chunkStr) {
            utteranceIndex++;
            speakNextSentence();
            return;
        }

        const utterance = new SpeechSynthesisUtterance(chunkStr);
        if (proVoice) utterance.voice = proVoice;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        utterance.onend = () => {
            utteranceIndex++;
            // Small timeout prevents Safari/Chrome garbage-collection freezing on chained TTS
            setTimeout(speakNextSentence, 50);
        };
        
        utterance.onerror = (e) => {
            console.error("Speech Synthesis Error:", e);
            utteranceIndex++;
            setTimeout(speakNextSentence, 50);
        };
        
        synthRef.current.speak(utterance);
    };
    
    speakNextSentence();
  };

  return (
    <div className="relief-companion-overlay animate-fade-in">
      <div className="relief-header">
        <h2>Virtual Guardian</h2>
        <button className="relief-close-btn" onClick={onClose}>&times;</button>
      </div>

      <div className="relief-content">
        <div className="guardian-orb-container">
          <div 
            className={`guardian-orb ${interactionState === 'speaking' ? 'speaking' : ''} ${interactionState === 'listening' ? 'listening' : ''} ${interactionState === 'processing' ? 'thinking' : ''} ${interactionState === 'idle' ? 'paused' : ''}`}
            onClick={handleOrbClick}
          ></div>

          <p className="guardian-status">
            {interactionState === 'idle' && "Tap orb to speak"}
            {interactionState === 'listening' && "Listening... Tap to reply"}
            {interactionState === 'processing' && "Alex is thinking..."}
            {interactionState === 'speaking' && "Alex is speaking..."}
          </p>
          
          {interactionState === 'listening' && transcript && (
             <p className="guardian-transcript">{transcript}</p>
          )}
          
          {interactionState === 'speaking' && aiTranscript && (
             <p className="guardian-transcript ai-reply">{aiTranscript}</p>
          )}
        </div>

        <button 
          onClick={() => {
            if (synthRef.current) synthRef.current.cancel();
            if (recognitionRef.current) recognitionRef.current.stop();
            onClose();
          }} 
          className="back-nav-btn"
          style={{ 
            marginTop: '20px', 
            padding: '14px 28px', 
            backgroundColor: 'rgba(255,255,255,0.07)', 
            color: 'white', 
            border: '1px solid rgba(255,255,255,0.15)', 
            borderRadius: '16px', 
            cursor: 'pointer', 
            fontSize: '1rem', 
            fontWeight: '500',
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px', 
            justifyContent: 'center',
            width: '100%',
            maxWidth: '320px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            transition: 'all 0.2s ease-in-out'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.12)' }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.07)' }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><polyline points="12 19 5 12 12 5"></polyline></svg>
          Back to Navigation
        </button>
      </div>
    </div>
  );
}
