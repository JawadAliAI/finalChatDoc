from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
import speech_recognition as sr
import os
import json
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from fastapi.responses import FileResponse


# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", "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"))

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

# Storage directories
STORAGE_DIR = Path("data")
CHAT_HISTORY_DIR = STORAGE_DIR / "chat_history"
PATIENT_DATA_DIR = STORAGE_DIR / "patient_data"

for dir_path in [STORAGE_DIR, CHAT_HISTORY_DIR, PATIENT_DATA_DIR]:
    dir_path.mkdir(exist_ok=True)

# ==================== MODELS ====================
class ChatRequest(BaseModel):
    message: str
    user_id: str
    language: str = "auto"

class PatientData(BaseModel):
    name: str
    patient_profile: dict
    lab_test_results: dict

# ==================== SYSTEM PROMPT ====================
DOCTOR_SYSTEM_PROMPT = """You are Dr. HealBot, a calm, knowledgeable, and empathetic virtual doctor.

GOAL:
Hold a natural, focused conversation with the patient to understand their health issue and offer helpful preliminary medical guidance. You also serve as a medical instructor for general health questions.

RESTRICTIONS:
- ONLY provide information related to medical, health, or wellness topics
- If asked anything non-medical, politely decline: "I'm a medical consultation assistant and can only help with health or medical-related concerns."

CONVERSATION MODES:
1. **Doctor Mode** (for symptoms/health issues):
   - Ask relevant, concise medical questions
   - Each question should clarify symptoms or narrow possible causes
   - Stop once enough information is collected
   - Provide structured medical response with headings and emojis

2. **Instructor Mode** (for general medical questions):
   - Give clear, educational explanations
   - Use short paragraphs or bullet points
   - Maintain professional but approachable tone
   - Conclude with practical health tips

FINAL RESPONSE FORMAT:
📋 Based on what you've told me...
[Brief summary of patient's description]

🔍 Possible Causes (Preliminary)
- List 1–2 possible conditions with phrases like "It could be" or "This sounds like"
- Include disclaimer that this is not a confirmed diagnosis

💡 Lifestyle & Home Care Tips
- 2–3 practical suggestions (rest, hydration, balanced diet, etc.)

⚠️ When to See a Real Doctor
- 2–3 warning signs when urgent medical care is needed

📅 Follow-Up Advice
- Brief recommendation for self-care or follow-up timing

TONE & STYLE:
- Speak like a caring doctor — short, clear, empathetic (1–2 sentences per reply)
- Plain language, no jargon
- One question per turn unless clarification is essential
- Warm, calm, professional
- Never make definitive diagnoses; use phrases like "it sounds like" or "it could be"
- If symptoms seem serious, always recommend urgent medical attention

IMPORTANT:
- This is preliminary guidance, not a substitute for professional care
- Never provide non-medical information"""

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
            for result in abnormal_results[:10]:  # Limit to top 10 most important
                summary += f"- {result}\n"
    
    # Health Goals
    if "patient_profile" in patient_data and "primary_health_goals" in patient_data["patient_profile"]:
        goals = patient_data["patient_profile"]["primary_health_goals"]
        summary += f"\n🎯 **Health Goals:** {goals}\n"
    
    return summary

def save_patient_data(user_id: str, data: dict):
    """Save patient data"""
    file_path = PATIENT_DATA_DIR / f"{user_id}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_patient_data(user_id: str) -> dict:
    """Load patient data if exists"""
    file_path = PATIENT_DATA_DIR / f"{user_id}.json"
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def load_chat_history(user_id: str) -> list:
    """Load chat history for a user"""
    file_path = CHAT_HISTORY_DIR / f"{user_id}.json"
    if file_path.exists():
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get("messages", [])
    return []

def save_chat_history(user_id: str, messages: list):
    """Save chat history for a user"""
    file_path = CHAT_HISTORY_DIR / f"{user_id}.json"
    with open(file_path, 'w') as f:
        json.dump({
            "user_id": user_id,
            "last_updated": datetime.now().isoformat(),
            "messages": messages
        }, f, indent=2)

def delete_chat_history(user_id: str):
    """Delete chat history for a user"""
    file_path = CHAT_HISTORY_DIR / f"{user_id}.json"
    if file_path.exists():
        file_path.unlink()

# ==================== CHAT ENDPOINT ====================
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_id = request.user_id
        user_message = request.message.strip()
        
        # Load existing chat history
        chat_history = load_chat_history(user_id)
        
        # Load patient data
        patient_data = load_patient_data(user_id)
        
        # Check if this is first message
        is_first_message = len(chat_history) == 0
        
        # Prepare messages for Groq
        messages = [{"role": "system", "content": DOCTOR_SYSTEM_PROMPT}]
        
        # If first message and patient has previous data, add context
        if is_first_message and patient_data:
            patient_summary = generate_patient_summary(patient_data)
            patient_name = patient_data.get('name', 'there')
            
            welcome_context = f"""This is a returning patient named {patient_name}. Here's their comprehensive medical profile:
{patient_summary}

IMPORTANT: 
- Greet them warmly by name
- Acknowledge their key health conditions (e.g., "I see you have hypertension and diabetes")
- Ask how they're feeling, especially regarding their known conditions
- Be aware of their medications and allergies when providing advice
- Reference their lab abnormalities if relevant to the conversation
- Keep your greeting natural and conversational (2-3 sentences max)"""
            
            messages.append({"role": "system", "content": welcome_context})
        
        # Add chat history (convert format for Groq)
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        
        reply_text = response.choices[0].message.content.strip()
        
        # Update chat history
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": reply_text})
        
        # Save updated history
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
class TTSRequest(BaseModel):
    text: str
    language_code: str = "en"

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

# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    return {
        "message": "Dr. HealBot API is running!",
        "version": "2.0",
        "features": [
            "Groq-powered AI chat with Llama 3.3 70B",
            "Persistent chat history per user",
            "Comprehensive patient profiles (medical history, lifestyle, organs)",
            "Complete lab test results storage",
            "Intelligent health summaries",
            "Session-based conversations",
            "Text-to-speech & Speech-to-text (Google)"
        ]

    }
@app.get("/")
def main():
    return FileResponse("index.html")
