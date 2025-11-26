"""
Patient Data Management Script
Upload questionnaire and biomarker data for patients
"""

import requests
import json

API_URL = "http://localhost:8000"

# Example patient data structure
EXAMPLE_PATIENT_1 = {
"name": "John Doe",
  "patient_profile": {
    "critical_medical_info": {
      "major_conditions": "Hypertension, mild asthma",
      "current_medications": "Amlodipine 5mg daily, Vitamin D supplement",
      "allergies": "Peanuts, Penicillin",
      "past_surgeries_or_treatments": "Appendix removal in 2018",
      "cancer_history": "No personal history of cancer"
    },
    "vital_risk_factors": {
      "smoking_status": "Smokes 5-7 cigarettes per day, started at age 19",
      "alcohol_use": "Occasional drinking on weekends",
      "drug_use": "No drug abuse history",
      "blood_pressure_issue": "High blood pressure diagnosed in 2022",
      "cholesterol_issue": "Borderline high cholesterol identified in last checkup",
      "diabetes_status": "No diabetes",
      "family_history_major_disease": "Father had heart disease, Mother has type 2 diabetes"
    },
    "organ_health_summary": {
      "heart_health": "Occasional chest discomfort during heavy exercise; no diagnosed heart disease",
      "kidney_health": "No kidney problems reported",
      "liver_health": "No liver disease; normal liver function tests",
      "gut_health": "Frequent bloating and occasional constipation",
      "immune_health": "No diagnosed autoimmune disorders; mild seasonal allergies"
    },
    "mental_sleep_health": {
      "mental_health_status": "Fair",
      "mental_conditions": "Mild anxiety and work-related stress",
      "sleep_hours": "5–6 hours per night",
      "sleep_problems": "Difficulty falling asleep and waking up frequently at night"
    },
    "lifestyle": {
      "physical_activity_level": "Moderately active (exercise 3–4 days per week)",
      "diet_type": "No special diet; mixed balanced diet",
      "food_intolerances": "Lactose intolerance (mild)",
      "water_intake": "2–3 liters per day"
    },
    "skin_hair": {
      "skin_issues": "Occasional acne and mild eczema on arms",
      "hair_loss": "Mild hair thinning for the past 2 years"
    },
    "women_health": {
      "pregnancy_history": "2 pregnancies, 1 miscarriage",
      "menstrual_status": "Regular periods",
      "menopause_status": "Not in menopause",
      "female_cancer_history": "No family history of ovarian/breast/cervical cancer"
    },
    "genetic_info": {
      "genetic_test_done": "Yes, basic genetic panel completed",
      "epigenetic_test_done": "No",
      "genetic_family_history": "Family history of heart disease and diabetes"
    },
    "primary_health_goals": "Weight management, improving sleep, reducing anxiety, optimizing gut health"
  },

  "lab_test_results": {
    "KidneyFunctionTest": {
      "urea": "normal",
      "creatinine": "high",
      "uric_acid": "normal",
      "calcium": "low",
      "phosphorus": "normal",
      "sodium": "normal",
      "potassium": "normal",
      "chloride": "normal",
      "amylase": "not_tested",
      "lipase": "not_tested",
      "urine_analysis": "normal",
      "bicarbonate": "normal",
      "egfr": "low",
      "serum_osmolality": "not_tested",
      "ionized_calcium": "not_tested"
    },
    "BasicCheckup": {
      "cbc": "normal",
      "differential": "normal"
    },
    "DiabeticProfile": {
      "fasting_blood_sugar": "normal",
      "hba1c": "normal",
      "insulin": "normal",
      "homa_ir": "normal"
    },
    "LipidProfile": {
      "cholesterol_total": "normal",
      "ldl": "high",
      "hdl_direct": "normal",
      "cholesterol_hdl_ratio": "normal",
      "triglycerides": "normal",
      "ldl_direct": "not_tested",
      "apo_a1": "not_tested",
      "apo_b": "not_tested",
      "apo_b_apo_a1_ratio": "not_tested"
    },
    "HormoneProfile": {
      "testosterone_total_free": "normal",
      "estrogen_e2": "normal",
      "progesterone": "normal",
      "dhea_s": "normal",
      "shbg": "normal",
      "lh": "normal",
      "fsh": "normal"
    },
    "ThyroidProfile": {
      "tsh": "normal",
      "free_t3": "normal",
      "free_t4": "normal",
      "total_t3": "not_tested",
      "total_t4": "not_tested",
      "reverse_t3": "not_tested",
      "tpo_ab": "normal",
      "tg_ab": "normal"
    },
    "AdrenalStressHormones": {
      "cortisol": "high",
      "acth": "normal",
      "igf1": "normal",
      "leptin": "normal",
      "adiponectin": "normal"
    },
    "CancerMarkers": {
      "ca125": "normal",
      "ca153": "not_tested",
      "ca199": "normal",
      "psa": "normal",
      "cea": "normal",
      "calcitonin": "not_tested",
      "afp": "normal",
      "tnf": "normal"
    },
    "LiverFunctionTest": {
      "albumin": "normal",
      "total_protein": "normal",
      "alt": "normal",
      "alp": "normal",
      "ast": "normal",
      "ggt": "normal",
      "ldh": "normal",
      "globulin": "normal",
      "albumin_globulin_ratio": "normal",
      "magnesium": "normal",
      "total_bilirubin": "normal",
      "direct_bilirubin": "normal",
      "indirect_bilirubin": "normal",
      "ammonia": "not_tested"
    },
    "BoneHealth": {
      "calcium": "normal",
      "phosphorus": "normal"
    },
    "CardiacProfile": {
      "hs_crp": "low",
      "ck": "normal",
      "ck_mb": "normal",
      "homocysteine": "not_tested"
    },
    "MineralsHeavyMetals": {
      "zinc": "normal",
      "copper": "normal",
      "selenium": "normal"
    },
    "IronProfile": {
      "iron": "normal",
      "tibc": "normal",
      "transferrin": "normal"
    },
    "Vitamins": {
      "vitamin_d": "low",
      "vitamin_b12": "normal"
    },
    "ImmuneProfile": {
      "ana": "normal",
      "ige": "normal",
      "igg": "normal",
      "anti_ccp": "normal",
      "dsdna_ssa_ssb_rnp_sm": "not_tested",
      "anca": "not_tested",
      "anti_ena": "normal",
      "il6": "normal",
      "comprehensive_allergy_profile": "normal",
      "allergy_panel_ige_igg": "normal"
    },
    "NordicLabTests": {
      "nutreval": "not_tested",
      "gi_360": "not_tested",
      "dutch_plus": "not_tested",
      "toxdetect": "not_tested",
      "truage": "normal",
      "glycanage": "normal"
    },
    "GenomicsProfile": {
      "wgs_30X": "normal",
      "wes_100X": "not_tested",
      "microbiome": "normal",
      "telomerase_length": "normal"
    }
  }
}


