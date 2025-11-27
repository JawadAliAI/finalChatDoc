from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import os
import json
import tempfile
import subprocess
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# ==================== ENVIRONMENT VALIDATION ====================
def validate_environment():
    """Validate required environment variables"""
    required_vars = ["GEMINI_API_KEY", "FIREBASE_CREDENTIALS"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

validate_environment()

# ==================== INITIALIZE SERVICES ====================
# Initialize Gemini client (NO HARDCODED KEY)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Firebase
firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
cred_dict = json.loads(firebase_creds)

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Initialize FastAPI
app = FastAPI(title="Dr. HealBot - Medical Consultation API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================
class ChatRequest(BaseModel):
    message: str
    user_id: str
    language: str = "auto"

class PatientData(BaseModel):
    name: str
    patient_profile: dict
    lab_test_results: dict

class TTSRequest(BaseModel):
    text: str
    language_code: str = "en"

# ==================== SYSTEM PROMPT ====================
DOCTOR_SYSTEM_PROMPT = """
You are Dr. HealBot, a calm, knowledgeable, and empathetic virtual doctor.

GOAL:
Hold a natural, focused conversation with the patient to understand their health issue through a series of questions (ONE AT A TIME) before providing comprehensive guidance.

PATIENT HISTORY (IMPORTANT):
The following medical profile belongs to the current patient:
{patient_summary}

RULES FOR PATIENT HISTORY:
- ALWAYS use patient history in your reasoning (chronic diseases, medications, allergies, surgeries, recent labs, lifestyle).
- NEVER ignore relevant risks or medication interactions.
- TAILOR all advice (possible causes, medication safety, red flags) based on the patient's medical profile.
- Keep references to history natural and brief—only if medically relevant.

⚠️ CRITICAL: ASK ONLY ONE QUESTION AT A TIME - This makes the conversation natural and not overwhelming.

RESTRICTIONS:
- ONLY provide information related to medical, health, or wellness topics.
- If asked anything non-medical, politely decline: 
  "I'm a medical consultation assistant and can only help with health or medical-related concerns."

CONVERSATION FLOW:

**PHASE 1: INFORMATION GATHERING (Conversational)**
When a patient first mentions a symptom or health concern:
- Acknowledge their concern warmly (1-2 sentences)
- Ask ONLY ONE relevant follow-up question
- Keep it conversational - like a real doctor's consultation
- DO NOT give the final detailed response yet
- DO NOT ask multiple questions at once

Examples of good single questions:
- "How long have you been experiencing this fever?"
- "Have you taken your temperature? If yes, what was the reading?"
- "Are you experiencing any other symptoms along with the fever?"
- "Have you taken any medication for this yet?"

**PHASE 2: CONTINUED CONVERSATION**
- Continue asking clarifying questions ONE AT A TIME until you have enough information
- Typical consultations need 2-3 exchanges before final assessment
- Each response should have: brief acknowledgment + ONE question
- Consider asking about: onset, duration, severity, location, triggers, relieving factors
- Factor in patient's medical history when asking questions
- Never overwhelm the patient with multiple questions at once

**PHASE 3: FINAL COMPREHENSIVE RESPONSE**
Only provide the detailed response format AFTER you have gathered sufficient information through conversation.

📋 Based on what you've told me...
[Brief summary of patient's symptoms, plus any relevant history factors]

🔍 Possible Causes (Preliminary)
- 1–2 possible explanations using soft language ("It could be…", "This might be…")
- Include disclaimer that this is not a confirmed diagnosis
- NOTE: Adjust based on patient's history (conditions, meds, allergies)

💊 Medication Advice (Safe & OTC)
- Suggest only widely available OTC medicines
- ENSURE medication is safe given the patient's:
  - allergies
  - chronic illnesses
  - current medications
- Use disclaimers:
  "Use only if you have no allergies to this medication."
  "Follow packaging instructions or consult a doctor for exact dosing."

💡 Lifestyle & Home Care Tips
- 2–3 simple, practical suggestions

⚠️ When to See a Real Doctor
- Warning signs adjusted to the patient's underlying medical risks

📅 Follow-Up Advice
- One short recommendation about monitoring symptoms or follow-up timing

**HOW TO DECIDE WHEN TO GIVE FINAL RESPONSE:**
Give the detailed final response when you have:
✅ Duration of symptoms
✅ Severity level
✅ Main accompanying symptoms
✅ Any relevant patient history considerations
✅ Patient has answered at least 2-3 of your questions

If patient explicitly asks for immediate advice or says "just tell me what to do", you can provide the final response earlier.

CONVERSATION MODES:

1. **Doctor Mode** (for symptoms/health issues):
   - Start with conversational questions
   - Gather information progressively
   - Only provide structured final response after sufficient information

2. **Instructor Mode** (for general medical questions):
   - If patient asks "What is diabetes?" or "How does aspirin work?" - provide direct educational answer
   - Give clear, educational explanations
   - Use short paragraphs or bullet points
   - No need for lengthy information gathering

TONE & STYLE:
- Warm, calm, professional—like a caring doctor in a consultation
- Conversational and natural in early exchanges
- Clear, empathetic, no jargon
- Show you're listening by referencing what they've told you
- Never give definitive diagnoses; always use soft language

IMPORTANT:
- This is preliminary guidance, not a substitute for professional care.
- Never provide non-medical information.
- Be conversational first, comprehensive later.
- response has No Emoji or  No emojis No smileys No flags No pictographs
"""

# ==================== HELPER FUNCTIONS ====================
def generate_patient_summary(patient_data: dict) -> str:
    """Generate a comprehensive summary of patient's medical profile and lab results"""
    if not patient_data:
        return ""
    
    summary = "\n🏥 **PATIENT MEDICAL PROFILE**\n"
    
    # Patient Profile Section
    if "patient_profile" in patient_data:
        profile = patient_data["patient_profile"]
        
        # Critical Medical Info
        if "critical_medical_info" in profile:
            cmi = profile["critical_medical_info"]
            summary += "\n📌 **Critical Medical Information:**\n"
            summary += f"- Major Conditions: {cmi.get('major_conditions', 'None')}\n"
            summary += f"- Current Medications: {cmi.get('current_medications', 'None')}\n"
            summary += f"- Allergies: {cmi.get('allergies', 'None')}\n"
            if cmi.get('past_surgeries_or_treatments') and cmi['past_surgeries_or_treatments'] != 'None':
                summary += f"- Past Surgeries: {cmi.get('past_surgeries_or_treatments')}\n"
        
        # Vital Risk Factors
        if "vital_risk_factors" in profile:
            vrf = profile["vital_risk_factors"]
            summary += "\n⚠️ **Risk Factors:**\n"
            if vrf.get('smoking_status') and 'smok' in vrf['smoking_status'].lower():
                summary += f"- Smoking: {vrf.get('smoking_status')}\n"
            if vrf.get('blood_pressure_issue') and vrf['blood_pressure_issue'] != 'No':
                summary += f"- Blood Pressure: {vrf.get('blood_pressure_issue')}\n"
            if vrf.get('cholesterol_issue') and vrf['cholesterol_issue'] != 'No':
                summary += f"- Cholesterol: {vrf.get('cholesterol_issue')}\n"
            if vrf.get('diabetes_status') and 'diabetes' in vrf['diabetes_status'].lower():
                summary += f"- Diabetes: {vrf.get('diabetes_status')}\n"
            if vrf.get('family_history_major_disease'):
                summary += f"- Family History: {vrf.get('family_history_major_disease')}\n"
        
        # Organ Health Summary
        if "organ_health_summary" in profile:
            ohs = profile["organ_health_summary"]
            issues = []
            if ohs.get('heart_health') and 'normal' not in ohs['heart_health'].lower():
                issues.append(f"Heart: {ohs['heart_health']}")
            if ohs.get('kidney_health') and 'no' not in ohs['kidney_health'].lower():
                issues.append(f"Kidney: {ohs['kidney_health']}")
            if ohs.get('liver_health') and 'normal' not in ohs['liver_health'].lower() and 'no' not in ohs['liver_health'].lower():
                issues.append(f"Liver: {ohs['liver_health']}")
            if ohs.get('gut_health') and 'normal' not in ohs['gut_health'].lower():
                issues.append(f"Gut: {ohs['gut_health']}")
            
            if issues:
                summary += "\n🫀 **Organ Health Concerns:**\n"
                for issue in issues:
                    summary += f"- {issue}\n"
        
        # Mental & Sleep Health
        if "mental_sleep_health" in profile:
            msh = profile["mental_sleep_health"]
            summary += "\n🧠 **Mental & Sleep Health:**\n"
            summary += f"- Mental Status: {msh.get('mental_health_status', 'Not specified')}\n"
            if msh.get('mental_conditions'):
                summary += f"- Mental Conditions: {msh.get('mental_conditions')}\n"
            summary += f"- Sleep: {msh.get('sleep_hours', 'Not specified')} per night"
            if msh.get('sleep_problems'):
                summary += f" ({msh.get('sleep_problems')})\n"
            else:
                summary += "\n"
        
        # Lifestyle
        if "lifestyle" in profile:
            ls = profile["lifestyle"]
            summary += "\n🏃 **Lifestyle:**\n"
            summary += f"- Activity: {ls.get('physical_activity_level', 'Not specified')}\n"
            summary += f"- Diet: {ls.get('diet_type', 'Not specified')}\n"
    
    # Lab Test Results Section
    if "lab_test_results" in patient_data:
        lab_results = patient_data["lab_test_results"]
        abnormal_results = []
        
        # Check each test category for abnormal results
        for test_category, tests in lab_results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if result and isinstance(result, str):
                        result_lower = result.lower()
                        if any(word in result_lower for word in ['high', 'low', 'elevated', 'borderline']):
                            abnormal_results.append(f"{test_name.replace('_', ' ').title()}: {result}")
        
        if abnormal_results:
            summary += "\n🔬 **Key Lab Results (Abnormal):**\n"
            for result in abnormal_results[:10]:
                summary += f"- {result}\n"
    
    # Health Goals
    if "patient_profile" in patient_data and "primary_health_goals" in patient_data["patient_profile"]:
        goals = patient_data["patient_profile"]["primary_health_goals"]
        summary += f"\n🎯 **Health Goals:** {goals}\n"
    
    return summary

def save_patient_data(user_id: str, data: dict):
    """Save patient data to Firebase Firestore"""
    data["last_updated"] = datetime.now().isoformat()
    db.collection("patients").document(user_id).set(data)

def load_patient_data(user_id: str) -> dict:
    """Load patient data from Firebase Firestore"""
    doc = db.collection("patients").document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_chat_history(user_id: str, messages: list):
    db.collection("chat_history").document(user_id).set({
        "messages": messages,
        "last_updated": datetime.now().isoformat()
    })

def load_chat_history(user_id: str) -> list:
    doc = db.collection("chat_history").document(user_id).get()
    if doc.exists:
        return doc.to_dict().get("messages", [])
    return []

def delete_chat_history(user_id: str):
    db.collection("chat_history").document(user_id).delete()

# ==================== ROOT ENDPOINT ====================
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - tries to serve index.html, falls back to JSON"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return JSONResponse({
            "status": "healthy",
            "service": "Dr. HealBot API",
            "version": "1.0.0",
            "endpoints": {
                "chat": "/chat",
                "tts": "/tts",
                "stt": "/stt",
                "patient_data": "/patient-data/{user_id}",
                "chat_history": "/chat-history/{user_id}",
                "patient_summary": "/patient-summary/{user_id}"
            }
        })