EXAMPLE_PATIENT_2 = {
"name": "Jane Smith",
  "patient_profile": {
    "critical_medical_info": {
      "major_conditions": "Type 2 diabetes (diagnosed 2021), mild osteoarthritis",
      "current_medications": "Metformin 1000mg daily, Omega-3 supplements",
      "allergies": "Shellfish",
      "past_surgeries_or_treatments": "Knee arthroscopy in 2020",
      "cancer_history": "No personal cancer history"
    },
    "vital_risk_factors": {
      "smoking_status": "Former smoker, quit 3 years ago",
      "alcohol_use": "Moderate, drinks 1–2 times a week",
      "drug_use": "No drug use",
      "blood_pressure_issue": "No diagnosed hypertension",
      "cholesterol_issue": "Mildly elevated LDL noted in latest checkup",
      "diabetes_status": "Type 2 diabetes, controlled",
      "family_history_major_disease": "Mother has diabetes; grandfather had stroke"
    },
    "organ_health_summary": {
      "heart_health": "Normal ECG; occasional palpitations",
      "kidney_health": "No kidney issues reported",
      "liver_health": "Mild fatty liver grade 1",
      "gut_health": "Frequent bloating and slow digestion",
      "immune_health": "Normal immune function"
    },
    "mental_sleep_health": {
      "mental_health_status": "Good",
      "mental_conditions": "Occasional stress",
      "sleep_hours": "6–7 hours",
      "sleep_problems": "Light sleep, wakes up early"
    },
    "lifestyle": {
      "physical_activity_level": "Walks daily, gym 1–2 times/week",
      "diet_type": "Low-carb diet",
      "food_intolerances": "None",
      "water_intake": "2 liters/day"
    },
    "skin_hair": {
      "skin_issues": "Dry skin on winter days",
      "hair_loss": "None"
    },
    "women_health": {
      "pregnancy_history": "Not applicable (male)",
      "menstrual_status": "Not applicable",
      "menopause_status": "Not applicable",
      "female_cancer_history": "Not applicable"
    },
    "genetic_info": {
      "genetic_test_done": "No",
      "epigenetic_test_done": "No",
      "genetic_family_history": "Family history of metabolic disorders"
    },
    "primary_health_goals": "Weight reduction, improving blood sugar, better gut health"
  },

  "lab_test_results": {
    "KidneyFunctionTest": {
      "urea": "normal",
      "creatinine": "normal",
      "uric_acid": "normal",
      "calcium": "normal",
      "phosphorus": "normal",
      "sodium": "normal",
      "potassium": "normal",
      "chloride": "normal",
      "amylase": "not_tested",
      "lipase": "not_tested",
      "urine_analysis": "normal",
      "bicarbonate": "normal",
      "egfr": "normal",
      "serum_osmolality": "not_tested",
      "ionized_calcium": "not_tested"
    },
    "BasicCheckup": {
      "cbc": "normal",
      "differential": "normal"
    },
    "DiabeticProfile": {
      "fasting_blood_sugar": "high",
      "hba1c": "borderline_high",
      "insulin": "normal",
      "homa_ir": "slightly_high"
    },
    "LipidProfile": {
      "cholesterol_total": "normal",
      "ldl": "high",
      "hdl_direct": "normal",
      "cholesterol_hdl_ratio": "normal",
      "triglycerides": "normal",
      "ldl_direct": "not_tested",
      "apo_a1": "not_tested",
      "apo_b": "not_tested",
      "apo_b_apo_a1_ratio": "not_tested"
    },
    "HormoneProfile": {
      "testosterone_total_free": "normal",
      "estrogen_e2": "not_tested",
      "progesterone": "not_tested",
      "dhea_s": "normal",
      "shbg": "normal",
      "lh": "normal",
      "fsh": "normal"
    },
    "ThyroidProfile": {
      "tsh": "normal",
      "free_t3": "normal",
      "free_t4": "normal",
      "total_t3": "not_tested",
      "total_t4": "not_tested",
      "reverse_t3": "not_tested",
      "tpo_ab": "normal",
      "tg_ab": "normal"
    },
    "AdrenalStressHormones": {
      "cortisol": "normal",
      "acth": "normal",
      "igf1": "normal",
      "leptin": "normal",
      "adiponectin": "normal"
    },
    "CancerMarkers": {
      "ca125": "normal",
      "ca153": "not_tested",
      "ca199": "normal",
      "psa": "normal",
      "cea": "normal",
      "calcitonin": "not_tested",
      "afp": "normal",
      "tnf": "normal"
    },
    "LiverFunctionTest": {
      "albumin": "normal",
      "total_protein": "normal",
      "alt": "normal",
      "alp": "normal",
      "ast": "normal",
      "ggt": "normal",
      "ldh": "normal",
      "globulin": "normal",
      "albumin_globulin_ratio": "normal",
      "magnesium": "normal",
      "total_bilirubin": "normal",
      "direct_bilirubin": "normal",
      "indirect_bilirubin": "normal",
      "ammonia": "not_tested"
    },
    "BoneHealth": {
      "calcium": "normal",
      "phosphorus": "normal"
    },
    "CardiacProfile": {
      "hs_crp": "normal",
      "ck": "normal",
      "ck_mb": "normal",
      "homocysteine": "not_tested"
    },
    "MineralsHeavyMetals": {
      "zinc": "normal",
      "copper": "normal",
      "selenium": "normal"
    },
    "IronProfile": {
      "iron": "normal",
      "tibc": "normal",
      "transferrin": "normal"
    },
    "Vitamins": {
      "vitamin_d": "low",
      "vitamin_b12": "normal"
    },
    "ImmuneProfile": {
      "ana": "normal",
      "ige": "normal",
      "igg": "normal",
      "anti_ccp": "normal",
      "dsdna_ssa_ssb_rnp_sm": "not_tested",
      "anca": "not_tested",
      "anti_ena": "normal",
      "il6": "normal",
      "comprehensive_allergy_profile": "normal",
      "allergy_panel_ige_igg": "normal"
    },
    "NordicLabTests": {
      "nutreval": "not_tested",
      "gi_360": "not_tested",
      "dutch_plus": "not_tested",
      "toxdetect": "not_tested",
      "truage": "normal",
      "glycanage": "normal"
    },
    "GenomicsProfile": {
      "wgs_30X": "normal",
      "wes_100X": "not_tested",
      "microbiome": "normal",
      "telomerase_length": "normal"
    }
  }
}


def upload_patient_data(user_id: str, patient_data: dict):
    """Upload patient data to the API"""
    try:
        response = requests.post(
            f"{API_URL}/patient-data/{user_id}",
            json=patient_data
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully uploaded data for {patient_data['name']} (user_id: {user_id})")
            return True
        else:
            print(f"❌ Failed to upload data: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error uploading data: {str(e)}")
        return False

def get_patient_summary(user_id: str):
    """Get patient summary from the API"""
    try:
        response = requests.get(f"{API_URL}/patient-summary/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Patient Summary for {user_id}:")
            print(data['summary'])
            return data
        else:
            print(f"❌ No data found for user_id: {user_id}")
            return None
    except Exception as e:
        print(f"❌ Error getting summary: {str(e)}")
        return None

def load_patient_from_json(file_path: str, user_id: str):
    """Load patient data from JSON file and upload"""
    try:
        with open(file_path, 'r') as f:
            patient_data = json.load(f)
        
        upload_patient_data(user_id, patient_data)
    except Exception as e:
        print(f"❌ Error loading JSON: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Dr. HealBot - Patient Data Upload Tool")
    print("=" * 60)
    
    # Example 1: Upload John Doe's data
    print("\n1️⃣ Uploading John Doe's patient data...")
    upload_patient_data("john_doe", EXAMPLE_PATIENT_1)
    
    # Example 2: Upload Jane Smith's data
    print("\n2️⃣ Uploading Jane Smith's patient data...")
    upload_patient_data("jane_smith", EXAMPLE_PATIENT_2)
    
    # Example 3: Get summaries
    print("\n" + "=" * 60)
    print("Retrieving Patient Summaries")
    print("=" * 60)
    
    get_patient_summary("john_doe")
    get_patient_summary("jane_smith")
    
    print("\n" + "=" * 60)
    print("✅ Patient data upload complete!")
    print("=" * 60)
    print("\nNow you can:")
    print("1. Login to the chatbot with name 'John Doe' or 'Jane Smith'")
    print("2. The bot will greet them with their medical history")
    print("3. Click the 'Summary' button to view their full medical profile")
    print("\nTo add your own patients:")
    print("- Create a JSON file following the EXAMPLE_PATIENT structure")
    print("- Use: load_patient_from_json('your_file.json', 'user_id')")