@app.get("/ping")
async def ping():
    return {"message": "pong"}

# ==================== CHAT ENDPOINT ====================
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that:
    - Loads patient data and chat history
    - Updates patient data if new symptoms are reported
    - Sends patient summary + chat history + current message to Gemini
    - Returns structured, history-aware medical response
    """
    try:
        user_id = request.user_id
        user_message = request.message.strip()
        
        # Load patient data & chat history
        patient_data = load_patient_data(user_id) or {}
        chat_history = load_chat_history(user_id)
        
        # Update patient data with new symptom info
        if "new_symptoms" not in patient_data:
            patient_data["new_symptoms"] = []
        
        # Simple heuristic: if message contains key symptoms, store it
        symptom_keywords = ["fever", "cough", "headache", "ache", "pain", "rash", "vomit", "nausea"]
        if any(word in user_message.lower() for word in symptom_keywords):
            patient_data["new_symptoms"].append(user_message)
            save_patient_data(user_id, patient_data)
        
        # Generate patient summary
        persistent_summary = generate_patient_summary(patient_data) if patient_data else "No patient history available."
        
        # Prepare messages for Gemini (convert to single prompt format)
        system_context = f"""
{DOCTOR_SYSTEM_PROMPT}

You MUST always consider the following patient medical data when responding:

{persistent_summary}

Instructions:
1. **Conversational Stage**:
   - Start by acknowledging the patient's symptoms warmly.
   - Ask **only one question at a time** to clarify their condition.
   - Wait for the patient's answer before asking the next question.
   - Limit clarifying questions to **3–4 total**, but ask them sequentially, not all at once.
   - Example:
       - "I'm sorry you're feeling unwell. How long have you had this fever?"
       - Wait for response, then: "Are you experiencing any chills or body aches?"
       - And so on.
2. **Structured Guidance Stage**:
   - Only after 3–4 clarifying questions, provide the structured advice in the FINAL RESPONSE FORMAT.

- Always factor in patient history (conditions, medications, allergies, labs).
- Keep tone warm, empathetic, professional.
- Never give definitive diagnoses; always use soft language.
"""
        
        # Build conversation prompt
        conversation_prompt = system_context + "\n\n=== CONVERSATION HISTORY ===\n"
        
        # Add previous chat history
        for msg in chat_history:
            role = "Patient" if msg["role"] == "user" else "Dr. HealBot"
            conversation_prompt += f"\n{role}: {msg['content']}\n"
        
        # Add current user message
        conversation_prompt += f"\nPatient: {user_message}\n\nDr. HealBot:"
        
        # Call Gemini API
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(
            conversation_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1024,
            )
        )
        
        reply_text = response.text.strip()
        
        # Update chat history
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": reply_text})
        save_chat_history(user_id, chat_history)
        
        return JSONResponse({
            "reply": reply_text,
            "user_id": user_id,
            "message_count": len(chat_history)
        })
    
    except Exception as e:
        print(f"Error in /chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CHAT HISTORY ENDPOINTS ====================
@app.get("/chat-history/{user_id}")
async def get_chat_history(user_id: str):
    """Get chat history for a user"""
    try:
        history = load_chat_history(user_id)
        return JSONResponse({
            "user_id": user_id,
            "chat_history": history,
            "message_count": len(history)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat-history/{user_id}")
async def clear_chat_history(user_id: str):
    """Clear chat history for a user"""
    try:
        delete_chat_history(user_id)
        return JSONResponse({"message": "Chat history cleared", "user_id": user_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PATIENT DATA ENDPOINTS ====================
@app.post("/patient-data/{user_id}")
async def save_patient(user_id: str, data: PatientData):
    """Save patient profile and lab test results"""
    try:
        patient_info = {
            "name": data.name,
            "patient_profile": data.patient_profile,
            "lab_test_results": data.lab_test_results,
            "last_updated": datetime.now().isoformat()
        }
        save_patient_data(user_id, patient_info)
        return JSONResponse({
            "message": "Patient data saved successfully",
            "user_id": user_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient-data/{user_id}")
async def get_patient(user_id: str):
    """Get patient data"""
    try:
        data = load_patient_data(user_id)
        if data:
            return JSONResponse(data)
        return JSONResponse({"message": "No patient data found"}, status_code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient-summary/{user_id}")
async def get_patient_summary(user_id: str):
    """Get formatted summary of patient's medical profile and lab results"""
    try:
        data = load_patient_data(user_id)
        if not data:
            return JSONResponse({"summary": "No patient data available"})
        
        summary = generate_patient_summary(data)
        return JSONResponse({"summary": summary, "raw_data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TTS ENDPOINT ====================
@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    try:
        tmp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts = gTTS(text=req.text, lang=req.language_code)
        tts.save(tmp_mp3.name)
        
        tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_mp3.name, "-ar", "44100", "-ac", "2", tmp_wav.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return FileResponse(tmp_wav.name, media_type="audio/wav", filename="speech.wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STT ENDPOINT ====================
# Initialize speech recognizer
recognizer = sr.Recognizer()

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        # Use speech_recognition library with Google's free API
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
            # Use Google Speech Recognition (free, no API key needed)
            transcript = recognizer.recognize_google(audio_data)
        
        # Clean up temp file
        os.remove(tmp_path)
        
        return JSONResponse({"transcript": transcript})
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition service error: {str(e)}")
    except Exception as e:
        print(f"Error in STT: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
